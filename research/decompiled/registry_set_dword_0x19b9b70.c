// Function: registry_set_dword
// Address: 0x19b9b70
// Size: 1 bytes


/* WARNING: Type propagation algorithm not settling */

long FUN_019b9b70(long param_1,undefined4 param_2,ulong param_3)

{
  long lVar1;
  uint uVar2;
  int iVar3;
  int iVar4;
  ulong uVar5;
  long lVar6;
  undefined4 *puVar7;
  long lVar8;
  long extraout_a1;
  ulong uVar9;
  long lVar10;
  ulong unaff_s4;
  ulong uVar11;
  long lStack_140;
  ulong auStack_138 [4];
  long alStack_a8 [4];
  long alStack_48 [4];
  
  alStack_48[2] = lRam00000000040b6a20;
  if (param_1 == 0) {
    lVar1 = 0x1f;
  }
  else {
    alStack_48[0] = FUN_019b9aec(1,0);
    if (alStack_48[0] == 0) {
      iVar3 = (*(code *)&UNK_019ac184)(alStack_48,param_1);
      lVar1 = (long)iVar3;
      if (lVar1 != 0) {
        alStack_48[1] = 0x2030e0b8;
        (*(code *)&UNK_019e6ea4)(1,alStack_48 + 1);
        goto code_r0x019b9bac;
      }
      *(undefined1 *)(alStack_48[0] + 0x18) = 1;
      *(undefined4 *)(alStack_48[0] + 0x10) = param_2;
      *(undefined4 *)(alStack_48[0] + 0x14) = 4;
    }
    else {
      *(undefined4 *)(alStack_48[0] + 0x10) = param_2;
    }
    lVar1 = 0;
  }
code_r0x019b9bac:
  if (lRam00000000040b6a20 == alStack_48[2]) {
    return lVar1;
  }
  uVar5 = (*(code *)&UNK_019e6a1e)(0);
  alStack_a8[2] = lRam00000000040b6a20;
  if ((uVar5 == 0) || (extraout_a1 == 0)) {
    lVar1 = 0x1f;
  }
  else {
    lVar6 = FUN_019b9aec(2,0);
    alStack_a8[0] = lVar6;
    if (lVar6 == 0) {
      iVar3 = (*(code *)&UNK_019ac184)(alStack_a8,uVar5);
      lVar1 = (long)iVar3;
      lVar6 = alStack_a8[0];
      if (lVar1 != 0) {
        alStack_a8[1] = 0x2030e0d0;
        (*(code *)&UNK_019e6ea4)(1,alStack_a8 + 1);
        unaff_s4 = uVar5;
        goto code_r0x019b9cb0;
      }
    }
    else if (*(long *)(lVar6 + 8) != 0) {
      (*(code *)&UNK_01854d0c)(0x40b77b0);
      *(undefined8 *)(lVar6 + 8) = 0;
      *(undefined4 *)(lVar6 + 0x14) = 0;
    }
    unaff_s4 = param_3 & 0xffffffff;
    lVar1 = (*(code *)&UNK_018543c4)(0x40b77d8,unaff_s4);
    *(long *)(lVar6 + 8) = lVar1;
    if (lVar1 == 0) {
      alStack_a8[1] = 0x2030e0e8;
      lVar1 = 0x51;
      (*(code *)&UNK_019e6ea4)(1,alStack_a8 + 1);
    }
    else {
      *(undefined1 *)(lVar6 + 0x18) = 2;
      *(int *)(lVar6 + 0x14) = (int)param_3;
      (*(code *)&UNK_018514b0)(unaff_s4,extraout_a1,unaff_s4);
      lVar1 = 0;
    }
  }
code_r0x019b9cb0:
  if (lRam00000000040b6a20 == alStack_a8[2]) {
    return lVar1;
  }
  puVar7 = (undefined4 *)(*(code *)&UNK_019e6a1e)(0);
  auStack_138[2] = lRam00000000040b6a20;
  if (*(uint *)(uRam00000000040b7720 + 8) < 0x28) {
    lVar1 = -0xeffffe;
    lVar6 = lVar1;
    goto code_r0x019b9e1c;
  }
  iVar3 = *(int *)(uRam00000000040b7720 + 0x20) + 0x20;
  if ((ulong)(long)iRam00000000040b7748 < (ulong)(long)iVar3) {
    unaff_s4 = (*(code *)&UNK_018543c4)(0x40b77d8,iVar3);
    if (unaff_s4 == 0) {
      auStack_138[0] = 0x2030e100;
      lVar1 = 0x51;
      (*(code *)&UNK_019e6ea4)(1,auStack_138);
      lVar6 = 0x51;
      goto code_r0x019b9e1c;
    }
    uVar2 = (*(code *)&UNK_019ad164)((long)iVar3,unaff_s4);
    lVar6 = (long)(int)uVar2;
    uVar5 = unaff_s4;
    if (lVar6 != 0) {
      auStack_138[0] = (ulong)uVar2;
      auStack_138[1] = 0x2030e118;
      lVar1 = (long)(int)uVar2;
      (*(code *)&UNK_019e6ea4)(2,auStack_138);
      goto code_r0x019b9e0a;
    }
  }
  else {
    unaff_s4 = 0;
    uVar5 = uRam00000000040b7720;
  }
  lVar1 = uVar5 + 0x20;
  uRam00000000040ef554 = 1;
  if (*(int *)(uVar5 + 0x24) == 0) {
code_r0x019b9f98:
    auStack_138[0] = 0x2030e130;
    (*(code *)&UNK_019e6ea4)(1,auStack_138);
    lVar1 = 0;
    lVar6 = 0;
  }
  else {
    uVar11 = 0;
    do {
      lVar6 = ((uVar11 << 0x20) >> 0x1c) + lVar1;
      uVar9 = (ulong)*(byte *)(lVar6 + 0xc);
      if (uVar9 == 2) {
        iVar3 = (*(code *)&UNK_019b9c1c)
                          ((ulong)*(uint *)(lVar6 + 8) + lVar1,
                           (ulong)*(uint *)(lVar6 + 0x10) + lVar1,(long)*(int *)(lVar6 + 0x14));
code_r0x019b9ec0:
        lVar6 = (long)iVar3;
        if (lVar6 != 0) {
          if (lVar6 != 0x10006) goto code_r0x019ba058;
          goto code_r0x019b9f98;
        }
      }
      else {
        if (uVar9 != 3) {
          if (uVar9 != 1) {
            auStack_138[1] = 0x2030e178;
            auStack_138[0] = uVar9;
            (*(code *)&UNK_019e6ea4)(2);
            lVar1 = 0x40;
            lVar6 = 0x40;
            goto code_r0x019b9df0;
          }
          iVar3 = FUN_019b9b70((ulong)*(uint *)(lVar6 + 8) + lVar1,(long)*(int *)(lVar6 + 0x10));
          goto code_r0x019b9ec0;
        }
        uVar2 = *(uint *)(lVar6 + 0x10);
        lVar10 = (ulong)*(uint *)(lVar6 + 8) + lVar1;
        iVar3 = *(int *)(lVar6 + 0x14);
        lVar8 = FUN_019b9aec(lVar10,3);
        lStack_140 = lVar8;
        if (lVar8 == 0) {
          iVar4 = (*(code *)&UNK_019ac184)(&lStack_140,lVar10);
          lVar6 = (long)iVar4;
          lVar8 = lStack_140;
          if (lVar6 != 0) {
            auStack_138[0] = 0x2030e148;
            (*(code *)&UNK_019e6ea4)(1);
            lVar1 = (long)iVar4;
            if (lVar6 != 0x10006) goto code_r0x019b9df0;
            goto code_r0x019b9f98;
          }
        }
        else if (*(long *)(lVar8 + 8) != 0) {
          (*(code *)&UNK_01854d0c)(0x40b77b0);
          *(undefined4 *)(lVar8 + 0x14) = 0;
          *(undefined8 *)(lVar8 + 8) = 0;
        }
        lVar6 = (*(code *)&UNK_018543c4)(0x40b77d8);
        *(long *)(lVar8 + 8) = lVar6;
        if (lVar6 == 0) {
          auStack_138[0] = 0x2030e160;
          (*(code *)&UNK_019e6ea4)(1);
          lVar1 = 0x51;
          lVar6 = 0x51;
          goto code_r0x019b9df0;
        }
        *(undefined1 *)(lVar8 + 0x18) = 3;
        *(int *)(lVar8 + 0x14) = iVar3;
        (*(code *)&UNK_018514b0)(iVar3,(ulong)uVar2 + lVar1,(ulong)(iVar3 - 1));
        *(undefined1 *)(*(long *)(lVar8 + 8) + (ulong)(iVar3 - 1)) = 0;
      }
      uVar11 = (ulong)((int)uVar11 + 1);
    } while (uVar11 < (ulong)(long)*(int *)(uVar5 + 0x24));
    lVar1 = 0;
    lVar6 = 0;
  }
  while( true ) {
    if (unaff_s4 != 0) {
code_r0x019b9e0a:
      (*(code *)&UNK_01854d0c)(0x40b77b0,unaff_s4);
    }
code_r0x019b9e1c:
    *puVar7 = (int)lVar6;
    if (lRam00000000040b6a20 == auStack_138[2]) break;
    (*(code *)&UNK_019e6a1e)(0);
code_r0x019ba058:
    lVar1 = (long)(int)lVar6;
code_r0x019b9df0:
    auStack_138[0] = 0x2030e190;
    (*(code *)&UNK_019e6ea4)(1,auStack_138);
  }
  return lVar1;
}

