; EXEC observes the shared raw-CON mode and changes it for its parent.
bits 16
cpu 8086
org 100h
 xor bx,bx
 mov ax,4400h
 int 21h
 jc failed
 test dl,20h
 jz failed
 xor dx,dx
 mov ax,4401h
 int 21h
 jc failed
 mov ax,4c07h
 int 21h
failed:
 mov ax,4c63h
 int 21h
