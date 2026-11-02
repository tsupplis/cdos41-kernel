; Disposable DOS regression fixture; NASM is used only by host tests.
bits 16
cpu 8086
org 100h
 mov bx,1
 mov dx,letter
 mov cx,1
 mov ah,40h
 int 21h
 jc failed
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
%ifdef ABORT
 int 23h
%endif
 mov ax,4c09h
 int 21h
failed:
 mov ax,4c63h
 int 21h
letter db 'G'
leak db 'R'
name db 'B:GRAND.DAT',0
