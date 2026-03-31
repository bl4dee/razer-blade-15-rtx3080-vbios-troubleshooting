// Function: mem_alloc
// Address: 0x18543c4


void FUN_018543c4(undefined8 *param_1,ulong param_2)

{
  int iVar1;
  undefined *unaff_retaddr;
  undefined8 unaff_s0;
  undefined8 unaff_s1;
  uint uVar2;
  ulong *puVar3;
  long *plVar4;
  ulong uVar5;
  ulong uVar6;
  long lVar7;
  long *plVar8;
  ulong unaff_s2;
  undefined8 *unaff_s3;
  ulong unaff_s4;
  undefined8 unaff_s5;
  
  do {
    *(undefined8 *)((long)register0x00002010 + -0x10) = unaff_s0;
    *(undefined8 *)((long)register0x00002010 + -0x38) = unaff_s5;
    *(undefined **)((long)register0x00002010 + -8) = unaff_retaddr;
    *(undefined8 *)((long)register0x00002010 + -0x18) = unaff_s1;
    *(ulong *)((long)register0x00002010 + -0x20) = unaff_s2;
    *(undefined8 **)((long)register0x00002010 + -0x28) = unaff_s3;
    *(ulong *)((long)register0x00002010 + -0x30) = unaff_s4;
    unaff_s5 = 0x40b6a20;
    *(long *)((long)register0x00002010 + -0x48) = lRam00000000040b6a20;
    *(undefined4 *)((long)register0x00002010 + -100) = 0;
    if (param_1 == (undefined8 *)0x0) {
code_r0x018544ac:
      puVar3 = (ulong *)0x0;
    }
    else {
      unaff_s1 = 0x40b7750;
      unaff_s2 = param_2;
      unaff_s3 = param_1;
      if (((cRam00000000040b78b8 == '\0') || (lRam00000000040ef4f8 == 0)) ||
         (lVar7 = *(long *)(lRam00000000040ef4f8 + 0x1a0), lVar7 == 0)) {
code_r0x018544b0:
        unaff_s4 = 0;
      }
      else {
        unaff_s4 = (ulong)*(int *)(lVar7 + 0x3c1a0);
        if (unaff_s4 != 0) {
          plVar8 = (long *)(lVar7 + 0x3bfa0);
          plVar4 = (long *)(((unaff_s4 << 0x20) >> 0x1c) + (long)plVar8);
          do {
            if (((int)plVar8[1] == 0) && (*plVar8 != 0)) {
              uVar2 = (*(code *)&UNK_010647c0)((undefined1 *)((long)register0x00002010 + -100));
              if (uVar2 != 0) {
                *(ulong *)((long)register0x00002010 + -0x60) = (ulong)uVar2;
                *(undefined8 *)((long)register0x00002010 + -0x58) = 0x20303cd8;
                (*(code *)&UNK_019e6ea4)(2,(undefined1 *)((long)register0x00002010 + -0x60));
                puVar3 = (ulong *)0x0;
                goto code_r0x018545d6;
              }
              uVar2 = *(uint *)((long)register0x00002010 + -100);
              unaff_s4 = (ulong)(int)uVar2;
              if (((cRam00000000040b78b8 == '\0') || (0x3f < uVar2 - 1)) ||
                 (lVar7 = *(long *)(((ulong)((long)(int)(uVar2 - 1) << 0x20) >> 0x1d) + 0x40b78c0),
                 uVar5 = *(ulong *)(lVar7 + 0x40), *(long *)(lVar7 + 0x48) + param_2 <= uVar5))
              goto code_r0x018544b2;
              unaff_s4 = (ulong)uVar2;
              *(ulong *)((long)register0x00002010 + -0x60) = unaff_s4;
              *(ulong *)((long)register0x00002010 + -0x58) = uVar5;
              *(undefined8 *)((long)register0x00002010 + -0x50) = 0x20303cf0;
              (*(code *)&UNK_019e6ea4)(3,(undefined1 *)((long)register0x00002010 + -0x60));
              goto code_r0x018544ac;
            }
            plVar8 = plVar8 + 2;
          } while (plVar8 != plVar4);
          goto code_r0x018544b0;
        }
      }
code_r0x018544b2:
      if (((param_2 == 0) ||
          ((((param_2 & 7) != 0 &&
            (unaff_s2 = (param_2 & 0xfffffffffffffff8) + 8,
            unaff_s2 < (param_2 & 0xfffffffffffffff8))) || (unaff_s2 + 0x10 < unaff_s2)))) ||
         (puVar3 = (ulong *)(*(code *)*param_1)(param_1,(code *)*param_1), puVar3 == (ulong *)0x0))
      goto code_r0x018544ac;
      lVar7 = param_1[3];
      if (lVar7 != 0) {
        *puVar3 = unaff_s2;
        iVar1 = *(int *)(lVar7 + 0x18) + 1;
        *(int *)(lVar7 + 0x18) = iVar1;
        *(int *)(lVar7 + 0x1c) = *(int *)(lVar7 + 0x1c) + 1;
        uVar5 = *(long *)(lVar7 + 0x28) + unaff_s2;
        *(ulong *)(lVar7 + 0x28) = uVar5;
        *(ulong *)(lVar7 + 0x30) = *(long *)(lVar7 + 0x30) + unaff_s2;
        while (uVar6 = *(ulong *)(lVar7 + 0x38), uVar6 < uVar5) {
          while (*(ulong *)(lVar7 + 0x38) == uVar6) {
            *(ulong *)(lVar7 + 0x38) = uVar5;
            uVar6 = *(ulong *)(lVar7 + 0x38);
            if (uVar5 <= uVar6) goto code_r0x01854510;
          }
        }
code_r0x01854510:
        do {
          if (uVar5 != *(ulong *)(lVar7 + 0x38)) goto code_r0x01854522;
        } while (*(int *)(lVar7 + 0x20) != *(int *)(lVar7 + 0x20));
        *(int *)(lVar7 + 0x20) = iVar1;
code_r0x01854522:
        iRam00000000040b7768 = iRam00000000040b7768 + 1;
        iRam00000000040b776c = iRam00000000040b776c + 1;
        uRam00000000040b7778 = uRam00000000040b7778 + unaff_s2;
        lRam00000000040b7780 = lRam00000000040b7780 + unaff_s2;
        if (uRam00000000040b7788 < uRam00000000040b7778) {
          uRam00000000040b7788 = uRam00000000040b7778;
        }
        if (uRam00000000040b7778 == uRam00000000040b7788) {
          iRam00000000040b7770 = iRam00000000040b7768;
        }
        *(int *)(puVar3 + 1) = (int)unaff_s4;
        uVar2 = (int)unaff_s4 - 1;
        unaff_s4 = (ulong)(int)uVar2;
        if (cRam00000000040b78b8 == '\0') {
          if (uVar2 < 0x40) goto code_r0x0185458e;
        }
        else if (uVar2 < 0x40) {
          lVar7 = *(long *)(((ulong)uVar2 + 0x2e) * 8 + 0x40b7750);
          *(ulong *)(lVar7 + 0x48) = *(long *)(lVar7 + 0x48) + unaff_s2;
code_r0x0185458e:
          unaff_s4 = (ulong)uVar2 + 0x2e;
          lVar7 = *(long *)(unaff_s4 * 8 + 0x40b7750);
          iVar1 = *(int *)(lVar7 + 0x18) + 1;
          *(int *)(lVar7 + 0x18) = iVar1;
          *(int *)(lVar7 + 0x1c) = *(int *)(lVar7 + 0x1c) + 1;
          uVar5 = *(long *)(lVar7 + 0x28) + unaff_s2;
          *(ulong *)(lVar7 + 0x28) = uVar5;
          *(ulong *)(lVar7 + 0x30) = *(long *)(lVar7 + 0x30) + unaff_s2;
          while (*(ulong *)(lVar7 + 0x38) < uVar5) {
            if (*(ulong *)(lVar7 + 0x38) == *(ulong *)(lVar7 + 0x38)) {
              *(ulong *)(lVar7 + 0x38) = uVar5;
            }
          }
          do {
            if (uVar5 != *(ulong *)(lVar7 + 0x38)) goto code_r0x018545d4;
          } while (*(int *)(lVar7 + 0x20) != *(int *)(lVar7 + 0x20));
          *(int *)(lVar7 + 0x20) = iVar1;
        }
      }
code_r0x018545d4:
      puVar3 = puVar3 + 2;
    }
code_r0x018545d6:
    if (lRam00000000040b6a20 == *(long *)((long)register0x00002010 + -0x48)) {
      return;
    }
    unaff_retaddr = &UNK_01854636;
    param_2 = (*(code *)&UNK_019e6a1e)(puVar3,0);
    *(BADSPACEBASE **)((long)register0x00002010 + -0x78) = register0x00002010;
    unaff_s0 = *(undefined8 *)((long)register0x00002010 + -0x78);
    param_1 = (undefined8 *)0x40b77d8;
    register0x00002010 = (BADSPACEBASE *)((long)register0x00002010 + -0x70);
  } while( true );
}

