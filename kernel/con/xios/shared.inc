supmod                  equ     ds:word ptr .00h
dispatcher              equ     ds:word ptr .038h
mpmseg                  equ     ds:word ptr .040h
endseg                  equ     ds:word ptr .044h
nflags                  equ     ds:byte ptr .04Ah
sysdisk                 equ     ds:byte ptr .04Bh
mmp                     equ     ds:word ptr .04Ch
tempdisk                equ     ds:byte ptr .050h
mdul                    equ     ds:word ptr .058h
mfl                     equ     ds:word ptr .05Ah
rlr                     equ     ds:word ptr .068h
thrdrt                  equ     ds:word ptr .072h
qlr                     equ     ds:word ptr .074h
version                 equ     ds:word ptr .078h
vernum                  equ     ds:word ptr .07Ah
mpmvernum               equ     ds:word ptr .07Ch
todday                  equ     ds:word ptr .07Eh
todhour                 equ     ds:byte ptr .080h
todmin                  equ     ds:byte ptr .081h
todsec                  equ     ds:byte ptr .082h
openvec                 equ     ds:word ptr .088h
owner8087               equ     ds:word ptr .08Ch
ndpintoff               equ     ds:word ptr .0A0h
ndpintseg               equ     ds:word ptr .0A2h
ndpvecoff               equ     ds:word ptr .0A4h
ndpvecseg               equ     ds:word ptr .0A6h
true                    equ     0ffffh
false                   equ     0
pdelay                  equ     141                              ;delay specified number of ticks
pterm                   equ     143                              ;terminate process
devpoll                 equ     131                              ;poll device
devflagwait             equ     132                              ;flag wait
devflagset              equ     133                              ;flag set
flagsetignored          equ     2Ah                              ;* only error to cause retry
tickflag                equ     1                                ;tick flag number
secflag                 equ     2                                ;seconds flag number
fdcflag                 equ     4                                ;disk operation flag
ciflag                  equ     5                                ;console in flag
wwflag                  equ     6                                ;window manager flag
erflag                  equ     7                                ;get errror response
auxflagin0              equ     8                                ; port 0 input flag
auxflagin1              equ     9                                ; port 1 input flag
auxflagout0             equ     10                               ; port 0 output flag
auxflagout1             equ     11                               ; port 1 output flag
sc0flag                 equ     12                               ; hang up serial con 0
sc1flag                 equ     13                               ; hang up serial con 1
plink                   equ     word ptr 0
pthread                 equ     word ptr plink + word
pstat                   equ     byte ptr pthread + word
pprior                  equ     byte ptr pstat + byte
pflag                   equ     word ptr pprior + byte
pname                   equ     byte ptr pflag + word
puda                    equ     word ptr pname + 8
pdisk                   equ     byte ptr puda + word
puser                   equ     byte ptr pdisk + byte
pmem                    equ     word ptr puser + 3
pparent                 equ     word ptr pmem + 8
pcons                   equ     byte ptr pparent + word
plist                   equ     byte ptr pcons + 4
pfsys                   equ     0001h                            ;system process
pfkeep                  equ     0002h                            ;do not terminate
pftempkeep              equ     0200h                            ;don't terminate yet...
ceditflag               equ     byte ptr 04h
cflineedit              equ     040h
cowner                  equ     word ptr 00h
cmimic                  equ     byte ptr 08h
cstate                  equ     word ptr 0Eh
csmbackground           equ     00002h
csmnoswitch             equ     00008h
csmctrlS                equ     00080h
csmctrlO                equ     00100h
csmctrlP                equ     00200h
mdlink                  equ     word ptr 0
mdstart                 equ     word ptr mdlink + word
mdlength                equ     word ptr mdstart + word
FWAIT                   equ     WAIT
tickspersecond          equ     60
picocwport              equ     020h                             ;port 0
picocwnseoi             equ     020h                             ;non specific end of interupt
picocwseoi              equ     060h                             ;specific end of interupt channel 0
diskchannel             equ     06h
timerchannel            equ     00h
nul                     equ     00h
soh                     equ     01h
stx                     equ     02h
etx                     equ     03h
eot                     equ     04h
enq                     equ     05h
ack                     equ     06h
bel                     equ     07h
bs                      equ     08h
ht                      equ     09h
lf                      equ     0ah
vt                      equ     0bh
ff                      equ     0ch
cr                      equ     0dh
so                      equ     0eh
shi                     equ     0fh
dle                     equ     10h
dc1                     equ     11h
dc2                     equ     12h
dc3                     equ     13h
dc4                     equ     14h
nak                     equ     15h
syn                     equ     16h
etb                     equ     17h
can                     equ     18h
em                      equ     19h
subb                    equ     1ah
esc                     equ     1bh
fs                      equ     1ch
gs                      equ     1dh
rds                     equ     1eh
us                      equ     1fh
del                     equ     7fh
xon                     equ     dc1
xoff                    equ     dc3
sysdat                  equ     ds:word ptr .0C06h
supervisoro             equ     ds:word ptr .0C08h
supervisors             equ     ds:word ptr .0C0Ah
supervisor              equ     dword ptr supervisoro
tick                    equ     ds:byte ptr .0C0Ch
tickssec                equ     ds:byte ptr .0C0Dh
door                    equ     ds:byte ptr .0C0Eh
nacb                    equ     ds:byte ptr .0C0Fh
npcns                   equ     ds:byte ptr .0C10h
nvcns                   equ     ds:byte ptr .0C11h
nccb                    equ     ds:byte ptr .0C12h
nlcb                    equ     ds:byte ptr .0C13h
ccb                     equ     ds:word ptr .0C14h
lcb                     equ     ds:word ptr .0C16h
dphtbl                  equ     ds:word ptr .0C18h
mddph                   equ     ds:word ptr .0C30h
genccpmbuf              equ     ds:word ptr .0C38h
acb                     equ     ds:word ptr .0C3Ah
nationalsignature       equ     ds:word ptr .0C3Ch
setupbuf                equ     0D80h                            ; fixed location for read/write
kbddata                 equ     060h                             ;input port for the key board data
kbdcontrol              equ     061h                             ;control port for the key board
ctrl                    equ     29
shftleft                equ     42
shftright               equ     54
alt                     equ     56
numlock                 equ     69
capslock                equ     58
shftleftbit             equ     001h
shftrightbit            equ     002h
ctrlbit                 equ     004h
altbit                  equ     008h
numlockbit              equ     010h
capslockbit             equ     020h
PCINSERTKEY             equ     82                               ;scan code for INSERT
PCSCROLLKEY             equ     70                               ;scan code for SCROLL LOCK
PCSCROLLFLAG            equ     10h                              ;ROS bit for SCROLL LOCK toggle
PCINSERTFLAG            equ     80h                              ;ROS bit for INSERT mode toggle
timer0reg               equ     040h                             ;first counter timer port
timer2reg               equ     042h
timercmndreg            equ     043h                             ;command port
timer60hz               equ     19886                            ;constant for 60.001 hz tick
timer1000hz             equ     533h                             ;constant for 1000 hz tone
beepcmnd                equ     10110110b                        ;timer 2 lsb,msb binary
beepon                  equ     03h
beepoff                 equ     0fch
portb                   equ     061h
portc                   equ     062h
timerlow                equ     word ptr .6Ch                    ;rom bios timer variables
timerhigh               equ     word ptr .6Eh
ndpstatus               equ     word ptr 2                       ; status word in env_8087
resetflag               equ     word ptr .72h
prsckey                 equ     7Ch                              ;print screen immediate
wakekey                 equ     7Dh                              ;window manager alarm clock
fullkey                 equ     7Eh                              ;full/partial window toggle
pfklsize                equ     20                               ; chars per pfk in low table
pfkhsize                equ     4                                ; chars per pfk in high table
lowpfks                 equ     10                               ; number of 20 char pfk codes
highpfks                equ     40                               ; number of 4 char pfk codes
lcbsize                 equ     10                               ; bytes per lcb
lcbattach               equ     word ptr 0                       ; list owner
lcbqueue                equ     word ptr 2                       ; next in line
prscpd                  equ     1234h                            ; phony process desc
fwakeup                 equ     213h                             ; internal system call
slmonobit               equ     01h                              ; if status goes to monochrome
slcolorbit              equ     02h                              ; if status goes to color
numauxports             equ     2                                ; the maximum we and IBM support
auxinbufsize            equ     1024                             ; size of the receive buffer
auxoutbufsize           equ     64                               ; size of the transmit buffer
afew                    equ     10                               ; time for protocol turn around
auxstacksize            equ     64                               ; interrupt stack size
auxbufcount             equ     word ptr 0
auxinptr                equ     word ptr 2
auxoutptr               equ     word ptr 4
auxbufbase              equ     word ptr 6
auxbuftop               equ     word ptr 8
auxportaddr             equ     word ptr 10
auxflag                 equ     byte ptr 12
auxwait                 equ     byte ptr 13
auxprot                 equ     byte ptr 14
auxxchr                 equ     byte ptr 15
dtrdsr                  equ     01h                              ; bit for dsr/dtr protocol
rtscts                  equ     02h                              ; bit for rts/cts protocol
xonxoff                 equ     04h                              ; bit for xon/xoff protocol
offbit                  equ     80h                              ; recieve protocol is now off
protrinit               equ     00h                              ; initial receive
prottinit               equ     dtrdsr + rtscts + xonxoff        ; initial transmit
auxport0                equ     3F8h                             ; port 0 base address
auxport1                equ     2F8h                             ; port 1 base address
auxportdata             equ     0                                ; rw data read/write
auxportinten            equ     1                                ; wo interrupt enable
auxportintid            equ     2                                ; ro interrupt identification
auxportmctrl            equ     4                                ; wo bit 3 = enable int
auxportstatus           equ     5                                ; ro tbe and da
auxportmstat            equ     6                                ; ro dsr and cts
dr                      equ     01h                              ; data ready
tbe                     equ     20h                              ; xmit buf empty
rtpmask                 equ     0Bh                              ; rec/trans/prot int en
dsrbit                  equ     20h                              ; from modem status
ctsbit                  equ     10h                              ; from modem status
rtsbit                  equ     02h                              ; also with int en
dtrbit                  equ     01h                              ; to modem control
ien                     equ     08h                              ; interrupt enable
picack                  equ     20h                              ; 8259 acknowledge address
picmask                 equ     picack + 1                       ; 8259 int mask address
nseoi                   equ     20h                              ; non specific end of int
auxpic0                 equ     0EFh                             ; enable port 0 int bit
auxpic1                 equ     0F7h                             ; enable port 1 int bit
crtrowsc                equ     24                               ; crt height for CP/M  w/ stat line
crtrowsp                equ     25                               ; crt height for PC DOS  w/o stat line
crtcols                 equ     80                               ; crt width
sloffset                equ     crtrowsc * crtcols               ; status line offset
buffersize              equ     crtrowsp * crtcols * (numvircons*2 + 1)
monoseg                 equ     0B000h                           ; monochrome memory segment
colorseg                equ     0B800h                           ; color memory segment
monoport                equ     03B4h                            ; monochrome controller addr
colorport               equ     03D4h                            ; color controller addr
monocursor              equ     0B0Ch                            ; monochrome cursor code
colorcursor             equ     0607h                            ; color cursor code
compaqcursor            equ     0B0Ch                            ; hi-res cursor on color card
vrt                     equ     08h                              ; vertical retrace bit
hrt                     equ     01h                              ; horiz retrace bit
movsburst               equ     112                              ; string move per vert retrace
stosburst               equ     168                              ; string store per vert retrace
neg4                    equ     -4                               ; for reverse indexing
blank                   equ     0720h                            ; space
cursorstart             equ     10
cursorhi                equ     14
normcount               equ     5
insync                  equ     01h
outsync                 equ     02h
horiz                   equ     word ptr 0[si]
vert                    equ     word ptr 2[si]
topcorners              equ     word ptr 4[si]
botcorners              equ     word ptr 6[si]
vscursor                equ     word ptr 0[bx]                   ; cursor row,column
vscurcol                equ     byte ptr 0[bx]
vscurrow                equ     byte ptr 1[bx]
vstopleft               equ     word ptr 2[bx]                   ; t l window corner
vsleft                  equ     byte ptr 2[bx]
vstop                   equ     byte ptr 3[bx]
vsbotright              equ     word ptr 4[bx]                   ; b r window corner
vsright                 equ     byte ptr 4[bx]
vsbottom                equ     byte ptr 5[bx]
vsoldtl                 equ     word ptr 6[bx]                   ; last t l corner
vsoldbr                 equ     word ptr 8[bx]                   ; last b r corner
vsviewpoint             equ     word ptr 14[bx]                  ; window top left
vsrows                  equ     word ptr 16[bx]                  ; window row count
vsrowsb                 equ     byte ptr 16[bx]
vscols                  equ     word ptr 18[bx]                  ; window column count
vscolsb                 equ     byte ptr 18[bx]
vscorrect               equ     word ptr 20[bx]                  ; char position factor
vsvcseg                 equ     word ptr 22[bx]                  ; vc map base segment
vscrtseg                equ     word ptr 24[bx]                  ; base of screen memory
vslistptr               equ     word ptr 26[bx]                  ; start of row updates
vsattrib                equ     byte ptr 28[bx]                  ; current char attrib
vsmode                  equ     byte ptr 29[bx]                  ; wrap, cursor on/off
vscurtrack              equ     byte ptr 30[bx]                  ; cursor tracking mode
vswidth                 equ     byte ptr 31[bx]                  ; wrap width
vsnumber                equ     byte ptr 32[bx]                  ; virt console num
vsbit                   equ     byte ptr 33[bx]                  ; vc num = bit pos
vssavecursor            equ     word ptr 34[bx]                  ; cursor save loc
vsvector                equ     word ptr 36[bx]                  ; console state vector
vsxlat                  equ     word ptr 38[bx]                  ; mono/color xlat table
vscrtrows               equ     byte ptr 40[bx]                  ; 24 (cpm) or 25 (pc)
vspcshifts              equ     byte ptr 41[bx]                  ; pc mode shift state
vstrueview              equ     word ptr 42[bx]                  ; corrected view point
vstruecol               equ     byte ptr 42[bx]
vstruerow               equ     byte ptr 43[bx]
vscurtype               equ     word ptr 44[bx]                  ; mono or color
vspfktbl                equ     word ptr 46[bx]                  ; prog func key base
vspfkptr                equ     word ptr 48[bx]                  ; pointer to pfk table
vspfkcount              equ     byte ptr 50[bx]                  ; pfk count down
vspfkexp                equ     byte ptr 51[bx]                  ; pfk expansion flag
vsmx                    equ     byte ptr 52[bx]                  ; mutual exclusion sema
vsbackcount             equ     byte ptr 53[bx]                  ; XIOS back door count
vsbackax                equ     word ptr 54[bx]                  ; ax for XIOS back door
vsbackdx                equ     word ptr 60[bx]
vsscreenmode            equ     byte ptr 62[bx]                  ; alpha/graphics mode
vsscreensave            equ     byte ptr 63[bx]                  ; saves the old mode
sizevs                  equ     64
wrapbit                 equ     01h                              ; wrap mode enabled
cursorbit               equ     02h                              ; cursor displayed
revbit                  equ     04h                              ; reverse video mode
syncbit                 equ     08h                              ; sync crt accesses
matchbit                equ     10h                              ; image matches physical
pcmodebit               equ     20h                              ; pc mode for console & keyboard
initmode                equ     wrapbit + cursorbit + matchbit
crtfull                 equ     100h * (crtrowsc - 1) + (crtcols - 1)
VIDax                   equ     word ptr 0                       ;ax register
VIDal                   equ     byte ptr 0
VIDbx                   equ     word ptr 2                       ;bx register
VIDbl                   equ     byte ptr 2
VIDbh                   equ     byte ptr 3
VIDcx                   equ     word ptr 4                       ;cx register
VIDcl                   equ     byte ptr 4
VIDch                   equ     byte ptr 5
VIDdx                   equ     word ptr 6                       ;dx register
VIDdl                   equ     byte ptr 6
VIDdh                   equ     byte ptr 7
VIDvcons                equ     byte ptr 8                       ;virtual console number
bytespersector          equ     512
fdcport                 equ     03F2h                            ;all bits clear on channel reset
fdcstat                 equ     03F4h                            ;status port for disk controller
fdcrate                 equ     03F7h                            ;data rate for the new PC
fdcon                   equ     00001100b                        ;mask to keep the 8272 unreset
fdcresetbit             equ     00000100b                        ;8272 reset when low
fdccmndread             equ     01100110b                        ;mfm, skip deleted data, read
fdccmndwrite            equ     01000101b                        ;mfm, write
fdccmndformat           equ     01001101b                        ;mfm, format
fdccmndseek             equ     00001111b                        ;seek
fdccmndrecal            equ     00000111b                        ;home to track 0
fdccmndsi               equ     00001000b                        ;sense interupt status
fdccmndspec             equ     00000011b                        ;specify
fdcreadywrite           equ     10000000b                        ;mask for transfer ready
fdcreadyread            equ     10000000b                        ;mask for transfer ready
fdcspec1                equ     11001111b                        ;srt=0c, hd unload=0f 1st specify byte
fdcspec2                equ     00000010b                        ;hd load=1, mode=dma 2nd specify byte
fbytes                  equ     2                                ;magic number for 512 bytes per sector
fsectors                equ     8                                ;CP/M sectors per diskette track
fgap                    equ     50h                              ;this is IBM's, not August's
ffill                   equ     0E5h                             ;CP/M blank directory fill char
ratehyper96             equ     00h                              ;these values are output to the
ratehyper48             equ     01h                              ;  FDC rate port to set the data
rateslow48              equ     02h                              ;  transfer for different media
gaphyper96              equ     1Bh                              ;these values are used to set
gaphyper48              equ     23h                              ;  FDC gap length value for
gapslow48               equ     2Ah                              ;  both read and write
fgap96                  equ     54h                              ;96 tpi format gap value
eothyper96              equ     15                               ;number of sectors per track
eot48cpm                equ     8                                ;on cpm media
eot48dos9               equ     9                                ;on some dos media
topcylin48              equ     39                               ;top cylinder number on old drives
topcylin96              equ     79                               ;same for hyper drives
slowdrive               equ     01h                              ;these match the codes used in the
hyperdrive              equ     02h                              ;  cmos ram of the new 286 PC
MOTORONTICKSAT          equ     TICKSPERSECOND*3/4               ;* 3/4 second for AT
MOTORONTICKSPC          equ     TICKSPERSECOND/8                 ;* 1/8 second for PC/XT
MOTOROFFTICKS           equ     TICKSPERSECOND*4                 ;* 4 seconds after disk-op is done
DOOROPENTICKS           equ     TICKSPERSECOND*4                 ;* 4 seconds after disk-op is done
drive                   equ     byte ptr 14[bp]
mcnt                    equ     byte ptr 15[bp]
track                   equ     word ptr 12[bp]
sector                  equ     word ptr 10[bp]
dmaseg                  equ     word ptr 8[bp]
dmaoff                  equ     word ptr 6[bp]
gpfl                    equ     word ptr 16[bp]                  ; gap and fill used by format
dpb                     equ     8                                ;disk parameter block offset in DPH
PERM                    equ     8000h                            ;* permanent media indicator in CKS
pcsegment               equ     40h                              ; = pc mode base page
pcseekstatus            equ     3Eh                              ; = our recal_byte
pcmotorstatus           equ     3Fh                              ; = our motor_flags
pcdiskettestatus        equ     41h                              ; = our disk_error
pcchipstatus            equ     42h                              ; = our disk_results
pclastrate              equ     byte ptr .8Bh                    ;* last data rate (AT)
pcdskstate              equ     byte ptr .90h                    ;* current diskette state (AT)
pcdsktrk                equ     byte ptr .94h                    ;* current physical cylinder number
PCSTATEHYP96            equ     15h                              ;* hyper in hyper
PCSTATEHYP48            equ     74h                              ;* old med. in hyper
PCSTATESLOW48           equ     93h                              ;* old news
dmac2address            equ     004h                             ;8237 channel 2 address		rw
dmac2count              equ     005h                             ;8237 channel 2 transfer count	rw
dmastatreg              equ     008h                             ;8237 status register		ro
dmabmskreg              equ     dmastatreg+2                     ;8237 binary channel mask	wo
dmamodereg              equ     dmastatreg+3                     ;8237 mode register		wo
dmacbpf                 equ     dmastatreg+4                     ;8237 clear byte ptr f/f	wo
dmapagefdc              equ     081h                             ;a16 to a20 for channel 2
dmamodewritefdc         equ     01001010b
dmamodereadfdc          equ     01000110b
dmamodeverifyfdc        equ     01000010b
dmabmskfdc              equ     00000010b                        ;binary channel mask for disk
udaerrmode              equ     byte ptr .10h                    ; error mode byte in uda
errmodecode             equ     0FEh                             ; or 0FFh for quick return
wpcode                  equ     03h                              ; ROS definition
maxretry                equ     2                                ;dropped for copy prot schemes
motoroffcounter         equ     byte ptr .40h                    ;*now in ROS data seg
numfatids               equ     5                                ; number of supported id's
submsgsize              equ     19
SLOWSEEK                equ     0                                ;if -1, forces 3 ms step rate
IBMSYSID                equ     0AA55h                           ;partition label id word
HDSYSID                 equ     0DBh                             ;yours truly for CP/M
HDDOSID1                equ     01h                              ;for DOS 2.x
extflag1                equ     0FFFFh                           ;for DOS 2.x FATs
HDDOSID4                equ     04h                              ;for DOS 3.x
extflag2                equ     0FFFEh                           ;for DOS 3.x FATs
HDVFYERR                equ     0AAh                             ;artificial ROS error code
blocksize               equ     2048                             ;remap block size
sectorsize              equ     512                              ;cpm physical sectors
hdspt                   equ     17                               ;sectors per track on XT and AT
IBMfn                   equ     ds:byte ptr .00h
IBMerrcode              equ     ds:byte ptr .01h
IBMlun                  equ     ds:byte ptr .02h
IBMhead                 equ     ds:byte ptr .03h
IBMcylinder             equ     ds:word ptr .04h
IBMsector               equ     ds:byte ptr .06h
IBMcount                equ     ds:byte ptr .07h
IBMxferofs              equ     ds:word ptr .08h
IBMxferseg              equ     ds:word ptr .0Ah
IBMXFERPTR              equ     dword ptr ibmxferofs
XTPTbootfl              equ     ds:byte ptr .00h
XTPTstarthead           equ     ds:byte ptr .01h
XTPTstartsector         equ     ds:byte ptr .02h
XTPTstartcylinder       equ     ds:byte ptr .03h
XTPTsystem              equ     ds:byte ptr .04h
XTPTendhead             equ     ds:byte ptr .05h
XTPTendsector           equ     ds:byte ptr .06h
XTPTendcylinder         equ     ds:byte ptr .07h
XTPTrelsect             equ     ds:word ptr .08h
XTPTsize                equ     ds:word ptr .0Ch
XTPTRECSIZE             equ     16
XTLBLcode               equ     ds:byte ptr .00h
XTLBLpart1              equ     ds:byte ptr .01BEh
XTLBLpart2              equ     ds:byte ptr .01CEh
XTLBLpart3              equ     ds:byte ptr .01DEh
XTLBLpart4              equ     ds:byte ptr .01EEh
XTLBLid                 equ     ds:word ptr .01FEh
HDLBchks                equ     ds:word ptr .00h
HDLBid                  equ     ds:byte ptr .02h
HDLBpstart              equ     ds:word ptr .021h
HDLBplength             equ     ds:word ptr .023h
HDLBnheads              equ     ds:byte ptr .025h
HDLBibmspt              equ     ds:byte ptr .026h
HDLBcpmoptions          equ     ds:byte ptr .027h
HDLBcpmnsect            equ     ds:byte ptr .028h
HDLBcpmdpb              equ     ds:byte ptr .029h
HDLBcpmspt              equ     ds:word ptr .029h
HDLBcpmbsh              equ     ds:byte ptr .02Bh
HDLBcpmblm              equ     ds:byte ptr .02Ch
HDLBcpmexm              equ     ds:byte ptr .02Dh
HDLBcpmdsm              equ     ds:word ptr .02Eh
HDLBcpmdrm              equ     ds:word ptr .030h
HDLBcpmal0              equ     ds:byte ptr .032h
HDLBcpmal1              equ     ds:byte ptr .033h
HDLBcpmcks              equ     ds:word ptr .034h
HDLBcpmoff              equ     ds:word ptr .036h
HDLBcpmpsh              equ     ds:byte ptr .038h
HDLBcpmprm              equ     ds:byte ptr .039h
HDLBcpmrsvd             equ     ds:word ptr .03Ah
HDLBmapctl              equ     ds:byte ptr .040h
HDLBmapspb              equ     ds:word ptr .040h
HDLBmapmax              equ     ds:word ptr .042h
HDLBmapcnt              equ     ds:word ptr .044h
HDLBmapspareend         equ     ds:word ptr .046h
HDLBmaptable            equ     ds:word ptr .048h
HDLABELSIZE             equ     512
HDINFexists             equ     ds:byte ptr .00h
HDINFlogged             equ     ds:byte ptr .01h
HDINFfixed              equ     ds:byte ptr .02h
HDINFheads              equ     ds:byte ptr .03h
HDINFspt                equ     ds:byte ptr .04h
HDINFcyl                equ     ds:word ptr .05h
HDINFenddir             equ     ds:word ptr .07h
HDINFlabelofs           equ     ds:word ptr .09h
HDINFpclogged           equ     ds:byte ptr .0Bh
HDINFSIZE               equ     12
HDINTERRUPT             equ     13h                              ;IBM entry point for hard disk
HDROSDATASEG            equ     40h
HDOPTIONADDR            equ     76h                              ;ibm controller option control
HDPTR                   equ     dword ptr HDINTERRUPT * 4
hdcontrolbyte           equ     byte ptr HDROSDATASEG*16 + HDOPTIONADDR
dphsize                 equ     20
PCBRsecsiz              equ     word ptr 11                      ; # of bytes per sector (512)
PCBRallocsiz            equ     byte ptr 13                      ; # of sectors per allocation unit
PCBRreserved            equ     word ptr 14                      ; # of reserved sectors (1)
PCBRnfats               equ     byte ptr 16                      ; # of fats
PCBRdirmax              equ     word ptr 17                      ; # of directory entries
PCBRtotsec              equ     word ptr 19                      ; # of sectors total in image
PCBRfatsec              equ     word ptr 22                      ; # of sectors in a fat
PCDPBextflag            equ     word ptr 0
PCDPBnfat               equ     word ptr 2
PCDPBfatrec             equ     word ptr 4
PCDPBnclstrs            equ     word ptr 6
PCDPBclsize             equ     word ptr 8
PCDPBfatadd             equ     word ptr 10
PCDPBspt                equ     word ptr 12
PCDPBbsh                equ     byte ptr 14
PCDPBblm                equ     byte ptr 15
PCDPBdsm                equ     word ptr 17
PCDPBdirsiz             equ     word ptr 19
PCDPBcksiz              equ     word ptr 23
divideinterrupt         equ     00h
nmiinterrupt            equ     02h
overflowinterrupt       equ     04h
clockinterrupt          equ     08h
keyboardinterrupt       equ     09h
aux1interrupt           equ     0Bh
aux0interrupt           equ     0Ch
diskinterrupt           equ     0Eh
equipint                equ     11h                              ; ROS equipment check int
memint                  equ     12h                              ; ROS memory check int
diskint                 equ     13h                              ; ROS disk int
asyncint                equ     14h                              ; ROS async port int
printint                equ     17h                              ; ROS printer int
breakinterrupt          equ     1Bh                              ; user keyboard break
tickinterrupt           equ     1Ch                              ; user tick vector
diskparmsinterrupt      equ     1Eh                              ;* diskette parameters ptr.
int1Evecoff             equ     diskparmsinterrupt * 4
int1Evecseg             equ     int1Evecoff + 2
hdcodeinterrupt         equ     40h                              ; pass along to floppy
flaginterrupt           equ     228                              ; to get an unused flag
fiddsinterrupt          equ     229                              ; for attachamatic drives
xiosinterrupt           equ     230                              ; for ver 1.0 back door
dphdpb                  equ     word ptr 8
dphhstbl                equ     word ptr 18
dpbdrm                  equ     word ptr 7
                        codemacro FNINIT
                        dw      0e3dbh
                        endm
                        codemacro FNDISI
                        dw      0e1dbh
                        endm
                        codemacro FNSTCW   dst:Mw
                        segfix  dst
                        db      0d9h
                        modrm   7,dst
                        endm
                        codemacro FNCLEX
                        dw      0e2dbh
                        endm
                        codemacro FNSTENV dst:M
                        segfix  dst
                        db      0d9h
                        modrm   6,dst
                        endm
                        codemacro FLDENV  src:M
                        db      9bh
                        segfix  src
                        db      0d9h
                        modrm   4,src
                        endm
                        CodeMacro popf286  addr:Cw
                        db      0eh                              ; push	cs
                        db      0e8h
                        RelW    addr                             ; call iret286	flags,cs,ip on stack
                        EndM
