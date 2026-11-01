; Disposable DOS regression program, not a production kernel component.
; Check the PSP call stub and functions 50h/51h, then load COM and MZ EXE
; children without executing them. Inspect the returned CS:IP, release each
; child block, restore the parent PSP/DTA and return to the command prompt.
; Also check real allocation geometry, volume-label masks and buffered input.
; Stage markers identify a failed precondition or DOS service on screen.
bits 16
cpu 8086
org 100h
start:
 mov ax,cs
 mov [saved_psp],ax
 mov [params+4],ax
 mov [params+8],ax
 mov [params+12],ax
 mov sp,stack_top
 mov bx,(stack_top-$$+100h+15)/16
 mov ah,4ah
 int 21h
 jc failed
 mov byte [stage],'1'
 cmp word [50h],21cdh
 jne failed
 cmp byte [52h],0cbh
 jne failed
 mov byte [stage],'2'
 mov ah,51h
 int 21h
 cmp bx,[saved_psp]
 jne failed
 mov byte [stage],'3'
 mov bx,1234h
 mov ah,50h
 int 21h
 mov ah,51h
 int 21h
 cmp bx,1234h
 jne failed
 mov bx,[saved_psp]
 mov ah,50h
 int 21h
 mov dx,child_com
 call load_one
 mov dx,child_exe
 call load_one
; Check geometry on a FAT12 drive which is not the current drive.
 mov byte [stage],'8'
 mov ah,19h
 int 21h
 mov [old_drive],al
 push ds
 mov dl,2
 mov ah,1ch
 int 21h
 pop ds
 cmp al,2
 jne failed
 cmp cx,512
 jne failed
 cmp dx,FATCLUSTERS
 jne failed
 mov ah,19h
 int 21h
 cmp al,[old_drive]
 jne failed
 ; Query current CP/M geometry too; the drive remains unchanged.
 push ds
 mov ah,1bh
 int 21h
 pop ds
 cmp al,0ffh
 je failed
 or al,al
 jz failed
 or cx,cx
 jz failed
 or dx,dx
 jz failed
 ; DOS extended-FCB volume-label search, exact and mismatching masks.
 mov byte [stage],'9'
 mov dx,label_fcb
 mov ah,11h
 int 21h
 or al,al
 jnz failed
 mov dx,label_fcb
 mov ah,12h
 int 21h
 cmp al,0ffh
 jne failed
 mov byte [label_fcb+8],'X'
 mov dx,label_fcb
 mov ah,11h
 int 21h
 cmp al,0ffh
 jne failed
; Grow two files alternately so directory/buffer state is repeatedly reused.
 mov byte [stage],'C'
 mov dx,grow_a
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov [handle_a],ax
 mov dx,grow_b
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov [handle_b],ax
 mov bp,64
write_pair:
 mov bx,[handle_a]
 mov dx,grow_buffer
 mov cx,512
 mov ah,40h
 int 21h
 jc failed
 cmp ax,512
 jne failed
 mov bx,[handle_b]
 mov dx,grow_buffer_b
 mov cx,512
 mov ah,40h
 int 21h
 jc failed
 cmp ax,512
 jne failed
 dec bp
 jnz write_pair
 mov bx,[handle_a]
 mov ah,3eh
 int 21h
 jc failed
 mov bx,[handle_b]
 mov ah,3eh
 int 21h
 jc failed
 ; Zero capacity must not consume input or touch the following byte.
 mov byte [stage],'A'
 mov dx,zero_buf
 mov ah,0ah
 int 21h
 cmp byte [zero_buf+1],055h
 jne failed
 ; The driver types abc<Enter>; capacity two permits one char plus CR.
 mov byte [stage],'B'
 mov dx,input_buf
 mov ah,0ah
 int 21h
 cmp byte [input_buf+1],1
 jne failed
 cmp word [input_buf+2],0d61h
 jne failed
 cmp byte [input_buf+4],055h
 jne failed
 mov dx,passed
 mov ah,9
 int 21h
 int 20h
load_one:
 mov [filename],dx
 mov bx,params
 push ds
 pop es
 mov byte [stage],'4'
 mov ax,4b01h
 int 21h
 jc failed
 mov byte [stage],'5'
 mov ah,51h
 int 21h
 cmp bx,[saved_psp]
 je failed
 mov [child_psp],bx
 ; COM's entry is 100h; EXE's is zero. Both start with our signature.
 mov byte [stage],'6'
 les di,[params+18]
 cmp word [es:di],0a55ah
 jne failed
 mov bx,[saved_psp]
 mov ah,50h
 int 21h
 mov es,[child_psp]
 mov byte [stage],'7'
 mov ah,49h
 int 21h
 jc failed
 push ds
 pop es
 mov dx,80h
 mov ah,1ah
 int 21h
 ret
failed:
 mov bx,[saved_psp]
 mov ah,50h
 int 21h
 mov dx,bad
 mov ah,9
 int 21h
 int 20h
grow_a db 'B:GROWA.DAT',0
grow_b db 'B:GROWB.DAT',0
handle_a dw 0
handle_b dw 0
grow_buffer times 512 db 05ah
grow_buffer_b times 512 db 059h
old_drive db 0
label_fcb db 0ffh,0,0,0,0,0,8,2,'VERIFY     '
 times 25 db 0
zero_buf db 0,055h
input_buf db 2,0,055h,055h,055h
saved_psp dw 0
child_psp dw 0
filename dw 0
params dw 0,tail,0,fcb,0,fcb,0,0,0,0,0
tail db 0,13
fcb times 37 db 0
child_com db 'B:CHILD.COM',0
child_exe db 'B:CHILD.EXE',0
passed db 'RECOVERY LIVE PASS',13,10,'$'
bad db 'RECOVERY LIVE FAIL stage '
stage db '0',13,10,'$'
times 256 db 0
stack_top:
