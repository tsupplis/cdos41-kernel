; Disposable DOS regression fixture; NASM is used only by host tests.
bits 16
cpu 8086
org 100h
 mov ah,0bh
 int 21h
 cmp al,255
 jne failed
 mov ah,7
 int 21h
 cmp al,0
 jne failed
 mov ah,8
 int 21h
 cmp al,1ah
 jne failed
 mov ah,6
 mov dl,255
 int 21h
 jz failed
 cmp al,'Z'
 jne failed
 mov dx,line
 mov ah,0ah
 int 21h
 cmp byte [line+1],3
 jne failed
 cmp word [line+2],'ON'
 jne failed
 mov dx,line
 mov ah,0ah
 int 21h
 cmp byte [line+1],3
 jne failed
 cmp word [line+2],'TW'
 jne failed
 mov dx,line
 mov ah,0ah
 int 21h
 cmp byte [line+1],0
 jne failed
 mov ah,0bh
 int 21h
 cmp al,0
 jne failed
 mov bx,0
 mov cx,1
 mov dx,input_byte
 mov ah,3fh
 int 21h
 jc failed
 cmp ax,0
 jne failed
 mov dx,text
 mov ah,9
 int 21h
 mov dl,'!'
 mov ah,2
 int 21h
 mov dl,0
 mov ah,6
 int 21h
 mov bx,1
 mov dx,binary
 mov cx,3
 mov ah,40h
 int 21h
 jc failed
 cmp ax,3
 jne failed
 mov ax,4c07h
 int 21h
failed:
 mov bx,2
 mov dx,failure
 mov cx,failure_end-failure
 mov ah,40h
 int 21h
 mov ax,4c63h
 int 21h
line db 16,0
 times 17 db 0
input_byte db 0
text db 'TEXT$'
binary db 0,1ah,255
failure db 13,10,'STREAM CHILD FAIL',13,10
failure_end:
