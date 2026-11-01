; Execute either CMD under emu2 with a deterministic, in-memory BDOS.
; No real queues, printers, or CP/M files are touched.
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
    mov si,code
    mov cx,code_end-code
    rep movsb
    mov ax,3000h
    mov es,ax
    xor di,di
    xor ax,ax
    mov cx,8000h
    rep stosw
    xor di,di
    mov si,data
    mov cx,data_end-data
    rep movsb
    mov word [es:6],DATA_LIMIT-2
    mov byte [es:80h],0
    mov ax,4000h
    mov es,ax
    xor di,di
    mov si,index
    mov cx,index_end-index
    rep movsb
    mov ax,5000h
    mov es,ax
    mov byte [es:4bh],0
    cli
    mov ax,3000h
    mov ss,ax
    mov sp,DATA_LIMIT-6
    mov ds,ax
    mov es,ax
    sti
    jmp 2000h:0

; Save the application's registers. BP remains the interrupt frame anchor.
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
    xor ax,ax
    cmp cl,0
    je finished
    cmp cl,2
    je console
    cmp cl,9
    je fataltext
    cmp cl,12
    je version
    cmp cl,25
    je done
    cmp cl,26
    je dmaoff
    cmp cl,32
    je done
    cmp cl,45
    je done
    cmp cl,68
    je unsupported
    cmp cl,105
    je unsupported
    cmp cl,163
    je version
    cmp cl,154
    je sysdata
    cmp cl,147
    je done
    cmp cl,145
    je done
    cmp cl,141
    je delay
    cmp cl,134
    je qmake
    cmp cl,135
    je qopen
    cmp cl,136
    je qdelete
    cmp cl,137
    je qread
    cmp cl,138
    je qcread
    cmp cl,139
    je qwrite
    cmp cl,140
    je qcwrite
    cmp cl,152
    je parse
    cmp cl,22
    je fmake
    cmp cl,15
    je fopen
    cmp cl,16
    je done
    cmp cl,19
    je fdelete
    cmp cl,20
    je fread
    cmp cl,21
    je fwrite
    cmp cl,30
    je done
    cmp cl,33
    je frandom
    cmp cl,34
    je wrandom
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
unsupported:
    mov ax,0xffff
    jmp done
version:
    mov word [bp-2],0x0031
    mov ax,0x1431
    jmp done
sysdata:
    mov word [bp-2],0
    mov word [bp-14],5000h
    jmp done
dmaoff:
    mov [cs:dma],dx
    jmp done
console:
    mov [cs:char],dl
    mov ax,cs
    mov ds,ax
    mov dx,char
    mov cx,1
    call emit
    xor ax,ax
    jmp done
fataltext:
    jmp failed
delay:
    mov [cs:delayarg],dx
    mov ax,cs
    mov ds,ax
    mov dx,delaytag
    mov cx,3
    call emit
    xor ax,ax
    jmp done
qmake:
    inc word [cs:makes]
    cmp word [cs:makes],QFAIL
    je failone
    jmp done
qopen:
    mov bx,dx
    cmp byte [bx+8],'D'
    jne done
    mov al,[bx+12]
    sub al,'0'
    mov ah,10
    mul ah
    add al,[bx+13]
    sub al,'0'
    mov cl,al
    mov ax,1
    shl ax,cl
    test ax,DEVICES
    jz failone
    xor ax,ax
    jmp done
qdelete:
    mov bx,dx
    cmp byte [bx+8],'M'
    je .mutex
    cmp byte [bx+11],'I'
    jne done
    inc word [cs:delins]
    cmp word [cs:delins],DELETE_BUSY
    jbe failone
    jmp done
.mutex:
    inc word [cs:delmx]
    cmp word [cs:delmx],DELETE_BUSY
    jbe failone
    jmp done
failone:
    mov ax,1
    jmp done
qread:
    mov bx,dx
    cmp byte [bx+11],'I'
    jne failed
    mov si,[cs:cursor]
    cmp si,messages_end
    jae finished
    mov di,[bx+6]
    mov ax,ds
    mov es,ax
    mov ax,cs
    mov ds,ax
    lodsw
    mov [flags],ax
    mov word [tries],0
    mov cx,160
    rep movsb
    mov [cursor],si
    xor ax,ax
    jmp done
qcread:
    mov bx,dx
    cmp byte [bx+11],'O'
    jne failone
    mov di,[bx+6]
    mov ax,ds
    mov es,ax
    mov al,0xa5
    mov cx,160
    rep stosb
    xor ax,ax
    jmp done
qcwrite:
    mov bx,dx
    cmp byte [bx+11],'O'
    jne qwrite
    test word [cs:flags],16
    jz qwrite
    inc word [cs:tries]
    cmp word [cs:tries],6
    jbe failone
qwrite:
    mov bx,dx
    cmp byte [bx+8],'M'
    je done
    push dx
    add dx,8
    mov cx,8
    call emit
    pop bx
    mov dx,[bx+6]
    mov cx,160
    call emit
    xor ax,ax
    jmp done
parse:
    test word [cs:flags],4
    jnz failone
    mov bx,dx
    mov di,[bx+2]
    mov byte [di+1],'S'
    mov byte [di+2],'P'
    mov byte [di+3],'L'
    mov word [di+4],0x2020
    mov word [di+6],0x2020
    mov byte [di+8],' '
    mov byte [di+9],'D'
    mov byte [di+10],'S'
    mov byte [di+11],'P'
    jmp done
fmake:
    mov bx,dx
    cmp byte [bx+1],'I'
    jne .spool
    cmp byte [cs:exists],0
    jne .exists
    mov byte [cs:exists],1
    mov word [cs:seq],0
    jmp done
.exists:
    mov ax,0x08ff
    jmp done
.spool:
    test word [cs:flags],2
    jnz failone
    jmp done
fopen:
    mov bx,dx
    cmp byte [bx+1],'I'
    jne done
    mov word [cs:seq],0
    mov byte [bx+32],0
    jmp done
fdelete:
    mov bx,dx
    cmp byte [bx+1],'I'
    jne .log
    mov byte [cs:exists],0
.log:
    push dx
    mov ax,cs
    mov ds,ax
    mov dx,deletetag
    mov cx,1
    call emit
    pop dx
    mov ds,[bp-12]
    mov cx,12
    call emit
    xor ax,ax
    jmp done
fread:
    mov bx,[cs:seq]
    cmp bx,INDEX_RECORDS
    jae failone
    inc word [cs:seq]
    jmp readrecord
frandom:
    test word [cs:flags],8
    jnz failone
    mov bx,dx
    xor ax,ax
    mov al,[bx+33]
    mov bx,ax
readrecord:
    cmp bx,127
    jae failone
    mov cl,7
    shl bx,cl
    mov di,[cs:dma]
    mov ax,ds
    mov es,ax
    mov ax,4000h
    mov ds,ax
    mov si,bx
    mov cx,128
    rep movsb
    xor ax,ax
    jmp done
fwrite:
    mov bx,dx
    cmp byte [bx+1],'I'
    jne .spool
    mov bx,[cs:seq]
    inc word [cs:seq]
    jmp writerecord
.spool:
    ; Log even failed writes so both calls and the bytes passed are compared.
    push dx
    mov ax,cs
    mov ds,ax
    mov dx,writetag
    mov cx,1
    call emit
    pop dx
    mov ds,[bp-12]
    mov cx,12
    call emit
    mov dx,[cs:dma]
    mov cx,128
    call emit
    test word [cs:flags],1
    jnz failone
    mov bx,[bp-6]
    inc byte [bx+32]
    inc byte [bx+15]
    xor ax,ax
    jmp done
wrandom:
    mov bx,dx
    xor ax,ax
    mov al,[bx+33]
    mov bx,ax
writerecord:
    cmp bx,127
    jae failed
    mov [cs:record],bx
    mov cl,7
    shl bx,cl
    mov di,bx
    mov si,[cs:dma]
    mov ax,4000h
    mov es,ax
    mov cx,128
    rep movsb
    mov ax,cs
    mov ds,ax
    mov dx,indextag
    mov cx,3
    call emit
    mov ds,[bp-12]
    mov dx,[cs:dma]
    mov cx,128
    call emit
    xor ax,ax
    jmp done

; DOS stdout is captured by the driver, never used as a CP/M disk.
emit:
    push ax
    push bx
    push cx
    push dx
    mov bx,1
    mov ah,40h
    int 21h
    jc failed
    cmp ax,cx
    jne failed
    pop dx
    pop cx
    pop bx
    pop ax
    ret
failed:
    mov byte [cs:exitcode],1
finished:
    cli
    mov ax,cs
    mov ss,ax
    mov sp,0xff00
    mov ds,ax
    sti
    mov al,[exitcode]
    mov ah,4ch
    int 21h

dma: dw 0
seq: dw 0
exists: db INDEX_EXISTS
cursor: dw messages
flags: dw 0
tries: dw 0
makes: dw 0
delins: dw 0
delmx: dw 0
exitcode: db 0
char: db 0
deletetag: db 'D'
writetag: db 'W'
indextag: db 'I'
record: dw 0
delaytag: db 'T'
delayarg: dw 0
messages: incbin "messages.bin"
messages_end:
index: incbin "index.bin"
index_end:
code: incbin "code.bin"
code_end:
data: incbin "data.bin"
data_end:
