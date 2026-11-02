; Run the linked checker with deterministic BDOS directory and DMA services.
bits 16
cpu 8086
org 100h
%include "case.inc"

start:
    cld
    push cs
    pop ds
    mov dx,bdos
    mov ax,25e0h
    int 21h

    mov ax,2000h
    mov es,ax
    xor di,di
    mov si,code_image
    mov cx,code_end-code_image
    rep movsb

    mov ax,3000h
    mov es,ax
    xor ax,ax
    xor di,di
    mov cx,8000h
    rep stosw
    xor di,di
    mov si,data_image
    mov cx,data_end-data_image
    rep movsb
    mov ax,3000h
    mov ds,ax
    mov es,ax
    jmp 2000h:0

bdos:
    push bp
    mov bp,sp
    push bx
    push cx
    push dx
    push si
    push di
    push ds
    push es
    cld
    cmp cl,0
    je finished
    cmp cl,2
    je console
    cmp cl,17
    je search_first
    cmp cl,18
    je search_next
    cmp cl,25
    je drive
    cmp cl,26
    je set_dma
    cmp cl,31
    je get_dpb
    cmp cl,52
    je get_dma
    jmp failed

done:
    pop es
    pop ds
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop bp
    iret

console:
    mov ah,2
    int 21h
    xor ax,ax
    jmp done

drive:
    xor ax,ax
    jmp done

set_dma:
    mov [cs:dma],dx
    inc byte [cs:dma_sets]
    xor ax,ax
    jmp done

get_dma:
    mov ax,[cs:dma]
    mov [bp-2],ax
    mov word [bp-14],3000h
    jmp done

get_dpb:
    mov word [bp-2],dpb
    mov ax,cs
    mov [bp-14],ax
    jmp done

search_first:
    inc byte [cs:first_count]
    cmp byte [cs:first_count],2
    ja failed
    mov si,dx
    cmp byte [si],'?'
    jne failed
    mov [cs:search_offset],dx
    cmp byte [cs:first_count],1
    jne begin_scan
    mov word [cs:source],probe
    call copy_search_result
    xor ax,ax
    jmp done

begin_scan:
    mov word [cs:cursor],0
    jmp search_entry

search_next:
    cmp byte [cs:first_count],2
    jne failed
    inc word [cs:cursor]
search_entry:
    mov ax,[cs:cursor]
    cmp ax,DIR_ENTRIES
    jae no_match
    and ax,0fffch
    mov cl,5
    shl ax,cl
    add ax,directory
    mov [cs:source],ax
    call copy_search_result
    mov ax,[cs:cursor]
    and ax,3
    jmp done
no_match:
    mov ax,0ffh
    jmp done

; Real CDOS saves 33 FCB bytes, fills the DMA record, then copies the FCB back.
copy_search_result:
    mov si,[cs:search_offset]
    push cs
    pop es
    mov di,fcb_copy
    mov cx,33
    rep movsb
    push ds
    push cs
    pop ds
    mov es,[bp-12]
    mov di,[cs:dma]
    mov si,[cs:source]
    mov cx,128
    rep movsb
    mov si,fcb_copy
    mov di,[cs:search_offset]
    mov cx,33
    rep movsb
    pop ds
    ret

failed:
    mov byte [cs:exit_code],1
finished:
    cmp word [cs:dma],INITIAL_DMA
    jne failed_exit
    cmp byte [cs:dma_sets],EXPECTED_DMA_SETS
    jne failed_exit
    cmp byte [cs:first_count],EXPECTED_SEARCHES
    jne failed_exit
    jmp exit
failed_exit:
    mov byte [cs:exit_code],1
exit:
    cli
    mov ax,cs
    mov ss,ax
    mov sp,0ff00h
    mov ds,ax
    sti
    mov al,[exit_code]
    mov ah,4ch
    int 21h

dma: dw INITIAL_DMA
dma_sets: db 0
first_count: db 0
search_offset: dw 0
cursor: dw 0
source: dw 0
exit_code: db 0
fcb_copy: times 33 db 0
dpb:
    dw 32
    db BSH, ((1 << BSH)-1) & 0ffh, EXM
    dw DSM, 63
    db AL0, AL1
    dw 0, 1
probe:
%if DOS_MEDIA
    db 20h
    times 14 db 0
    db 80h
    times 112 db 0
%else
    db 0e5h
    times 127 db 0
%endif
directory: incbin "directory.bin"
code_image: incbin "code.bin"
code_end:
data_image: incbin "data.bin"
data_end:
