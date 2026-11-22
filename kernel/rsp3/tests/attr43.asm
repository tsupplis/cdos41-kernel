bits 16
org 100h
    mov dx,name
    mov cx,27h
    call set_get
    jc fail
    mov cx,24h
    call set_get
    jc fail
    mov dx,passed
    jmp print
fail:
    mov dx,failed
print:
    mov ah,9
    int 21h
    int 20h

; Set all four writable bits, then verify the returned attribute word.
set_get:
    push cx
    mov ax,4301h
    int 21h
    pop bx
    jc done
    push bx
    mov dx,name
    mov ax,4300h
    int 21h
    pop bx
    jc done
    cmp cx,bx
    je done
    stc
done:
    ret
name db 'B:N.TXT',0
passed db 'ATTR43 PASS$'
failed db 'ATTR43 FAIL$'
