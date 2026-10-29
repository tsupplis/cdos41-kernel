; Execute the actual built XIOS RTC routines with a synthetic INT 1Ah BIOS.
; No host or emulator real-time clock is read or changed.
bits 16
cpu 8086
org 100h
%include "case.inc"
start:
    push cs
    pop ds
    mov dx,bios
    mov ax,251ah
    int 21h
%if MODE = 2
    xor ax,ax
    mov es,ax
    mov word [es:68h],0
    mov word [es:6ah],0
%endif
    mov ax,cs
    add ax,(payload-$$+100h)/16
    mov [target+2],ax
    mov ds,ax
    mov es,ax
    mov word [TOD_DAY],1234h
    mov word [TOD_HOUR],2211h
    mov byte [TOD_SEC],33h
    mov ax,1122h
    mov bx,3344h
    mov cx,5566h
    mov dx,7788h
    mov si,99aah
    mov di,0bbcch
    mov bp,0ddeeh
    cli
    stc
    call far [cs:target]
    pushf
    pop word [cs:saved_flags]
    cmp ax,1122h
    jne failed
    cmp bx,3344h
    jne failed
    cmp cx,5566h
    jne failed
    cmp dx,7788h
    jne failed
    cmp si,99aah
    jne failed
    cmp di,0bbcch
    jne failed
    cmp bp,0ddeeh
    jne failed
    mov ax,[cs:saved_flags]
    and ax,201h
    cmp ax,1
    jne failed
    mov ax,ds
    mov bx,es
    cmp ax,bx
    jne failed
    cmp ax,[cs:target+2]
    jne failed
    cmp word [TOD_DAY],EXPECT_DAY
    jne failed
    cmp word [TOD_HOUR],EXPECT_TIME
    jne failed
    cmp byte [TOD_SEC],EXPECT_SEC
    jne failed
    cmp byte [RTC_PRESENT],PRESENT
    jne failed
    cmp byte [cs:date_reads],DATE_READS
    jne failed
    mov word [TOD_DAY],SET_DAY
    mov word [TOD_HOUR],3412h
    mov byte [TOD_SEC],56h
    mov word [cs:target],4
    call far [cs:target]
    cmp byte [cs:date_writes],DATE_WRITES
    jne failed
    cmp byte [cs:time_writes],TIME_WRITES
    jne failed
%if DATE_WRITES
    cmp word [cs:written_date_c],SET_DATE_C
    jne failed
    cmp word [cs:written_date_d],SET_DATE_D
    jne failed
%endif
%if TIME_WRITES
    cmp word [cs:written_time_c],1234h
    jne failed
    cmp word [cs:written_time_d],5601h
    jne failed
%endif
    cmp word [TOD_DAY],SET_DAY
    jne failed
    cmp word [TOD_HOUR],3412h
    jne failed
    cmp byte [TOD_SEC],56h
    jne failed
    mov ax,4c00h
    int 21h
bios:
    push bp
    mov bp,sp
    cmp ah,4
    je read_date
    cmp ah,2
    je read_time
    cmp ah,5
    je write_date
    cmp ah,3
    je write_time
    jmp failed
read_date:
    inc byte [cs:date_reads]
%if MODE = 1
    jmp bios_fail
%elif MODE = 5
    jmp bios_ok
%else
    mov cx,DATE_C
    mov dx,DATE_D
%if MODE = 3
    test byte [cs:date_reads],1
    jnz bios_ok
    add dl,7 ; fixture rolls packed BCD 29 to 30
%elif MODE = 4
    cmp byte [cs:date_reads],1
    je bios_ok
    add dl,7 ; fixture rolls packed BCD 29 to 30
%endif
    jmp bios_ok
%endif
read_time:
    mov cx,TIME_C
    mov dx,TIME_D
    jmp bios_ok
write_date:
    inc byte [cs:date_writes]
    mov [cs:written_date_c],cx
    mov [cs:written_date_d],dx
%if WRITE_FAIL
    jmp bios_fail
%else
    jmp bios_ok
%endif
write_time:
    inc byte [cs:time_writes]
    mov [cs:written_time_c],cx
    mov [cs:written_time_d],dx
bios_ok:
    and word [ss:bp+6],0fffeh
    pop bp
    iret
bios_fail:
    or word [ss:bp+6],1
    pop bp
    iret
failed:
    mov ax,4c01h
    int 21h
target: dw 0,0
saved_flags: dw 0
date_reads: db 0
date_writes: db 0
time_writes: db 0
written_date_c: dw 0
written_date_d: dw 0
written_time_c: dw 0
written_time_d: dw 0
align 16, db 0
payload: incbin "payload.bin"
