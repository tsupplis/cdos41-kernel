; Execute the actual built XIOS detector with a synthetic INT 10h probe.
bits 16
cpu 8086
org 100h
%include "case.inc"
start:
    push cs
    pop ds
    mov dx,bios
    mov ax,2510h
    int 21h
    mov ax,40h
    mov es,ax
    mov word [es:63h],CRT_PORT
    mov word [es:85h],HEIGHT
    mov ax,cs
    add ax,(payload-$$+100h)/16
    mov [target+2],ax
    mov es,ax
    mov word [es:VAR_CURSOR],0607h
    mov word [es:VAR_MONO],0b0ch
    mov byte [es:VAR_SYNC],8
    mov ds,ax
    call far [cs:target]
    cmp word [es:VAR_CURSOR],EXPECT_COLOR
    jne failed
    cmp word [es:VAR_MONO],EXPECT_MONO
    jne failed
    cmp byte [es:VAR_SYNC],EXPECT_SYNC
    jne failed
    mov ax,4c00h
    int 21h
bios:
    cmp ah,12h
    jne failed
    cmp bx,0ff10h
    jne failed
    mov bh,ADAPTER
    iret
failed:
    mov ax,4c01h
    int 21h
target: dw 0,0
align 16, db 0
payload: incbin "payload.bin"
