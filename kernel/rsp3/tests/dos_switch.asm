; Host-only DOS 37h regression. Production kernel uses RASM86/ASM86.
bits 16
cpu 8086
org 100h
start:
    push cs
    pop ds
%ifdef PROBE
    mov ax,3700h
    int 21h
    cmp al,0
    jne failed
    cmp dl,'!'
    jne failed
    mov ax,3701h
    mov dl,'/'
    int 21h
    mov dx,probe_pass
    jmp print
%elifdef CHILD
    mov ax,3700h
    int 21h
    cmp al,0
    jne failed
    cmp dl,'-'
    jne failed
    mov ax,3701h
    mov dl,'+'
    int 21h
    cmp al,0
    jne failed
    mov ax,4c07h
    int 21h
%else
    mov sp,0ff0h
    mov bx,100h
    mov ah,4ah
    int 21h
    jc failed
    mov ax,3700h
    int 21h
    cmp al,0
    jne failed
    cmp dl,'/'
    jne failed
    ; BDOS 110 is a separate native output-terminator setting.
    mov cx,110
    mov dx,0ffffh
    int 0e0h
    mov [native_delim],bl
    mov ax,3701h
    mov dx,0a52dh
    mov bx,1234h
    mov cx,5678h
    mov si,1357h
    mov di,2468h
    mov bp,4321h
    int 21h
    jc failed
    cmp al,0
    jne failed
    cmp dx,0a52dh
    jne failed
    cmp bx,1234h
    jne failed
    cmp cx,5678h
    jne failed
    cmp si,1357h
    jne failed
    cmp di,2468h
    jne failed
    cmp bp,4321h
    jne failed
    mov ax,3700h
    mov dx,05a00h
    int 21h
    cmp dx,05a2dh
    jne failed
    mov ax,3702h
    mov dx,0a55ah
    int 21h
    jc failed
    cmp al,0ffh
    jne failed
    cmp dx,0a55ah
    jne failed
    mov cx,110
    mov dx,0ffffh
    int 0e0h
    cmp bl,[native_delim]
    jne failed
    mov [params+4],ds
    mov ax,4b00h
    mov dx,child
    mov bx,params
    int 21h
    jc failed
    mov ah,4dh
    int 21h
    cmp ax,7
    jne failed
    mov ax,3700h
    int 21h
    cmp dl,'+'
    jne failed
    mov ax,3701h
    mov dl,'!'
    int 21h
    mov dx,parent_pass
%endif
print:
    mov ah,9
    int 21h
    mov ax,4c00h
    int 21h
failed:
    mov dx,error
    mov ah,9
    int 21h
    mov ax,4c63h
    int 21h
native_delim db 0
child db 'B:SWCHILD.COM',0
params dw 0,tail,0,0,0,0,0
tail db 0,13
parent_pass db 'DOS SWITCH EXEC PASS',13,10,'$'
probe_pass db 'DOS SWITCH PERSIST PASS',13,10,'$'
error db 'DOS SWITCH FAIL',13,10,'$'
