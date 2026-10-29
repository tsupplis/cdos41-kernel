/* ATTRDEF.H	-   Set of defines to transform user defined attributes */

/*			    Copyright (c) 1984	RTEK Inc.		    */
/*						2265 E. Becker Lane	    */
/*						Phoenix, Arizona 85028	    */
/*						(602) 867-9336		    */

#define REV_V(x)  (( (x) & 0x07 ) << 4 ) | (( (x) & 0x70 ) >> 4 )
#define IBM_DEF_ATTR 0x07		/* IBM default attribute  */

/*  define Default attribute		*/

#if DEF_C_SC == SC_NORM
#define     DEF_AT  DEF_C
#endif

#if DEF_C_SC == SC_BRIGHT
#define     DEF_AT  DEF_C | BRIGHT
#endif

#if DEF_C_SC == SC_BLINK
#define     DEF_AT  DEF_C | BLINK
#endif

#if DEF_C_SC == SC_BOTH
#define     DEF_AT  DEF_C | BLINK | BRIGHT
#endif

#if DEF_C_SC == SC_RV
#define     DEF_AT  REV_V( DEF_C )
#endif

#if DEF_C_SC == SC_RV_BRIGHT
#define     DEF_AT  REV_V( DEF_C ) | BRIGHT
#endif

#if DEF_C_SC == SC_RV_BLINK
#define     DEF_AT  REV_V( DEF_C ) | BLINK
#endif

#if DEF_C_SC == SC_RV_BOTH
#define     DEF_AT  REV_V( DEF_C ) | BLINK | BRIGHT
#endif

/*  define Screen Title Attribute	*/

#if TIT_C_SC == SC_NORM
#define     TIT_AT  TIT_C
#endif

#if TIT_C_SC == SC_BRIGHT
#define     TIT_AT  TIT_C | BRIGHT
#endif

#if TIT_C_SC == SC_BLINK
#define     TIT_AT  TIT_C | BLINK
#endif

#if TIT_C_SC == SC_BOTH
#define     TIT_AT  TIT_C | BLINK | BRIGHT
#endif

#if TIT_C_SC == SC_RV
#define     TIT_AT  REV_V( TIT_C )
#endif

#if TIT_C_SC == SC_RV_BRIGHT
#define     TIT_AT  REV_V( TIT_C ) | BRIGHT
#endif

#if TIT_C_SC == SC_RV_BLINK
#define     TIT_AT  REV_V( TIT_C ) | BLINK
#endif

#if TIT_C_SC == SC_RV_BOTH
#define     TIT_AT  REV_V( TIT_C ) | BLINK | BRIGHT
#endif

/*  define background Attribute       */

#if BKG_C_SC == SC_NORM
#define     BKG_AT  BKG_C
#endif

#if BKG_C_SC == SC_BRIGHT
#define     BKG_AT  BKG_C | BRIGHT
#endif

#if BKG_C_SC == SC_BLINK
#define     BKG_AT  BKG_C | BLINK
#endif

#if BKG_C_SC == SC_BOTH
#define     BKG_AT  BKG_C | BLINK | BRIGHT
#endif

#if BKG_C_SC == SC_RV
#define     BKG_AT  REV_V( BKG_C )
#endif

#if BKG_C_SC == SC_RV_BRIGHT
#define     BKG_AT  REV_V( BKG_C ) | BRIGHT
#endif

#if BKG_C_SC == SC_RV_BLINK
#define     BKG_AT  REV_V( BKG_C ) | BLINK
#endif

#if BKG_C_SC == SC_RV_BOTH
#define     BKG_AT  REV_V( BKG_C ) | BLINK | BRIGHT
#endif

/*  define input Attribute	 */

#if INP_C_SC == SC_NORM
#define     INP_AT  INP_C
#endif

#if INP_C_SC == SC_BRIGHT
#define     INP_AT  INP_C | BRIGHT
#endif

#if INP_C_SC == SC_BLINK
#define     INP_AT  INP_C | BLINK
#endif

#if INP_C_SC == SC_BOTH
#define     INP_AT  INP_C | BLINK | BRIGHT
#endif

#if INP_C_SC == SC_RV
#define     INP_AT  REV_V( INP_C )
#endif

#if INP_C_SC == SC_RV_BRIGHT
#define     INP_AT  REV_V( INP_C ) | BRIGHT
#endif

#if INP_C_SC == SC_RV_BLINK
#define     INP_AT  REV_V( INP_C ) | BLINK
#endif

#if INP_C_SC == SC_RV_BOTH
#define     INP_AT  REV_V( INP_C ) | BLINK | BRIGHT
#endif

/*  define modifiable fields Attribute	     */

#if MOD_C_SC == SC_NORM
#define     MOD_AT  MOD_C
#endif

#if MOD_C_SC == SC_BRIGHT
#define     MOD_AT  MOD_C | BRIGHT
#endif

#if MOD_C_SC == SC_BLINK
#define     MOD_AT  MOD_C | BLINK
#endif

#if MOD_C_SC == SC_BOTH
#define     MOD_AT  MOD_C | BLINK | BRIGHT
#endif

#if MOD_C_SC == SC_RV
#define     MOD_AT  REV_V( MOD_C )
#endif

#if MOD_C_SC == SC_RV_BRIGHT
#define     MOD_AT  REV_V( MOD_C ) | BRIGHT
#endif

#if MOD_C_SC == SC_RV_BLINK
#define     MOD_AT  REV_V( MOD_C ) | BLINK
#endif

#if MOD_C_SC == SC_RV_BOTH
#define     MOD_AT  REV_V( MOD_C ) | BLINK | BRIGHT
#endif

/*  define Error Messages Attribute	  */

#if ERR_C_SC == SC_NORM
#define     ERR_AT  ERR_C
#endif

#if ERR_C_SC == SC_BRIGHT
#define     ERR_AT  ERR_C | BRIGHT
#endif

#if ERR_C_SC == SC_BLINK
#define     ERR_AT  ERR_C | BLINK
#endif

#if ERR_C_SC == SC_BOTH
#define     ERR_AT  ERR_C | BLINK | BRIGHT
#endif

#if ERR_C_SC == SC_RV
#define     ERR_AT  REV_V( ERR_C )
#endif

#if ERR_C_SC == SC_RV_BRIGHT
#define     ERR_AT  REV_V( ERR_C ) | BRIGHT
#endif

#if ERR_C_SC == SC_RV_BLINK
#define     ERR_AT  REV_V( ERR_C ) | BLINK
#endif

#if ERR_C_SC == SC_RV_BOTH
#define     ERR_AT  REV_V( ERR_C ) | BLINK | BRIGHT
#endif

/*  define Options Attribute	   */

#if OPT_C_SC == SC_NORM
#define     OPT_AT  OPT_C
#endif

#if OPT_C_SC == SC_BRIGHT
#define     OPT_AT  OPT_C | BRIGHT
#endif

#if OPT_C_SC == SC_BLINK
#define     OPT_AT  OPT_C | BLINK
#endif

#if OPT_C_SC == SC_BOTH
#define     OPT_AT  OPT_C | BLINK | BRIGHT
#endif

#if OPT_C_SC == SC_RV
#define     OPT_AT  REV_V( OPT_C )
#endif

#if OPT_C_SC == SC_RV_BRIGHT
#define     OPT_AT  REV_V( OPT_C ) | BRIGHT
#endif

#if OPT_C_SC == SC_RV_BLINK
#define     OPT_AT  REV_V( OPT_C ) | BLINK
#endif

#if OPT_C_SC == SC_RV_BOTH
#define     OPT_AT  REV_V( OPT_C ) | BLINK | BRIGHT
#endif

/*  define Other Messages Attribute	  */

#if OTH_C_SC == SC_NORM
#define     OTH_AT  OTH_C
#endif

#if OTH_C_SC == SC_BRIGHT
#define     OTH_AT  OTH_C | BRIGHT
#endif

#if OTH_C_SC == SC_BLINK
#define     OTH_AT  OTH_C | BLINK
#endif

#if OTH_C_SC == SC_BOTH
#define     OTH_AT  OTH_C | BLINK | BRIGHT
#endif

#if OTH_C_SC == SC_RV
#define     OTH_AT  REV_V( OTH_C )
#endif

#if OTH_C_SC == SC_RV_BRIGHT
#define     OTH_AT  REV_V( OTH_C ) | BRIGHT
#endif

#if OTH_C_SC == SC_RV_BLINK
#define     OTH_AT  REV_V( OTH_C ) | BLINK
#endif

#if OTH_C_SC == SC_RV_BOTH
#define     OTH_AT  REV_V( OTH_C ) | BLINK | BRIGHT
#endif

/*  define Special Effects 1 Attribute	     */

#if SP1_C_SC == SC_NORM
#define     SP1_AT  SP1_C
#endif

#if SP1_C_SC == SC_BRIGHT
#define     SP1_AT  SP1_C | BRIGHT
#endif

#if SP1_C_SC == SC_BLINK
#define     SP1_AT  SP1_C | BLINK
#endif

#if SP1_C_SC == SC_BOTH
#define     SP1_AT  SP1_C | BLINK | BRIGHT
#endif

#if SP1_C_SC == SC_RV
#define     SP1_AT  REV_V( SP1_C )
#endif

#if SP1_C_SC == SC_RV_BRIGHT
#define     SP1_AT  REV_V( SP1_C ) | BRIGHT
#endif

#if SP1_C_SC == SC_RV_BLINK
#define     SP1_AT  REV_V( SP1_C ) | BLINK
#endif

#if SP1_C_SC == SC_RV_BOTH
#define     SP1_AT  REV_V( SP1_C ) | BLINK | BRIGHT
#endif

/*  define Special Effects 2 Attribute	     */

#if SP2_C_SC == SC_NORM
#define     SP2_AT  SP2_C
#endif

#if SP2_C_SC == SC_BRIGHT
#define     SP2_AT  SP2_C | BRIGHT
#endif

#if SP2_C_SC == SC_BLINK
#define     SP2_AT  SP2_C | BLINK
#endif

#if SP2_C_SC == SC_BOTH
#define     SP2_AT  SP2_C | BLINK | BRIGHT
#endif

#if SP2_C_SC == SC_RV
#define     SP2_AT  REV_V( SP2_C )
#endif

#if SP2_C_SC == SC_RV_BRIGHT
#define     SP2_AT  REV_V( SP2_C ) | BRIGHT
#endif

#if SP2_C_SC == SC_RV_BLINK
#define     SP2_AT  REV_V( SP2_C ) | BLINK
#endif

#if SP2_C_SC == SC_RV_BOTH
#define     SP2_AT  REV_V( SP2_C ) | BLINK | BRIGHT
#endif

/*  define Special Effects 3 Attribute	     */

#if SP3_C_SC == SC_NORM
#define     SP3_AT  SP3_C
#endif

#if SP3_C_SC == SC_BRIGHT
#define     SP3_AT  SP3_C | BRIGHT
#endif

#if SP3_C_SC == SC_BLINK
#define     SP3_AT  SP3_C | BLINK
#endif

#if SP3_C_SC == SC_BOTH
#define     SP3_AT  SP3_C | BLINK | BRIGHT
#endif

#if SP3_C_SC == SC_RV
#define     SP3_AT  REV_V( SP3_C )
#endif

#if SP3_C_SC == SC_RV_BRIGHT
#define     SP3_AT  REV_V( SP3_C ) | BRIGHT
#endif

#if SP3_C_SC == SC_RV_BLINK
#define     SP3_AT  REV_V( SP3_C ) | BLINK
#endif

#if SP3_C_SC == SC_RV_BOTH
#define     SP3_AT  REV_V( SP3_C ) | BLINK | BRIGHT
#endif

/*  define Special Effects 4 Attribute	     */

#if SP4_C_SC == SC_NORM
#define     SP4_AT  SP4_C
#endif

#if SP4_C_SC == SC_BRIGHT
#define     SP4_AT  SP4_C | BRIGHT
#endif

#if SP4_C_SC == SC_BLINK
#define     SP4_AT  SP4_C | BLINK
#endif

#if SP4_C_SC == SC_BOTH
#define     SP4_AT  SP4_C | BLINK | BRIGHT
#endif

#if SP4_C_SC == SC_RV
#define     SP4_AT  REV_V( SP4_C )
#endif

#if SP4_C_SC == SC_RV_BRIGHT
#define     SP4_AT  REV_V( SP4_C ) | BRIGHT
#endif

#if SP4_C_SC == SC_RV_BLINK
#define     SP4_AT  REV_V( SP4_C ) | BLINK
#endif

#if SP4_C_SC == SC_RV_BOTH
#define     SP4_AT  REV_V( SP4_C ) | BLINK | BRIGHT
#endif

/*  define Special Effects 5 Attribute	     */

#if SP5_C_SC == SC_NORM
#define     SP5_AT  SP5_C
#endif

#if SP5_C_SC == SC_BRIGHT
#define     SP5_AT  SP5_C | BRIGHT
#endif

#if SP5_C_SC == SC_BLINK
#define     SP5_AT  SP5_C | BLINK
#endif

#if SP5_C_SC == SC_BOTH
#define     SP5_AT  SP5_C | BLINK | BRIGHT
#endif

#if SP5_C_SC == SC_RV
#define     SP5_AT  REV_V( SP5_C )
#endif

#if SP5_C_SC == SC_RV_BRIGHT
#define     SP5_AT  REV_V( SP5_C ) | BRIGHT
#endif

#if SP5_C_SC == SC_RV_BLINK
#define     SP5_AT  REV_V( SP5_C ) | BLINK
#endif

#if SP5_C_SC == SC_RV_BOTH
#define     SP5_AT  REV_V( SP5_C ) | BLINK | BRIGHT
#endif

/*  define Special Effects 6 Attribute	     */

#if SP6_C_SC == SC_NORM
#define     SP6_AT  SP6_C
#endif

#if SP6_C_SC == SC_BRIGHT
#define     SP6_AT  SP6_C | BRIGHT
#endif

#if SP6_C_SC == SC_BLINK
#define     SP6_AT  SP6_C | BLINK
#endif

#if SP6_C_SC == SC_BOTH
#define     SP6_AT  SP6_C | BLINK | BRIGHT
#endif

#if SP6_C_SC == SC_RV
#define     SP6_AT  REV_V( SP6_C )
#endif

#if SP6_C_SC == SC_RV_BRIGHT
#define     SP6_AT  REV_V( SP6_C ) | BRIGHT
#endif

#if SP6_C_SC == SC_RV_BLINK
#define     SP6_AT  REV_V( SP6_C ) | BLINK
#endif

#if SP6_C_SC == SC_RV_BOTH
#define     SP6_AT  REV_V( SP6_C ) | BLINK | BRIGHT
#endif

/*  define Special Effects 7 Attribute	     */

#if SP7_C_SC == SC_NORM
#define     SP7_AT  SP7_C
#endif

#if SP7_C_SC == SC_BRIGHT
#define     SP7_AT  SP7_C | BRIGHT
#endif

#if SP7_C_SC == SC_BLINK
#define     SP7_AT  SP7_C | BLINK
#endif

#if SP7_C_SC == SC_BOTH
#define     SP7_AT  SP7_C | BLINK | BRIGHT
#endif

#if SP7_C_SC == SC_RV
#define     SP7_AT  REV_V( SP7_C )
#endif

#if SP7_C_SC == SC_RV_BRIGHT
#define     SP7_AT  REV_V( SP7_C ) | BRIGHT
#endif

#if SP7_C_SC == SC_RV_BLINK
#define     SP7_AT  REV_V( SP7_C ) | BLINK
#endif

#if SP7_C_SC == SC_RV_BOTH
#define     SP7_AT  REV_V( SP7_C ) | BLINK | BRIGHT
#endif

/*  define Special Effects 8 Attribute	     */

#if SP8_C_SC == SC_NORM
#define     SP8_AT  SP8_C
#endif

#if SP8_C_SC == SC_BRIGHT
#define     SP8_AT  SP8_C | BRIGHT
#endif

#if SP8_C_SC == SC_BLINK
#define     SP8_AT  SP8_C | BLINK
#endif

#if SP8_C_SC == SC_BOTH
#define     SP8_AT  SP8_C | BLINK | BRIGHT
#endif

#if SP8_C_SC == SC_RV
#define     SP8_AT  REV_V( SP8_C )
#endif

#if SP8_C_SC == SC_RV_BRIGHT
#define     SP8_AT  REV_V( SP8_C ) | BRIGHT
#endif

#if SP8_C_SC == SC_RV_BLINK
#define     SP8_AT  REV_V( SP8_C ) | BLINK
#endif

#if SP8_C_SC == SC_RV_BOTH
#define     SP8_AT  REV_V( SP8_C ) | BLINK | BRIGHT
#endif

/*  define Special Effects 9 Attribute	     */

#if SP9_C_SC == SC_NORM
#define     SP9_AT  SP9_C
#endif

#if SP9_C_SC == SC_BRIGHT
#define     SP9_AT  SP9_C | BRIGHT
#endif

#if SP9_C_SC == SC_BLINK
#define     SP9_AT  SP9_C | BLINK
#endif

#if SP9_C_SC == SC_BOTH
#define     SP9_AT  SP9_C | BLINK | BRIGHT
#endif

#if SP9_C_SC == SC_RV
#define     SP9_AT  REV_V( SP9_C )
#endif

#if SP9_C_SC == SC_RV_BRIGHT
#define     SP9_AT  REV_V( SP9_C ) | BRIGHT
#endif

#if SP9_C_SC == SC_RV_BLINK
#define     SP9_AT  REV_V( SP9_C ) | BLINK
#endif

#if SP9_C_SC == SC_RV_BOTH
#define     SP9_AT  REV_V( SP9_C ) | BLINK | BRIGHT
#endif

/*  define Special Effects 10 Attribute       */

#if SP10_C_SC == SC_NORM
#define     SP10_AT  SP10_C
#endif

#if SP10_C_SC == SC_BRIGHT
#define     SP10_AT  SP10_C | BRIGHT
#endif

#if SP10_C_SC == SC_BLINK
#define     SP10_AT  SP10_C | BLINK
#endif

#if SP10_C_SC == SC_BOTH
#define     SP10_AT  SP10_C | BLINK | BRIGHT
#endif

#if SP10_C_SC == SC_RV
#define     SP10_AT  REV_V( SP10_C )
#endif

#if SP10_C_SC == SC_RV_BRIGHT
#define     SP10_AT  REV_V( SP10_C ) | BRIGHT
#endif

#if SP10_C_SC == SC_RV_BLINK
#define     SP10_AT  REV_V( SP10_C ) | BLINK
#endif

#if SP10_C_SC == SC_RV_BOTH
#define     SP10_AT  REV_V( SP10_C ) | BLINK | BRIGHT
#endif

/*  define Special Effects 11 Attribute       */

#if SP11_C_SC == SC_NORM
#define     SP11_AT  SP11_C
#endif

#if SP11_C_SC == SC_BRIGHT
#define     SP11_AT  SP11_C | BRIGHT
#endif

#if SP11_C_SC == SC_BLINK
#define     SP11_AT  SP11_C | BLINK
#endif

#if SP11_C_SC == SC_BOTH
#define     SP11_AT  SP11_C | BLINK | BRIGHT
#endif

#if SP11_C_SC == SC_RV
#define     SP11_AT  REV_V( SP11_C )
#endif

#if SP11_C_SC == SC_RV_BRIGHT
#define     SP11_AT  REV_V( SP11_C ) | BRIGHT
#endif

#if SP11_C_SC == SC_RV_BLINK
#define     SP11_AT  REV_V( SP11_C ) | BLINK
#endif

#if SP11_C_SC == SC_RV_BOTH
#define     SP11_AT  REV_V( SP11_C ) | BLINK | BRIGHT
#endif

/*  define Special Effects 12 Attribute       */

#if SP12_C_SC == SC_NORM
#define     SP12_AT  SP12_C
#endif

#if SP12_C_SC == SC_BRIGHT
#define     SP12_AT  SP12_C | BRIGHT
#endif

#if SP12_C_SC == SC_BLINK
#define     SP12_AT  SP12_C | BLINK
#endif

#if SP12_C_SC == SC_BOTH
#define     SP12_AT  SP12_C | BLINK | BRIGHT
#endif

#if SP12_C_SC == SC_RV
#define     SP12_AT  REV_V( SP12_C )
#endif

#if SP12_C_SC == SC_RV_BRIGHT
#define     SP12_AT  REV_V( SP12_C ) | BRIGHT
#endif

#if SP12_C_SC == SC_RV_BLINK
#define     SP12_AT  REV_V( SP12_C ) | BLINK
#endif

#if SP12_C_SC == SC_RV_BOTH
#define     SP12_AT  REV_V( SP12_C ) | BLINK | BRIGHT
#endif

/*  define Special Effects 13 Attribute       */

#if SP13_C_SC == SC_NORM
#define     SP13_AT  SP13_C
#endif

#if SP13_C_SC == SC_BRIGHT
#define     SP13_AT  SP13_C | BRIGHT
#endif

#if SP13_C_SC == SC_BLINK
#define     SP13_AT  SP13_C | BLINK
#endif

#if SP13_C_SC == SC_BOTH
#define     SP13_AT  SP13_C | BLINK | BRIGHT
#endif

#if SP13_C_SC == SC_RV
#define     SP13_AT  REV_V( SP13_C )
#endif

#if SP13_C_SC == SC_RV_BRIGHT
#define     SP13_AT  REV_V( SP13_C ) | BRIGHT
#endif

#if SP13_C_SC == SC_RV_BLINK
#define     SP13_AT  REV_V( SP13_C ) | BLINK
#endif

#if SP13_C_SC == SC_RV_BOTH
#define     SP13_AT  REV_V( SP13_C ) | BLINK | BRIGHT
#endif

/*  define Special Effects 14 Attribute       */

#if SP14_C_SC == SC_NORM
#define     SP14_AT  SP14_C
#endif

#if SP14_C_SC == SC_BRIGHT
#define     SP14_AT  SP14_C | BRIGHT
#endif

#if SP14_C_SC == SC_BLINK
#define     SP14_AT  SP14_C | BLINK
#endif

#if SP14_C_SC == SC_BOTH
#define     SP14_AT  SP14_C | BLINK | BRIGHT
#endif

#if SP14_C_SC == SC_RV
#define     SP14_AT  REV_V( SP14_C )
#endif

#if SP14_C_SC == SC_RV_BRIGHT
#define     SP14_AT  REV_V( SP14_C ) | BRIGHT
#endif

#if SP14_C_SC == SC_RV_BLINK
#define     SP14_AT  REV_V( SP14_C ) | BLINK
#endif

#if SP14_C_SC == SC_RV_BOTH
#define     SP14_AT  REV_V( SP14_C ) | BLINK | BRIGHT
#endif

/*  define Special Effects 15 Attribute       */

#if SP15_C_SC == SC_NORM
#define     SP15_AT  SP15_C
#endif

#if SP15_C_SC == SC_BRIGHT
#define     SP15_AT  SP15_C | BRIGHT
#endif

#if SP15_C_SC == SC_BLINK
#define     SP15_AT  SP15_C | BLINK
#endif

#if SP15_C_SC == SC_BOTH
#define     SP15_AT  SP15_C | BLINK | BRIGHT
#endif

#if SP15_C_SC == SC_RV
#define     SP15_AT  REV_V( SP15_C )
#endif

#if SP15_C_SC == SC_RV_BRIGHT
#define     SP15_AT  REV_V( SP15_C ) | BRIGHT
#endif

#if SP15_C_SC == SC_RV_BLINK
#define     SP15_AT  REV_V( SP15_C ) | BLINK
#endif

#if SP15_C_SC == SC_RV_BOTH
#define     SP15_AT  REV_V( SP15_C ) | BLINK | BRIGHT
#endif

/*  define Special Effects 16 Attribute       */

#if SP16_C_SC == SC_NORM
#define     SP16_AT  SP16_C
#endif

#if SP16_C_SC == SC_BRIGHT
#define     SP16_AT  SP16_C | BRIGHT
#endif

#if SP16_C_SC == SC_BLINK
#define     SP16_AT  SP16_C | BLINK
#endif

#if SP16_C_SC == SC_BOTH
#define     SP16_AT  SP16_C | BLINK | BRIGHT
#endif

#if SP16_C_SC == SC_RV
#define     SP16_AT  REV_V( SP16_C )
#endif

#if SP16_C_SC == SC_RV_BRIGHT
#define     SP16_AT  REV_V( SP16_C ) | BRIGHT
#endif

#if SP16_C_SC == SC_RV_BLINK
#define     SP16_AT  REV_V( SP16_C ) | BLINK
#endif

#if SP16_C_SC == SC_RV_BOTH
#define     SP16_AT  REV_V( SP16_C ) | BLINK | BRIGHT
#endif

/*  define Special Effects 17 Attribute       */

#if SP17_C_SC == SC_NORM
#define     SP17_AT  SP17_C
#endif

#if SP17_C_SC == SC_BRIGHT
#define     SP17_AT  SP17_C | BRIGHT
#endif

#if SP17_C_SC == SC_BLINK
#define     SP17_AT  SP17_C | BLINK
#endif

#if SP17_C_SC == SC_BOTH
#define     SP17_AT  SP17_C | BLINK | BRIGHT
#endif

#if SP17_C_SC == SC_RV
#define     SP17_AT  REV_V( SP17_C )
#endif

#if SP17_C_SC == SC_RV_BRIGHT
#define     SP17_AT  REV_V( SP17_C ) | BRIGHT
#endif

#if SP17_C_SC == SC_RV_BLINK
#define     SP17_AT  REV_V( SP17_C ) | BLINK
#endif

#if SP17_C_SC == SC_RV_BOTH
#define     SP17_AT  REV_V( SP17_C ) | BLINK | BRIGHT
#endif

/*  define Special Effects 18 Attribute       */

#if SP18_C_SC == SC_NORM
#define     SP18_AT  SP18_C
#endif

#if SP18_C_SC == SC_BRIGHT
#define     SP18_AT  SP18_C | BRIGHT
#endif

#if SP18_C_SC == SC_BLINK
#define     SP18_AT  SP18_C | BLINK
#endif

#if SP18_C_SC == SC_BOTH
#define     SP18_AT  SP18_C | BLINK | BRIGHT
#endif

#if SP18_C_SC == SC_RV
#define     SP18_AT  REV_V( SP18_C )
#endif

#if SP18_C_SC == SC_RV_BRIGHT
#define     SP18_AT  REV_V( SP18_C ) | BRIGHT
#endif

#if SP18_C_SC == SC_RV_BLINK
#define     SP18_AT  REV_V( SP18_C ) | BLINK
#endif

#if SP18_C_SC == SC_RV_BOTH
#define     SP18_AT  REV_V( SP18_C ) | BLINK | BRIGHT
#endif

/*  define Special Effects 19 Attribute       */

#if SP19_C_SC == SC_NORM
#define     SP19_AT  SP19_C
#endif

#if SP19_C_SC == SC_BRIGHT
#define     SP19_AT  SP19_C | BRIGHT
#endif

#if SP19_C_SC == SC_BLINK
#define     SP19_AT  SP19_C | BLINK
#endif

#if SP19_C_SC == SC_BOTH
#define     SP19_AT  SP19_C | BLINK | BRIGHT
#endif

#if SP19_C_SC == SC_RV
#define     SP19_AT  REV_V( SP19_C )
#endif

#if SP19_C_SC == SC_RV_BRIGHT
#define     SP19_AT  REV_V( SP19_C ) | BRIGHT
#endif

#if SP19_C_SC == SC_RV_BLINK
#define     SP19_AT  REV_V( SP19_C ) | BLINK
#endif

#if SP19_C_SC == SC_RV_BOTH
#define     SP19_AT  REV_V( SP19_C ) | BLINK | BRIGHT
#endif

/*  define Special Effects 20 Attribute       */

#if SP20_C_SC == SC_NORM
#define     SP20_AT  SP20_C
#endif

#if SP20_C_SC == SC_BRIGHT
#define     SP20_AT  SP20_C | BRIGHT
#endif

#if SP20_C_SC == SC_BLINK
#define     SP20_AT  SP20_C | BLINK
#endif

#if SP20_C_SC == SC_BOTH
#define     SP20_AT  SP20_C | BLINK | BRIGHT
#endif

#if SP20_C_SC == SC_RV
#define     SP20_AT  REV_V( SP20_C )
#endif

#if SP20_C_SC == SC_RV_BRIGHT
#define     SP20_AT  REV_V( SP20_C ) | BRIGHT
#endif

#if SP20_C_SC == SC_RV_BLINK
#define     SP20_AT  REV_V( SP20_C ) | BLINK
#endif

#if SP20_C_SC == SC_RV_BOTH
#define     SP20_AT  REV_V( SP20_C ) | BLINK | BRIGHT
#endif

/*  define Special Effects 21 Attribute       */

#if SP21_C_SC == SC_NORM
#define     SP21_AT  SP21_C
#endif

#if SP21_C_SC == SC_BRIGHT
#define     SP21_AT  SP21_C | BRIGHT
#endif

#if SP21_C_SC == SC_BLINK
#define     SP21_AT  SP21_C | BLINK
#endif

#if SP21_C_SC == SC_BOTH
#define     SP21_AT  SP21_C | BLINK | BRIGHT
#endif

#if SP21_C_SC == SC_RV
#define     SP21_AT  REV_V( SP21_C )
#endif

#if SP21_C_SC == SC_RV_BRIGHT
#define     SP21_AT  REV_V( SP21_C ) | BRIGHT
#endif

#if SP21_C_SC == SC_RV_BLINK
#define     SP21_AT  REV_V( SP21_C ) | BLINK
#endif

#if SP21_C_SC == SC_RV_BOTH
#define     SP21_AT  REV_V( SP21_C ) | BLINK | BRIGHT
#endif

/*  define Special Effects 22 Attribute       */

#if SP22_C_SC == SC_NORM
#define     SP22_AT  SP22_C
#endif

#if SP22_C_SC == SC_BRIGHT
#define     SP22_AT  SP22_C | BRIGHT
#endif

#if SP22_C_SC == SC_BLINK
#define     SP22_AT  SP22_C | BLINK
#endif

#if SP22_C_SC == SC_BOTH
#define     SP22_AT  SP22_C | BLINK | BRIGHT
#endif

#if SP22_C_SC == SC_RV
#define     SP22_AT  REV_V( SP22_C )
#endif

#if SP22_C_SC == SC_RV_BRIGHT
#define     SP22_AT  REV_V( SP22_C ) | BRIGHT
#endif

#if SP22_C_SC == SC_RV_BLINK
#define     SP22_AT  REV_V( SP22_C ) | BLINK
#endif

#if SP22_C_SC == SC_RV_BOTH
#define     SP22_AT  REV_V( SP22_C ) | BLINK | BRIGHT
#endif

/*  define Special Effects 23 Attribute       */

#if SP23_C_SC == SC_NORM
#define     SP23_AT  SP23_C
#endif

#if SP23_C_SC == SC_BRIGHT
#define     SP23_AT  SP23_C | BRIGHT
#endif

#if SP23_C_SC == SC_BLINK
#define     SP23_AT  SP23_C | BLINK
#endif

#if SP23_C_SC == SC_BOTH
#define     SP23_AT  SP23_C | BLINK | BRIGHT
#endif

#if SP23_C_SC == SC_RV
#define     SP23_AT  REV_V( SP23_C )
#endif

#if SP23_C_SC == SC_RV_BRIGHT
#define     SP23_AT  REV_V( SP23_C ) | BRIGHT
#endif

#if SP23_C_SC == SC_RV_BLINK
#define     SP23_AT  REV_V( SP23_C ) | BLINK
#endif

#if SP23_C_SC == SC_RV_BOTH
#define     SP23_AT  REV_V( SP23_C ) | BLINK | BRIGHT
#endif

/*  define Special Effects 24 Attribute       */

#if SP24_C_SC == SC_NORM
#define     SP24_AT  SP24_C
#endif

#if SP24_C_SC == SC_BRIGHT
#define     SP24_AT  SP24_C | BRIGHT
#endif

#if SP24_C_SC == SC_BLINK
#define     SP24_AT  SP24_C | BLINK
#endif

#if SP24_C_SC == SC_BOTH
#define     SP24_AT  SP24_C | BLINK | BRIGHT
#endif

#if SP24_C_SC == SC_RV
#define     SP24_AT  REV_V( SP24_C )
#endif

#if SP24_C_SC == SC_RV_BRIGHT
#define     SP24_AT  REV_V( SP24_C ) | BRIGHT
#endif

#if SP24_C_SC == SC_RV_BLINK
#define     SP24_AT  REV_V( SP24_C ) | BLINK
#endif

#if SP24_C_SC == SC_RV_BOTH
#define     SP24_AT  REV_V( SP24_C ) | BLINK | BRIGHT
#endif

/*	Define the Monochrome Attributes     */

/*  define Default attribute		*/

#if DEF_M_SC == SC_NORM
#define     DEF_ATB IBM_DEF_ATTR
#endif

#if DEF_M_SC == SC_BRIGHT
#define     DEF_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if DEF_M_SC == SC_BLINK
#define     DEF_ATB IBM_DEF_ATTR | BLINK
#endif

#if DEF_M_SC == SC_BOTH
#define     DEF_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if DEF_M_SC == SC_RV
#define     DEF_ATB REV_V( IBM_DEF_ATTR )
#endif

#if DEF_M_SC == SC_RV_BRIGHT
#define     DEF_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if DEF_M_SC == SC_RV_BLINK
#define     DEF_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if DEF_M_SC == SC_RV_BOTH
#define     DEF_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Screen Title Attribute	*/

#if TIT_M_SC == SC_NORM
#define     TIT_ATB IBM_DEF_ATTR
#endif

#if TIT_M_SC == SC_BRIGHT
#define     TIT_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if TIT_M_SC == SC_BLINK
#define     TIT_ATB IBM_DEF_ATTR | BLINK
#endif

#if TIT_M_SC == SC_BOTH
#define     TIT_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if TIT_M_SC == SC_RV
#define     TIT_ATB REV_V( IBM_DEF_ATTR )
#endif

#if TIT_M_SC == SC_RV_BRIGHT
#define     TIT_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if TIT_M_SC == SC_RV_BLINK
#define     TIT_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if TIT_M_SC == SC_RV_BOTH
#define     TIT_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define background Attribute       */

#if BKG_M_SC == SC_NORM
#define     BKG_ATB IBM_DEF_ATTR
#endif

#if BKG_M_SC == SC_BRIGHT
#define     BKG_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if BKG_M_SC == SC_BLINK
#define     BKG_ATB IBM_DEF_ATTR | BLINK
#endif

#if BKG_M_SC == SC_BOTH
#define     BKG_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if BKG_M_SC == SC_RV
#define     BKG_ATB REV_V( IBM_DEF_ATTR )
#endif

#if BKG_M_SC == SC_RV_BRIGHT
#define     BKG_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if BKG_M_SC == SC_RV_BLINK
#define     BKG_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if BKG_M_SC == SC_RV_BOTH
#define     BKG_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define input Attribute	 */

#if INP_M_SC == SC_NORM
#define     INP_ATB IBM_DEF_ATTR
#endif

#if INP_M_SC == SC_BRIGHT
#define     INP_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if INP_M_SC == SC_BLINK
#define     INP_ATB IBM_DEF_ATTR | BLINK
#endif

#if INP_M_SC == SC_BOTH
#define     INP_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if INP_M_SC == SC_RV
#define     INP_ATB REV_V( IBM_DEF_ATTR )
#endif

#if INP_M_SC == SC_RV_BRIGHT
#define     INP_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if INP_M_SC == SC_RV_BLINK
#define     INP_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if INP_M_SC == SC_RV_BOTH
#define     INP_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define modifiable fields Attribute	     */

#if MOD_M_SC == SC_NORM
#define     MOD_ATB IBM_DEF_ATTR
#endif

#if MOD_M_SC == SC_BRIGHT
#define     MOD_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if MOD_M_SC == SC_BLINK
#define     MOD_ATB IBM_DEF_ATTR | BLINK
#endif

#if MOD_M_SC == SC_BOTH
#define     MOD_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if MOD_M_SC == SC_RV
#define     MOD_ATB REV_V( IBM_DEF_ATTR )
#endif

#if MOD_M_SC == SC_RV_BRIGHT
#define     MOD_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if MOD_M_SC == SC_RV_BLINK
#define     MOD_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if MOD_M_SC == SC_RV_BOTH
#define     MOD_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Error Messages Attribute	  */

#if ERR_M_SC == SC_NORM
#define     ERR_ATB IBM_DEF_ATTR
#endif

#if ERR_M_SC == SC_BRIGHT
#define     ERR_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if ERR_M_SC == SC_BLINK
#define     ERR_ATB IBM_DEF_ATTR | BLINK
#endif

#if ERR_M_SC == SC_BOTH
#define     ERR_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if ERR_M_SC == SC_RV
#define     ERR_ATB REV_V( IBM_DEF_ATTR )
#endif

#if ERR_M_SC == SC_RV_BRIGHT
#define     ERR_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if ERR_M_SC == SC_RV_BLINK
#define     ERR_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if ERR_M_SC == SC_RV_BOTH
#define     ERR_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Options Attribute	   */

#if OPT_M_SC == SC_NORM
#define     OPT_ATB IBM_DEF_ATTR
#endif

#if OPT_M_SC == SC_BRIGHT
#define     OPT_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if OPT_M_SC == SC_BLINK
#define     OPT_ATB IBM_DEF_ATTR | BLINK
#endif

#if OPT_M_SC == SC_BOTH
#define     OPT_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if OPT_M_SC == SC_RV
#define     OPT_ATB REV_V( IBM_DEF_ATTR )
#endif

#if OPT_M_SC == SC_RV_BRIGHT
#define     OPT_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if OPT_M_SC == SC_RV_BLINK
#define     OPT_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if OPT_M_SC == SC_RV_BOTH
#define     OPT_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Other Messages Attribute	  */

#if OTH_M_SC == SC_NORM
#define     OTH_ATB IBM_DEF_ATTR
#endif

#if OTH_M_SC == SC_BRIGHT
#define     OTH_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if OTH_M_SC == SC_BLINK
#define     OTH_ATB IBM_DEF_ATTR | BLINK
#endif

#if OTH_M_SC == SC_BOTH
#define     OTH_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if OTH_M_SC == SC_RV
#define     OTH_ATB REV_V( IBM_DEF_ATTR )
#endif

#if OTH_M_SC == SC_RV_BRIGHT
#define     OTH_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if OTH_M_SC == SC_RV_BLINK
#define     OTH_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if OTH_M_SC == SC_RV_BOTH
#define     OTH_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Special Effects 1 Attribute	     */

#if SP1_M_SC == SC_NORM
#define     SP1_ATB IBM_DEF_ATTR
#endif

#if SP1_M_SC == SC_BRIGHT
#define     SP1_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if SP1_M_SC == SC_BLINK
#define     SP1_ATB IBM_DEF_ATTR | BLINK
#endif

#if SP1_M_SC == SC_BOTH
#define     SP1_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if SP1_M_SC == SC_RV
#define     SP1_ATB REV_V( IBM_DEF_ATTR )
#endif

#if SP1_M_SC == SC_RV_BRIGHT
#define     SP1_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if SP1_M_SC == SC_RV_BLINK
#define     SP1_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if SP1_M_SC == SC_RV_BOTH
#define     SP1_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Special Effects 2 Attribute	     */

#if SP2_M_SC == SC_NORM
#define     SP2_ATB IBM_DEF_ATTR
#endif

#if SP2_M_SC == SC_BRIGHT
#define     SP2_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if SP2_M_SC == SC_BLINK
#define     SP2_ATB IBM_DEF_ATTR | BLINK
#endif

#if SP2_M_SC == SC_BOTH
#define     SP2_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if SP2_M_SC == SC_RV
#define     SP2_ATB REV_V( IBM_DEF_ATTR )
#endif

#if SP2_M_SC == SC_RV_BRIGHT
#define     SP2_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if SP2_M_SC == SC_RV_BLINK
#define     SP2_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if SP2_M_SC == SC_RV_BOTH
#define     SP2_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Special Effects 3 Attribute	     */

#if SP3_M_SC == SC_NORM
#define     SP3_ATB IBM_DEF_ATTR
#endif

#if SP3_M_SC == SC_BRIGHT
#define     SP3_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if SP3_M_SC == SC_BLINK
#define     SP3_ATB IBM_DEF_ATTR | BLINK
#endif

#if SP3_M_SC == SC_BOTH
#define     SP3_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if SP3_M_SC == SC_RV
#define     SP3_ATB REV_V( IBM_DEF_ATTR )
#endif

#if SP3_M_SC == SC_RV_BRIGHT
#define     SP3_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if SP3_M_SC == SC_RV_BLINK
#define     SP3_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if SP3_M_SC == SC_RV_BOTH
#define     SP3_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Special Effects 4 Attribute	     */

#if SP4_M_SC == SC_NORM
#define     SP4_ATB IBM_DEF_ATTR
#endif

#if SP4_M_SC == SC_BRIGHT
#define     SP4_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if SP4_M_SC == SC_BLINK
#define     SP4_ATB IBM_DEF_ATTR | BLINK
#endif

#if SP4_M_SC == SC_BOTH
#define     SP4_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if SP4_M_SC == SC_RV
#define     SP4_ATB REV_V( IBM_DEF_ATTR )
#endif

#if SP4_M_SC == SC_RV_BRIGHT
#define     SP4_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if SP4_M_SC == SC_RV_BLINK
#define     SP4_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if SP4_M_SC == SC_RV_BOTH
#define     SP4_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Special Effects 5 Attribute	     */

#if SP5_M_SC == SC_NORM
#define     SP5_ATB IBM_DEF_ATTR
#endif

#if SP5_M_SC == SC_BRIGHT
#define     SP5_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if SP5_M_SC == SC_BLINK
#define     SP5_ATB IBM_DEF_ATTR | BLINK
#endif

#if SP5_M_SC == SC_BOTH
#define     SP5_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if SP5_M_SC == SC_RV
#define     SP5_ATB REV_V( IBM_DEF_ATTR )
#endif

#if SP5_M_SC == SC_RV_BRIGHT
#define     SP5_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if SP5_M_SC == SC_RV_BLINK
#define     SP5_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if SP5_M_SC == SC_RV_BOTH
#define     SP5_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Special Effects 6 Attribute	     */

#if SP6_M_SC == SC_NORM
#define     SP6_ATB IBM_DEF_ATTR
#endif

#if SP6_M_SC == SC_BRIGHT
#define     SP6_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if SP6_M_SC == SC_BLINK
#define     SP6_ATB IBM_DEF_ATTR | BLINK
#endif

#if SP6_M_SC == SC_BOTH
#define     SP6_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if SP6_M_SC == SC_RV
#define     SP6_ATB REV_V( IBM_DEF_ATTR )
#endif

#if SP6_M_SC == SC_RV_BRIGHT
#define     SP6_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if SP6_M_SC == SC_RV_BLINK
#define     SP6_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if SP6_M_SC == SC_RV_BOTH
#define     SP6_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Special Effects 7 Attribute	     */

#if SP7_M_SC == SC_NORM
#define     SP7_ATB IBM_DEF_ATTR
#endif

#if SP7_M_SC == SC_BRIGHT
#define     SP7_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if SP7_M_SC == SC_BLINK
#define     SP7_ATB IBM_DEF_ATTR | BLINK
#endif

#if SP7_M_SC == SC_BOTH
#define     SP7_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if SP7_M_SC == SC_RV
#define     SP7_ATB REV_V( IBM_DEF_ATTR )
#endif

#if SP7_M_SC == SC_RV_BRIGHT
#define     SP7_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if SP7_M_SC == SC_RV_BLINK
#define     SP7_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if SP7_M_SC == SC_RV_BOTH
#define     SP7_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Special Effects 8 Attribute	     */

#if SP8_M_SC == SC_NORM
#define     SP8_ATB IBM_DEF_ATTR
#endif

#if SP8_M_SC == SC_BRIGHT
#define     SP8_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if SP8_M_SC == SC_BLINK
#define     SP8_ATB IBM_DEF_ATTR | BLINK
#endif

#if SP8_M_SC == SC_BOTH
#define     SP8_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if SP8_M_SC == SC_RV
#define     SP8_ATB REV_V( IBM_DEF_ATTR )
#endif

#if SP8_M_SC == SC_RV_BRIGHT
#define     SP8_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if SP8_M_SC == SC_RV_BLINK
#define     SP8_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if SP8_M_SC == SC_RV_BOTH
#define     SP8_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Special Effects 9 Attribute	     */

#if SP9_M_SC == SC_NORM
#define     SP9_ATB IBM_DEF_ATTR
#endif

#if SP9_M_SC == SC_BRIGHT
#define     SP9_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if SP9_M_SC == SC_BLINK
#define     SP9_ATB IBM_DEF_ATTR | BLINK
#endif

#if SP9_M_SC == SC_BOTH
#define     SP9_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if SP9_M_SC == SC_RV
#define     SP9_ATB REV_V( IBM_DEF_ATTR )
#endif

#if SP9_M_SC == SC_RV_BRIGHT
#define     SP9_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if SP9_M_SC == SC_RV_BLINK
#define     SP9_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if SP9_M_SC == SC_RV_BOTH
#define     SP9_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Special Effects 10 Attribute       */

#if SP10_M_SC == SC_NORM
#define     SP10_ATB IBM_DEF_ATTR
#endif

#if SP10_M_SC == SC_BRIGHT
#define     SP10_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if SP10_M_SC == SC_BLINK
#define     SP10_ATB IBM_DEF_ATTR | BLINK
#endif

#if SP10_M_SC == SC_BOTH
#define     SP10_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if SP10_M_SC == SC_RV
#define     SP10_ATB REV_V( IBM_DEF_ATTR )
#endif

#if SP10_M_SC == SC_RV_BRIGHT
#define     SP10_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if SP10_M_SC == SC_RV_BLINK
#define     SP10_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if SP10_M_SC == SC_RV_BOTH
#define     SP10_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Special Effects 11 Attribute       */

#if SP11_M_SC == SC_NORM
#define     SP11_ATB IBM_DEF_ATTR
#endif

#if SP11_M_SC == SC_BRIGHT
#define     SP11_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if SP11_M_SC == SC_BLINK
#define     SP11_ATB IBM_DEF_ATTR | BLINK
#endif

#if SP11_M_SC == SC_BOTH
#define     SP11_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if SP11_M_SC == SC_RV
#define     SP11_ATB REV_V( IBM_DEF_ATTR )
#endif

#if SP11_M_SC == SC_RV_BRIGHT
#define     SP11_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if SP11_M_SC == SC_RV_BLINK
#define     SP11_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if SP11_M_SC == SC_RV_BOTH
#define     SP11_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Special Effects 12 Attribute       */

#if SP12_M_SC == SC_NORM
#define     SP12_ATB IBM_DEF_ATTR
#endif

#if SP12_M_SC == SC_BRIGHT
#define     SP12_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if SP12_M_SC == SC_BLINK
#define     SP12_ATB IBM_DEF_ATTR | BLINK
#endif

#if SP12_M_SC == SC_BOTH
#define     SP12_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if SP12_M_SC == SC_RV
#define     SP12_ATB REV_V( IBM_DEF_ATTR )
#endif

#if SP12_M_SC == SC_RV_BRIGHT
#define     SP12_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if SP12_M_SC == SC_RV_BLINK
#define     SP12_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if SP12_M_SC == SC_RV_BOTH
#define     SP12_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Special Effects 13 Attribute       */

#if SP13_C_SC == SC_NORM
#define     SP13_ATB IBM_DEF_ATTR
#endif

#if SP13_C_SC == SC_BRIGHT
#define     SP13_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if SP13_C_SC == SC_BLINK
#define     SP13_ATB IBM_DEF_ATTR | BLINK
#endif

#if SP13_C_SC == SC_BOTH
#define     SP13_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if SP13_C_SC == SC_RV
#define     SP13_ATB REV_V( IBM_DEF_ATTR )
#endif

#if SP13_C_SC == SC_RV_BRIGHT
#define     SP13_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if SP13_C_SC == SC_RV_BLINK
#define     SP13_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if SP13_C_SC == SC_RV_BOTH
#define     SP13_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Special Effects 14 Attribute       */

#if SP14_C_SC == SC_NORM
#define     SP14_ATB IBM_DEF_ATTR
#endif

#if SP14_C_SC == SC_BRIGHT
#define     SP14_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if SP14_C_SC == SC_BLINK
#define     SP14_ATB IBM_DEF_ATTR | BLINK
#endif

#if SP14_C_SC == SC_BOTH
#define     SP14_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if SP14_C_SC == SC_RV
#define     SP14_ATB REV_V( IBM_DEF_ATTR )
#endif

#if SP14_C_SC == SC_RV_BRIGHT
#define     SP14_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if SP14_C_SC == SC_RV_BLINK
#define     SP14_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if SP14_C_SC == SC_RV_BOTH
#define     SP14_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Special Effects 15 Attribute       */

#if SP15_C_SC == SC_NORM
#define     SP15_ATB IBM_DEF_ATTR
#endif

#if SP15_C_SC == SC_BRIGHT
#define     SP15_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if SP15_C_SC == SC_BLINK
#define     SP15_ATB IBM_DEF_ATTR | BLINK
#endif

#if SP15_C_SC == SC_BOTH
#define     SP15_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if SP15_C_SC == SC_RV
#define     SP15_ATB REV_V( IBM_DEF_ATTR )
#endif

#if SP15_C_SC == SC_RV_BRIGHT
#define     SP15_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if SP15_C_SC == SC_RV_BLINK
#define     SP15_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if SP15_C_SC == SC_RV_BOTH
#define     SP15_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Special Effects 16 Attribute       */

#if SP16_C_SC == SC_NORM
#define     SP16_ATB IBM_DEF_ATTR
#endif

#if SP16_C_SC == SC_BRIGHT
#define     SP16_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if SP16_C_SC == SC_BLINK
#define     SP16_ATB IBM_DEF_ATTR | BLINK
#endif

#if SP16_C_SC == SC_BOTH
#define     SP16_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if SP16_C_SC == SC_RV
#define     SP16_ATB REV_V( IBM_DEF_ATTR )
#endif

#if SP16_C_SC == SC_RV_BRIGHT
#define     SP16_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if SP16_C_SC == SC_RV_BLINK
#define     SP16_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if SP16_C_SC == SC_RV_BOTH
#define     SP16_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Special Effects 17 Attribute       */

#if SP17_C_SC == SC_NORM
#define     SP17_ATB IBM_DEF_ATTR
#endif

#if SP17_C_SC == SC_BRIGHT
#define     SP17_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if SP17_C_SC == SC_BLINK
#define     SP17_ATB IBM_DEF_ATTR | BLINK
#endif

#if SP17_C_SC == SC_BOTH
#define     SP17_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if SP17_C_SC == SC_RV
#define     SP17_ATB REV_V( IBM_DEF_ATTR )
#endif

#if SP17_C_SC == SC_RV_BRIGHT
#define     SP17_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if SP17_C_SC == SC_RV_BLINK
#define     SP17_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if SP17_C_SC == SC_RV_BOTH
#define     SP17_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Special Effects 18 Attribute       */

#if SP18_C_SC == SC_NORM
#define     SP18_ATB IBM_DEF_ATTR
#endif

#if SP18_C_SC == SC_BRIGHT
#define     SP18_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if SP18_C_SC == SC_BLINK
#define     SP18_ATB IBM_DEF_ATTR | BLINK
#endif

#if SP18_C_SC == SC_BOTH
#define     SP18_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if SP18_C_SC == SC_RV
#define     SP18_ATB REV_V( IBM_DEF_ATTR )
#endif

#if SP18_C_SC == SC_RV_BRIGHT
#define     SP18_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if SP18_C_SC == SC_RV_BLINK
#define     SP18_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if SP18_C_SC == SC_RV_BOTH
#define     SP18_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Special Effects 19 Attribute       */

#if SP19_C_SC == SC_NORM
#define     SP19_ATB IBM_DEF_ATTR
#endif

#if SP19_C_SC == SC_BRIGHT
#define     SP19_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if SP19_C_SC == SC_BLINK
#define     SP19_ATB IBM_DEF_ATTR | BLINK
#endif

#if SP19_C_SC == SC_BOTH
#define     SP19_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if SP19_C_SC == SC_RV
#define     SP19_ATB REV_V( IBM_DEF_ATTR )
#endif

#if SP19_C_SC == SC_RV_BRIGHT
#define     SP19_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if SP19_C_SC == SC_RV_BLINK
#define     SP19_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if SP19_C_SC == SC_RV_BOTH
#define     SP19_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Special Effects 20 Attribute       */

#if SP20_C_SC == SC_NORM
#define     SP20_ATB IBM_DEF_ATTR
#endif

#if SP20_C_SC == SC_BRIGHT
#define     SP20_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if SP20_C_SC == SC_BLINK
#define     SP20_ATB IBM_DEF_ATTR | BLINK
#endif

#if SP20_C_SC == SC_BOTH
#define     SP20_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if SP20_C_SC == SC_RV
#define     SP20_ATB REV_V( IBM_DEF_ATTR )
#endif

#if SP20_C_SC == SC_RV_BRIGHT
#define     SP20_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if SP20_C_SC == SC_RV_BLINK
#define     SP20_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if SP20_C_SC == SC_RV_BOTH
#define     SP20_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Special Effects 21 Attribute       */

#if SP21_C_SC == SC_NORM
#define     SP21_ATB IBM_DEF_ATTR
#endif

#if SP21_C_SC == SC_BRIGHT
#define     SP21_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if SP21_C_SC == SC_BLINK
#define     SP21_ATB IBM_DEF_ATTR | BLINK
#endif

#if SP21_C_SC == SC_BOTH
#define     SP21_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if SP21_C_SC == SC_RV
#define     SP21_ATB REV_V( IBM_DEF_ATTR )
#endif

#if SP21_C_SC == SC_RV_BRIGHT
#define     SP21_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if SP21_C_SC == SC_RV_BLINK
#define     SP21_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if SP21_C_SC == SC_RV_BOTH
#define     SP21_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Special Effects 22 Attribute       */

#if SP22_C_SC == SC_NORM
#define     SP22_ATB IBM_DEF_ATTR
#endif

#if SP22_C_SC == SC_BRIGHT
#define     SP22_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if SP22_C_SC == SC_BLINK
#define     SP22_ATB IBM_DEF_ATTR | BLINK
#endif

#if SP22_C_SC == SC_BOTH
#define     SP22_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if SP22_C_SC == SC_RV
#define     SP22_ATB REV_V( IBM_DEF_ATTR )
#endif

#if SP22_C_SC == SC_RV_BRIGHT
#define     SP22_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if SP22_C_SC == SC_RV_BLINK
#define     SP22_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if SP22_C_SC == SC_RV_BOTH
#define     SP22_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Special Effects 23 Attribute       */

#if SP23_C_SC == SC_NORM
#define     SP23_ATB IBM_DEF_ATTR
#endif

#if SP23_C_SC == SC_BRIGHT
#define     SP23_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if SP23_C_SC == SC_BLINK
#define     SP23_ATB IBM_DEF_ATTR | BLINK
#endif

#if SP23_C_SC == SC_BOTH
#define     SP23_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if SP23_C_SC == SC_RV
#define     SP23_ATB REV_V( IBM_DEF_ATTR )
#endif

#if SP23_C_SC == SC_RV_BRIGHT
#define     SP23_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if SP23_C_SC == SC_RV_BLINK
#define     SP23_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if SP23_C_SC == SC_RV_BOTH
#define     SP23_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif

/*  define Special Effects 24 Attribute       */

#if SP24_C_SC == SC_NORM
#define     SP24_ATB IBM_DEF_ATTR
#endif

#if SP24_C_SC == SC_BRIGHT
#define     SP24_ATB IBM_DEF_ATTR | BRIGHT
#endif

#if SP24_C_SC == SC_BLINK
#define     SP24_ATB IBM_DEF_ATTR | BLINK
#endif

#if SP24_C_SC == SC_BOTH
#define     SP24_ATB IBM_DEF_ATTR | BLINK | BRIGHT
#endif

#if SP24_C_SC == SC_RV
#define     SP24_ATB REV_V( IBM_DEF_ATTR )
#endif

#if SP24_C_SC == SC_RV_BRIGHT
#define     SP24_ATB REV_V( IBM_DEF_ATTR ) | BRIGHT
#endif

#if SP24_C_SC == SC_RV_BLINK
#define     SP24_ATB REV_V( IBM_DEF_ATTR ) | BLINK
#endif

#if SP24_C_SC == SC_RV_BOTH
#define     SP24_ATB REV_V( IBM_DEF_ATTR ) | BLINK | BRIGHT
#endif
                                                                                                                                                                                                                                                                                                                                                                                                                                      