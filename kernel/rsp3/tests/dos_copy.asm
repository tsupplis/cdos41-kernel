; Disposable DOS regression fixture; NASM is used only by host tests.
bits 16
cpu 8086
org 100h
; Deliberately uses block handles, preserving NUL and Ctrl-Z through EOF.
again:
 xor bx,bx
 mov dx,buffer
 mov cx,73
 mov ah,3fh
 int 21h
 jc failed
 or ax,ax
 jz done
 mov cx,ax
 mov bx,1
 mov ah,40h
 int 21h
 jc failed
 cmp ax,cx
 jne failed
 jmp again
done:
 mov ax,4c00h
 int 21h
failed:
 mov bx,2
 mov dx,error
 mov cx,error_end-error
 mov ah,40h
 int 21h
 mov ax,4c63h
 int 21h
error db 'DOS COPY FAIL',13,10
error_end:
buffer times 73 db 0
