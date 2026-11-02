; Ctrl-C must reach INT 23h from a non-console DOS call with user registers.
bits 16
cpu 8086
org 100h
 mov dx,handler
 mov ax,2523h
 int 21h
 mov ax,3301h
 mov dl,1
 int 21h
poll:
 mov bx,1234h
 mov cx,5678h
 mov dx,9abch
 mov ah,30h
 int 21h
 cmp byte [count],0
 je poll
 cmp byte [bad],0
 jne failed
 mov ax,3301h
 xor dx,dx
 int 21h
 mov dx,passed
 mov ah,9
 int 21h
 mov ax,4c00h
 int 21h
failed:
 mov dx,failure
 mov ah,9
 int 21h
 mov ax,4c01h
 int 21h
handler:
 cmp bx,1234h
 jne invalid
 cmp cx,5678h
 jne invalid
 cmp dx,9abch
 jne invalid
 inc byte [cs:count]
 iret
invalid:
 inc byte [cs:bad]
 inc byte [cs:count]
 iret
count db 0
bad db 0
passed db 13,10,'DOS BREAK PASS',13,10,'$'
failure db 13,10,'DOS BREAK FAIL',13,10,'$'
