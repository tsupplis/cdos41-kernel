bits 16
cpu 8086
%ifdef NATIVE
 db 1
 dw (code_end-code_start)/16,0,(code_end-code_start)/16,(code_end-code_start)/16
 db 2
 dw 32,0,32,32
 times 127-($-$$) db 0
 db 0
code_start:
 mov ax,ds
 cli
 mov ss,ax
 mov sp,500
 sti
 mov si,81h
 xor bp,bp
 mov bl,[80h]
 xor bh,bh
 mov bp,bx
 mov dl,'['
 call emit
again:
 or bp,bp
 jz done
 lodsb
 push ax
 mov cl,4
 shr al,cl
 call hex
 pop ax
 and al,15
 call hex
 dec bp
 jmp again
done:
 mov dl,']'
 call emit
 mov dl,13
 call emit
 mov dl,10
 call emit
 xor cx,cx
 xor dx,dx
 int 0e0h
hex:
 add al,'0'
 cmp al,'9'
 jbe hex_out
 add al,7
hex_out:
 mov dl,al
emit:
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push es
 mov cx,2
 int 0e0h
 pop es
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 ret
 align 16,db 0
code_end:
 times 512 db 0
%else
 org 100h
 mov dx,81h
 xor cx,cx
 mov cl,[80h]
 mov bx,1
 mov ah,40h
 int 21h
 mov dl,13
 mov ah,2
 int 21h
 mov dl,10
 mov ah,2
 int 21h
 mov ax,4c00h
 int 21h
%endif
