// Function: mem_free
// Address: 0x1854d0c


void FUN_01854d0c(long param_1,long param_2)

{
  uint uVar1;
  undefined *unaff_retaddr;
  undefined8 unaff_s0;
  long unaff_s1;
  long lVar2;
  long lVar3;
  ulong uVar4;
  long unaff_s2;
  long unaff_s3;
  undefined8 unaff_s4;
  ulong unaff_s5;
  
  do {
    lVar2 = param_2;
    *(undefined8 *)((long)register0x00002010 + -0x10) = unaff_s0;
    *(long *)((long)register0x00002010 + -0x18) = unaff_s1;
    *(long *)((long)register0x00002010 + -0x20) = unaff_s2;
    *(undefined8 *)((long)register0x00002010 + -0x30) = unaff_s4;
    *(undefined **)((long)register0x00002010 + -8) = unaff_retaddr;
    *(long *)((long)register0x00002010 + -0x28) = unaff_s3;
    *(ulong *)((long)register0x00002010 + -0x38) = unaff_s5;
    lVar3 = *(long *)(param_1 + 0x18);
    unaff_s4 = 0x40b6a20;
    *(long *)((long)register0x00002010 + -0x48) = lRam00000000040b6a20;
    if (lVar3 != 0) {
      unaff_s5 = *(ulong *)(lVar2 + -0x10);
      unaff_s3 = 0x40b7750;
      *(int *)(lVar3 + 0x18) = *(int *)(lVar3 + 0x18) + -1;
      *(ulong *)(lVar3 + 0x28) = *(long *)(lVar3 + 0x28) - unaff_s5;
      iRam00000000040b7768 = iRam00000000040b7768 + -1;
      lRam00000000040b7778 = lRam00000000040b7778 - unaff_s5;
      if (cRam00000000040b78b8 != '\0') {
        uVar1 = *(int *)(lVar2 + -8) - 1;
        if (0x3f < uVar1) goto code_r0x01854dce;
        lVar3 = *(long *)(((ulong)((long)(int)uVar1 << 0x20) >> 0x1d) + 0x40b78c0);
        if (*(ulong *)(lVar3 + 0x48) < unaff_s5) {
          *(undefined8 *)((long)register0x00002010 + -0x50) = 0x20303db0;
          (*(code *)&UNK_019e6ea4)(1,(undefined1 *)((long)register0x00002010 + -0x50));
        }
        else {
          *(ulong *)(lVar3 + 0x48) = *(long *)(lVar3 + 0x48) - unaff_s5;
        }
      }
      uVar1 = *(int *)(lVar2 + -8) - 1;
      if (uVar1 < 0x40) {
        uVar4 = (ulong)((long)(int)uVar1 << 0x20) >> 0x1d;
        unaff_s3 = uVar4 + 0x40b7750;
        lVar3 = *(long *)(uVar4 + 0x40b78c0);
        *(int *)(lVar3 + 0x18) = *(int *)(lVar3 + 0x18) + -1;
        *(ulong *)(lVar3 + 0x28) = *(long *)(lVar3 + 0x28) - unaff_s5;
      }
    }
code_r0x01854dce:
    if (lRam00000000040b6a20 == *(long *)((long)register0x00002010 + -0x48)) {
                    /* WARNING: Could not recover jumptable at 0x01854df4. Too many branches */
                    /* WARNING: Treating indirect jump as call */
      (**(code **)(param_1 + 8))(param_1,lVar2 + -0x10,*(code **)(param_1 + 8));
      return;
    }
    unaff_retaddr = &UNK_01854e1a;
    param_2 = (*(code *)&UNK_019e6a1e)(0);
    *(BADSPACEBASE **)((long)register0x00002010 + -0x58) = register0x00002010;
    if (param_2 == 0) {
      return;
    }
    unaff_s0 = *(undefined8 *)((long)register0x00002010 + -0x58);
    register0x00002010 = (BADSPACEBASE *)((long)register0x00002010 + -0x50);
    unaff_s1 = param_1;
    param_1 = 0x40b77b0;
    unaff_s2 = lVar2;
  } while( true );
}

