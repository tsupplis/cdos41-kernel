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
    cmp cl,45
    je bdos_ok
    cmp cl,105
    jne failed
    ; DATE uses the day counter only to print the weekday in interactive mode.
    mov bx,dx
    mov word [bx],17830
    mov word [bx+2],0
    mov byte [bx+4],0
bdos_ok:
    xor ax,ax
    iret
dos:
    cmp ah,2bh
    je got_date
    cmp ah,9
    je print_string
    cmp ah,2
    je dos_ok
    cmp ah,2ah
    je current_date
    cmp ah,0ah
    je input_line
    jmp failed
current_date:
    mov cx,2026
    mov dx,0a1dh
    xor al,al
    iret
input_line:
    push si
    push di
    push cx
    push es
    mov ax,ds
    mov es,ax
    mov di,dx
    inc di
    mov byte [di],INPUT_LEN
    inc di
    push ds
    push cs
    pop ds
    mov si,input
    mov cx,INPUT_LEN
    rep movsb
    mov byte [es:di],13
    pop ds
    pop es
    pop cx
    pop di
    pop si
    iret
print_string:
    mov bx,dx
    cmp word [bx],'In'
    jne dos_ok
%if REJECT
    jmp passed
%else
    jmp failed
%endif
dos_ok:
    iret
got_date:
%if REJECT
    jmp failed
%else
    cmp cx,EXPECT_YEAR
    jne failed
    cmp dh,EXPECT_MONTH
    jne failed
    cmp dl,EXPECT_DAY
    jne failed
    jmp passed
%endif
passed:
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
tail: incbin "tail.bin"
input: incbin "input.bin"
payload: incbin "payload.bin"
payload_end:
