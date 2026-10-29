; Run the rebuilt DOS DATE.EXE with synthetic DOS/BDOS calls under emu2.
; Capture function 2Bh instead of changing any real clock.
bits 16
cpu 8086
org 100h
%include "case.inc"
start:
    push cs
    pop ds
    mov ax,3521h
    int 21h
    mov [old21],bx
    mov [old21+2],es
    mov dx,bdos
    mov ax,25e0h
    int 21h
    mov ax,2000h
    mov es,ax
    xor di,di
    xor ax,ax
    mov cx,8000h
    rep stosw
    mov si,payload
    xor di,di
    mov cx,payload_end-payload
    rep movsb
    mov ax,1ff0h
    mov es,ax
    mov byte [es:80h],TAIL_LEN
    mov si,tail
    mov di,81h
    mov cx,TAIL_LEN
    rep movsb
    mov dx,dos
    mov ax,2521h
    int 21h
    mov ax,EXE_SS
    cli
    mov ss,ax
    mov sp,EXE_SP
    sti
    mov ax,1ff0h
    mov ds,ax
    mov es,ax
    mov ax,EXE_CS
    push ax
    mov ax,EXE_IP
    push ax
    retf
bdos:
    xor ax,ax
    iret
dos:
    cmp ah,2ch
    je current
    cmp ah,9
    je string
    cmp ah,2
    je character
    cmp ah,0ah
    je finished
    jmp failed
current:
    mov cx,(HOUR << 8) | MINUTE
    mov dx,(SECOND << 8) | HUNDREDTH
    iret
string:
    push si
    mov si,dx
.next:
    lodsb
    cmp al,'$'
    je .done
    call compare
    jmp .next
.done:
    pop si
    iret
character:
    mov al,dl
    call compare
    iret
compare:
    push bx
    mov bx,[cs:position]
    cmp al,[cs:bx]
    jne failed
    inc word [cs:position]
    pop bx
    ret
finished:
    mov bx,[cs:position]
    cmp byte [cs:bx],0
    jne failed
    mov byte [cs:exitcode],0
    jmp finish
failed:
    mov byte [cs:exitcode],1
finish:
    cli
    mov ax,cs
    mov ss,ax
    mov sp,0fff0h
    sti
    mov ds,ax
    xor ax,ax
    mov es,ax
    mov ax,[old21]
    mov [es:84h],ax
    mov ax,[old21+2]
    mov [es:86h],ax
    mov al,[exitcode]
    mov ah,4ch
    int 21h
old21: dd 0
exitcode: db 1
position: dw expected
expected: incbin "expected.bin"
    db 0
tail:
payload: incbin "payload.bin"
payload_end:
