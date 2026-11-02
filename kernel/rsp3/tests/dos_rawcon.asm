; Disposable PCE regression: DOS 2.x version and per-open-CON binary mode.
bits 16
cpu 8086
org 100h
 mov sp,0ff0h
 mov bx,100h
 mov ah,4ah
 int 21h
 jc failed
 mov bx,1357h
 mov cx,2468h
 mov si,1234h
 mov di,5678h
 mov bp,4321h
 mov ax,3000h
 int 21h
 cmp ax,2
 jne failed
 cmp bx,0ff00h
 jne failed
 or cx,cx
 jnz failed
 cmp si,1234h
 jne failed
 cmp di,5678h
 jne failed
 cmp bp,4321h
 jne failed
 xor bx,bx
 mov ax,4400h
 int 21h
 jc failed
 test dl,20h
 jnz failed
%ifdef PROBE
 mov bx,1
 mov ax,4400h
 int 21h
 jc failed
 test dl,20h
 jnz failed
 mov dx,reset_pass
 jmp report
%else
 mov ah,45h
 int 21h
 jc failed
 mov [alias],ax
 mov bx,ax
 mov dx,20h
 mov ax,4401h
 int 21h
 jc failed
 xor bx,bx
 mov ax,4400h
 int 21h
 jc failed
 test dl,20h
 jz failed
 ; Child observes and clears the inherited HCB bit; parent sees the change.
 mov [params+4],ds
 mov dx,child
 mov bx,params
 mov ax,4b00h
 int 21h
 jc failed
 mov ah,4dh
 int 21h
 cmp ax,7
 jne failed
 xor bx,bx
 mov ax,4400h
 int 21h
 test dl,20h
 jnz failed
 mov bx,[alias]
 mov dx,20h
 mov ax,4401h
 int 21h
 jc failed
 mov ax,3301h
 mov dl,1
 int 21h
 mov dx,raw_prompt
 mov ah,9
 int 21h
 ; Zero-byte reads must not consume or wait for a key.
 xor bx,bx
 xor cx,cx
 mov dx,buffer
 mov ah,3fh
 int 21h
 jc failed
 or ax,ax
 jnz failed
 mov cx,5
 mov ah,3fh
 int 21h
 jc failed
 cmp ax,5
 jne failed
 cmp byte [buffer],'j'
 jne failed
 cmp byte [buffer+1],8
 jne failed
 cmp byte [buffer+2],1ah
 jne failed
 cmp byte [buffer+3],3
 jne failed
 cmp byte [buffer+4],13
 jne failed
 mov dx,extended_prompt
 mov ah,9
 int 21h
 xor bx,bx
 mov dx,buffer
 mov cx,2
 mov ah,3fh
 int 21h
 jc failed
 cmp ax,2
 jne failed
 cmp word [buffer],4800h
 jne failed
 mov bx,1
 mov dx,20h
 mov ax,4401h
 int 21h
 jc failed
 mov bx,1
 mov dx,raw_output
 mov cx,raw_output_end-raw_output
 mov ah,40h
 int 21h
 jc failed
 cmp ax,raw_output_end-raw_output
 jne failed
 ; Switching an alias back to cooked must affect stdin, not stdout.
 mov bx,[alias]
 xor dx,dx
 mov ax,4401h
 int 21h
 jc failed
 xor bx,bx
 mov ax,4400h
 int 21h
 test dl,20h
 jnz failed
 mov bx,1
 mov ax,4400h
 int 21h
 test dl,20h
 jz failed
 xor dx,dx
 mov ax,4401h
 int 21h
 jc failed
 mov bx,[alias]
 mov ah,3eh
 int 21h
 jc failed
 mov dx,cooked_prompt
 mov ah,9
 int 21h
 xor bx,bx
 mov dx,buffer
 mov cx,16
 mov ah,3fh
 int 21h
 jc failed
 cmp ax,4
 jne failed
 cmp word [buffer],'aC'
 jne failed
 cmp word [buffer+2],0a0dh
 jne failed
 ; Leave raw set deliberately; the next root program must start cooked.
 xor bx,bx
 mov dx,20h
 mov ax,4401h
 int 21h
 jc failed
 mov bx,1
 mov dx,20h
 mov ax,4401h
 int 21h
 jc failed
 mov dx,success
%endif
report:
 mov ah,9
 int 21h
 mov ax,4c00h
 int 21h
failed:
 mov dx,failure
 mov ah,9
 int 21h
 mov ax,4c63h
 int 21h
alias dw 0
params dw 0,tail,0,0,0,0,0
tail db 0,13
child db 'B:RAWCHILD.COM',0
buffer times 17 db 0
raw_prompt db 13,10,'RAW INPUT READY',13,10,'$'
extended_prompt db 13,10,'EXTENDED READY',13,10,'$'
cooked_prompt db 13,10,'COOKED READY',13,10,'$'
raw_output db 'RAWBYTES:',0fdh,0feh,0ffh,':END',13,10
raw_output_end:
success db 13,10,'RAWCON PASS',13,10,'$'
reset_pass db 13,10,'MODE RESET PASS',13,10,'$'
failure db 13,10,'RAWCON FAIL',13,10,'$'
