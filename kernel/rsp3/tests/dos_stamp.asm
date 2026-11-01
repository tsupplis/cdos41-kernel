; DOS 2.x country record and handle timestamp regression.
; NASM assembles only this disposable test driver.
; CPM=1 writes on the timestamp-enabled CP/M boot disk.
; CPM=0 writes on the FAT data disk.
%if CPM
%define EXPECTED_TIME 7460h
%else
%define EXPECTED_TIME 747dh
%endif
bits 16
cpu 8086
org 100h
 mov dx,country
 mov ax,3800h
 int 21h
 jc failed
 cmp word [country],0
 jne failed
 cmp word [country+2],'$'
 jne failed
 cmp word [country+4],','
 jne failed
 cmp word [country+6],'.'
 jne failed
 cmp byte [country+32],55h
 jne failed
 mov si,country+8
 mov cx,24
zeroes:
 lodsb
 test al,al
 jnz failed
 loop zeroes
 mov ax,3801h
 int 21h
 jnc failed
 cmp ax,2
 jne failed
 mov ax,3800h
 mov dx,0ffffh
 int 21h
 jnc failed
 cmp ax,2
 jne failed
 mov ax,5700h
 mov bx,0ffffh
 int 21h
 jnc failed
 cmp ax,6
 jne failed
 xor bx,bx
 mov ax,5700h
 int 21h
 jnc failed
 mov dx,name
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov [handle],ax
 mov bx,ax
 mov dx,data
 mov cx,1
 mov ah,40h
 int 21h
 jc failed
 mov bx,[handle]
 mov ax,5701h
 mov dx,5d7ch
 mov cx,747dh
 int 21h
 jc failed
 mov bx,[handle]
 mov ax,5700h
 int 21h
 jc failed
 cmp dx,5d7ch
 jne failed
 cmp cx,EXPECTED_TIME
 jne failed
 mov bx,[handle]
 mov ah,45h
 int 21h
 jc failed
 mov bx,ax
 mov [duplicate],ax
 mov ax,5700h
 int 21h
 jc failed
 cmp cx,EXPECTED_TIME
 jne failed
 mov bx,[duplicate]
 mov ah,3eh
 int 21h
 jc failed
 mov bx,[handle]
 mov ax,5701h
 mov cx,0ffffh
 mov dx,5d7ch
 int 21h
 jnc failed
 mov bx,[handle]
 mov ah,3eh
 int 21h
 jc failed
 mov ax,3d00h
 mov dx,name
 int 21h
 jc failed
 mov bx,ax
 mov [handle],ax
 mov ax,5700h
 int 21h
 jc failed
 cmp dx,5d7ch
 jne failed
 cmp cx,EXPECTED_TIME
 jne failed
 mov bx,[handle]
 mov ah,3eh
 int 21h
 jc failed
 mov dx,success
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
%if CPM
name db 'A:STAMP.DAT',0
%else
name db 'B:STAMP.DAT',0
%endif
handle dw 0
duplicate dw 0
data db 'X'
country times 33 db 55h
success db 13,10,'STAMP COUNTRY PASS',13,10,'$'
failure db 13,10,'STAMP COUNTRY FAIL',13,10,'$'
