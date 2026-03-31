// Function: mem_copy
// Address: 0x18514b0


/* WARNING: Control flow encountered bad instruction data */

undefined8 * FUN_018514b0(undefined8 *param_1,ulong param_2,undefined8 *param_3,ulong param_4)

{
  undefined1 uVar1;
  undefined8 *puVar2;
  ulong uVar3;
  undefined8 *puVar4;
  undefined8 *puVar5;
  
  if (param_1 == param_3) {
    return param_1;
  }
  if (param_2 == 0) {
    return param_1;
  }
  if (((param_1 == (undefined8 *)0x0) || (param_3 == (undefined8 *)0x0)) || (param_2 < param_4)) {
    return (undefined8 *)0x0;
  }
  if (param_1 < param_3) {
    if (param_3 < (undefined8 *)(param_2 + (long)param_1)) goto code_r0x01851524;
  }
  else if (param_1 < (undefined8 *)((long)param_3 + param_4)) goto code_r0x01851524;
  uVar3 = ((ulong)param_1 | (ulong)param_3 | param_4) & 7;
  puVar2 = param_1;
  if (param_4 < 0x8001) {
    if (uVar3 == 0) {
      puVar5 = param_3;
      if (param_4 == 0) {
        return param_1;
      }
code_r0x018514fc:
      do {
        puVar4 = puVar5 + 1;
        *puVar2 = *puVar5;
        puVar2 = puVar2 + 1;
        puVar5 = puVar4;
      } while ((undefined8 *)((long)puVar4 - param_4) != param_3);
      return param_1;
    }
    if (param_4 < 0x20) {
      if (param_4 == 0) {
        return param_1;
      }
      do {
        uVar1 = *(undefined1 *)param_3;
        puVar5 = (undefined8 *)((long)puVar2 + 1);
        param_3 = (undefined8 *)((long)param_3 + 1);
        *(undefined1 *)puVar2 = uVar1;
        puVar2 = puVar5;
      } while ((undefined8 *)(param_4 + (long)param_1) != puVar5);
      return param_1;
    }
  }
  else if (cRam00000000040b7171 == '\0') {
    puVar5 = param_3;
    if (uVar3 == 0) goto code_r0x018514fc;
  }
  else if (uVar3 == 0) {
    fence();
    if (cRam00000000040ef4e0 == '\0') {
                    /* WARNING: Bad instruction - Truncating control flow here */
      halt_baddata();
    }
                    /* WARNING: Bad instruction - Truncating control flow here */
    halt_baddata();
  }
code_r0x01851524:
  puVar2 = (undefined8 *)(*(code *)&UNK_01a839b8)(param_1,param_3,param_4);
  return puVar2;
}

