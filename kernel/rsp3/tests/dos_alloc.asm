; Host-only regression; production assembly uses RASM86/ASM86.
bits 16
cpu 8086
org 100h
start:
    push cs
    pop ds
    mov ah,19h
    int 21h
    cmp al,0
    jne failed
    ; CP/M current-drive results agree between 1Bh, 1Ch/0 and 36h.
    mov ah,1bh
    int 21h
    push cs
    pop ds
    cmp al,0ffh
    je failed
    mov [cpm_spc],al
    mov [cpm_bps],cx
    mov [cpm_units],dx
    mov ah,1ch
    xor dx,dx
    int 21h
    push cs
    pop ds
    cmp al,[cpm_spc]
    jne failed
    cmp cx,[cpm_bps]
    jne failed
    cmp dx,[cpm_units]
    jne failed
    mov ah,36h
    xor dx,dx
    int 21h
    cmp al,[cpm_spc]
    jne failed
    cmp cx,[cpm_bps]
    jne failed
    cmp dx,[cpm_units]
    jne failed
    cmp bx,dx
    ja failed
    ; Cross-drive query must preserve the A: default and expose FAT byte 0.
    mov ah,1ch
    mov dl,2
    int 21h
    mov si,ds
    push cs
    pop ds
    cmp al,SPC
    jne failed
    cmp cx,BPS
    jne failed
    cmp dx,UNITS
    jne failed
    mov [fat_seg],si
    mov [fat_off],bx
    mov es,si
    cmp byte [es:bx],MEDIA
    jne failed
    mov ah,19h
    int 21h
    cmp al,0
    jne failed
    ; Select B: and check 1Bh ignores the supplied DL.
    mov ah,0eh
    mov dl,1
    int 21h
    mov ah,1bh
    mov dl,0ffh
    int 21h
    mov si,ds
    push cs
    pop ds
    cmp al,SPC
    jne failed
    cmp cx,BPS
    jne failed
    cmp dx,UNITS
    jne failed
    cmp si,[fat_seg]
    jne failed
    cmp bx,[fat_off]
    jne failed
    mov es,si
    cmp byte [es:bx],MEDIA
    jne failed
    mov ah,36h
    xor dx,dx
    int 21h
    cmp ax,SPC
    jne failed
    cmp cx,BPS
    jne failed
    cmp dx,UNITS
    jne failed
    cmp bx,dx
    ja failed
    mov si,bad_drives
    mov cx,bad_count
invalid:
    push cx
    mov dl,[si]
    mov ah,1ch
    int 21h
    push cs
    pop ds
    cmp al,0ffh
    jne failed
    mov dl,[si]
    mov ah,36h
    int 21h
    cmp ax,0ffffh
    jne failed
    mov ah,19h
    int 21h
    cmp al,1
    jne failed
    inc si
    pop cx
    loop invalid
    mov ah,0eh
    xor dx,dx
    int 21h
    mov dx,success
    jmp print
failed:
    push cs
    pop ds
    mov dx,error
print:
    mov ah,9
    int 21h
    mov ax,4c00h
    int 21h
cpm_spc db 0
cpm_bps dw 0
cpm_units dw 0
fat_seg dw 0
fat_off dw 0
bad_drives db 17,7fh,80h,81h,0feh,0ffh
bad_count equ $-bad_drives
success db 'DOS ALLOCATION PASS',13,10,'$'
error db 'DOS ALLOCATION FAIL',13,10,'$'
