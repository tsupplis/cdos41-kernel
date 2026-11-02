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
 mov dx,letter
 mov cx,1
 mov ah,40h
 int 21h
 jc failed
 mov [params+4],ds
 mov dx,grandchild
 mov bx,params
 mov ax,4b00h
 int 21h
 jc failed
 mov ah,4dh
 int 21h
%ifdef ABORT
 cmp ax,0100h
%else
 cmp ax,9
%endif
 jne failed
 mov bx,1
 mov ah,3eh
 int 21h
 jc failed
 mov dx,name
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,leak
 mov cx,1
 mov ah,40h
 int 21h
 jc failed
 mov ax,4c07h
 int 21h
failed:
 mov ax,4c63h
 int 21h
letter db 'C'
leak db 'Q'
name db 'B:LEAK.DAT',0

grandchild db 'B:GRAND.COM',0
params dw 0,tail,0,0,0,0,0
tail db 0,13
