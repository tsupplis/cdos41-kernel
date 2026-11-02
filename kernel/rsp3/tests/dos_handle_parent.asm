; Disposable DOS regression fixture; NASM is used only by host tests.
bits 16
cpu 8086
org 100h
 mov sp,0ff0h
 mov bx,100h
 mov ah,4ah
 int 21h
 jc failed
 mov bx,1
 mov ah,45h
 int 21h
 jc failed
 mov [console],ax
 mov dx,name
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov [file],ax
 mov bx,ax
 mov cx,1
 mov ah,46h
 int 21h
 jc failed
 mov bx,[file]
 mov ah,3eh
 int 21h
 jc failed
 mov dx,missing
 mov bx,params
 mov [params+4],ds
 mov ax,4b00h
 int 21h
 jnc failed
 cmp ax,2
 jne failed
 mov bx,1
 mov dx,letter
 mov cx,1
 mov ah,40h
 int 21h
 jc failed
 mov [params+4],ds
 mov dx,child
 mov bx,params
 mov cx,5678h
 mov si,1357h
 mov di,2468h
 mov bp,3456h
 mov ax,4b00h
 int 21h
 jc failed
 cmp cx,5678h
 jne failed
 cmp si,1357h
 jne failed
 cmp di,2468h
 jne failed
 cmp bp,3456h
 jne failed
 mov ah,4dh
 int 21h
 cmp ax,7
 jne failed
 mov bx,1
 mov dx,letter
 mov cx,1
 mov ah,40h
 int 21h
 jc failed
 cmp ax,1
 jne failed
 mov bx,[console]
 mov cx,1
 mov ah,46h
 int 21h
 jc failed
 mov bx,[console]
 mov ah,3eh
 int 21h
 jc failed
 mov dx,name
 mov ax,3d00h
 int 21h
 jc failed
 mov bx,ax
 mov dx,readback
 mov cx,5
 mov ah,3fh
 int 21h
 jc failed
 cmp ax,4
 jne failed
 cmp word [readback],'PC'
 jne failed
 cmp word [readback+2],'GP'
 jne failed
 mov ah,3eh
 int 21h
 jc failed
 mov dx,success
 mov ah,9
 int 21h
 mov ax,4c00h
 int 21h
failed:
 mov bx,2
 mov dx,failure
 mov cx,failure_end-failure
 mov ah,40h
 int 21h
 mov ax,4c01h
 int 21h
console dw 0
file dw 0
name db 'B:REDIR.DAT',0
child db 'B:CHILD.COM',0
letter db 'P'
params dw 0,tail,0,0,0,0,0
tail db 0,13
success db 13,10,'HANDLE EXEC PASS',13,10,'$'
failure db 13,10,'HANDLE EXEC FAIL',13,10
failure_end:

missing db 'B:MISSING.COM',0
readback times 5 db 0
