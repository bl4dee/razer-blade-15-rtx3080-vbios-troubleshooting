// Function: registry_lookup
// Address: 0x19b9aec
// Size: 1 bytes


long * FUN_019b9aec(char *param_1,ulong param_2)

{
  char cVar1;
  char *pcVar2;
  char cVar3;
  char *pcVar4;
  long *plVar5;
  
  plVar5 = plRam00000000040ef620;
  if (plRam00000000040ef620 != (long *)0x0) {
    do {
      while (*(byte *)(plVar5 + 3) != param_2) {
code_r0x019b9b02:
        plVar5 = (long *)*plVar5;
        if (plVar5 == (long *)0x0) {
          return (long *)0x0;
        }
      }
      pcVar2 = (char *)((long)plVar5 + 0x19);
      pcVar4 = param_1;
      do {
        while( true ) {
          cVar3 = *pcVar2;
          cVar1 = *pcVar4;
          if ((byte)(cVar3 + 0xbfU) < 0x1a) {
            cVar3 = cVar3 + ' ';
          }
          pcVar2 = pcVar2 + 1;
          pcVar4 = pcVar4 + 1;
          if ((byte)(cVar1 + 0xbfU) < 0x1a) break;
          if (cVar1 != cVar3) goto code_r0x019b9b02;
          if (cVar1 == '\0') {
            return plVar5;
          }
        }
      } while ((char)(cVar1 + ' ') == cVar3);
      plVar5 = (long *)*plVar5;
    } while (plVar5 != (long *)0x0);
  }
  return plVar5;
}

