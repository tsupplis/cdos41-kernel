; Disposable DOS regression fixture; NASM is used only by host tests.
bits 16
cpu 8086
%ifdef EXE
org 0
%else
org 100h
%endif
 push cs
 pop ds
 mov bx,1
 mov dx,payload
 mov cx,payload_end-payload
 mov ah,40h
 int 21h
 jc failed
 cmp ax,cx
 jne failed
 mov bx,2
 mov dx,diagnostic
 mov cx,diagnostic_end-diagnostic
 mov ah,40h
 int 21h
 mov ax,4c00h
 int 21h
failed:
 mov ax,4c63h
 int 21h
payload db 'REDIR PAYLOAD',13,10,0,1ah,255
payload_end:
diagnostic db 'STDERR CONSOLE',13,10
diagnostic_end:
 times 512 db 0
