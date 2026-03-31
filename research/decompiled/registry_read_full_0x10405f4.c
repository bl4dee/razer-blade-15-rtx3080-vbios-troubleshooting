// Function: registry_read_full
// Address: 0x10405f4


void FUN_010405f4(uint *param_1,uint *param_2,uint *param_3,uint *param_4)

{
  byte bVar1;
  undefined8 *puVar2;
  uint *unaff_retaddr;
  uint *puVar3;
  uint *puVar4;
  undefined *puVar5;
  undefined *puVar6;
  undefined1 *puVar7;
  uint *unaff_s1;
  int iVar8;
  uint uVar9;
  long lVar10;
  uint *puVar11;
  long lVar12;
  uint *extraout_a1;
  uint *extraout_a1_00;
  long extraout_a1_01;
  uint *puVar13;
  uint *puVar14;
  uint *puVar15;
  uint *unaff_s2;
  uint *unaff_s3;
  long lVar16;
  undefined8 uVar17;
  long lVar18;
  uint *unaff_s6;
  undefined8 unaff_s7;
  undefined8 unaff_s8;
  undefined8 unaff_s9;
  undefined1 auStack_80 [8];
  uint *puStack_78;
  uint uStack_6c;
  undefined4 uStack_68;
  int iStack_64;
  undefined8 uStack_60;
  undefined8 auStack_58 [2];
  long lStack_48;
  
  puVar7 = auStack_80;
  uVar17 = 0x40b6a20;
  lStack_48 = lRam00000000040b6a20;
  if (param_2 == (uint *)0x0) {
    auStack_58[0] = 0x201f85e0;
code_r0x0104079a:
    (*(code *)&UNK_019e6ea4)(1,auStack_58);
    (*(code *)&UNK_01a84340)(0);
    lVar10 = lRam00000000040b6fa0;
    puVar13 = param_3;
    if (cRam00000000040ef504 != '\0') {
      *(uint *)(lRam00000000040b6fa0 + 0x11152c) =
           *(uint *)(lRam00000000040b6fa0 + 0x11152c) | 0x400000;
      param_4 = (uint *)(lVar10 + 0x111520);
      puVar13 = (uint *)0x400000;
      *param_4 = 0x400000;
      *(undefined4 *)(lVar10 + 0x1113d0) = 0;
    }
    ebreak();
    lVar10 = 0x1f;
  }
  else {
    unaff_s2 = param_3;
    if (param_3 == (uint *)0x0) {
      auStack_58[0] = 0x201f85f8;
      goto code_r0x0104079a;
    }
    unaff_s1 = param_2;
    puVar13 = param_3;
    unaff_s3 = param_1;
    if (cRam00000000040ef554 == '\0') {
      auStack_58[0] = 0x201f8610;
      (*(code *)&UNK_019e6ea4)(1,auStack_58);
      (*(code *)&UNK_01a84340)(0);
      lVar10 = lRam00000000040b6fa0;
      if (cRam00000000040ef504 == '\0') {
        ebreak();
      }
      else {
        *(uint *)(lRam00000000040b6fa0 + 0x11152c) =
             *(uint *)(lRam00000000040b6fa0 + 0x11152c) | 0x400000;
        param_4 = (uint *)(lVar10 + 0x111520);
        puVar13 = (uint *)0x400000;
        *param_4 = 0x400000;
        *(undefined4 *)(lVar10 + 0x1113d0) = 0;
        ebreak();
      }
      lVar10 = FUN_019b9aec(param_2,1);
      if (lVar10 != 0) goto code_r0x01040640;
code_r0x010406aa:
      lVar10 = FUN_019b9aec(param_2,2);
      if ((lVar10 != 0) && (3 < *(uint *)(lVar10 + 0x14))) {
        uVar9 = **(uint **)(lVar10 + 8);
        goto code_r0x01040642;
      }
      if (param_1 == (uint *)0x0) {
        lVar10 = 0x31;
      }
      else if (*(char *)((long)param_1 + 0x533) == '\0') {
        unaff_retaddr = (uint *)(ulong)*(ushort *)(*(long *)(lRam00000000040ef4f8 + 0x1d0) + 0x68);
        puStack_78 = (uint *)(ulong)*(byte *)(*(long *)(lRam00000000040ef4f8 + 0x1d0) + 0x58);
        puVar13 = param_2;
        if ((char)*param_2 == '\0') {
          uVar9 = 0;
        }
        else {
          do {
            puVar3 = puVar13;
            puVar13 = (uint *)((long)puVar3 + 1);
          } while (*(char *)((long)puVar3 + 1) != '\0');
          uVar9 = ((int)puVar3 - (int)param_2) + 1U & 0xffff;
        }
        (*(code *)&UNK_0104035c)(param_2,uVar9,auStack_58);
        uStack_68 = 4;
        puVar13 = unaff_retaddr;
        param_4 = puStack_78;
        iVar8 = (*(code *)&UNK_0103fab8)(param_1,1,auStack_58,&uStack_6c,&uStack_68,&iStack_64);
        lVar10 = (long)iVar8;
        if (lVar10 == 0) {
          if (iStack_64 == 0) {
            *param_3 = uStack_6c;
            lVar10 = 0;
          }
          else {
            if (iStack_64 == -2) {
              uStack_60 = 0x201f8658;
              (*(code *)&UNK_019e6ea4)(1,&uStack_60);
              (*(code *)&UNK_01851240)();
              (*(code *)&UNK_019b85f8)();
            }
            lVar10 = 0xffff;
          }
        }
      }
      else {
        auStack_58[0] = 0x201f8628;
        (*(code *)&UNK_019e6ea4)(1,auStack_58);
        auStack_58[0] = 0x201f8640;
        (*(code *)&UNK_019e6ea4)(1,auStack_58);
        (*(code *)&UNK_01a84340)(0);
        lVar10 = lRam00000000040b6fa0;
        if (cRam00000000040ef504 != '\0') {
          *(uint *)(lRam00000000040b6fa0 + 0x11152c) =
               *(uint *)(lRam00000000040b6fa0 + 0x11152c) | 0x400000;
          param_4 = (uint *)(lVar10 + 0x111520);
          puVar13 = (uint *)0x400000;
          *param_4 = 0x400000;
          *(undefined4 *)(lVar10 + 0x1113d0) = 0;
        }
        ebreak();
        lVar10 = 0x3f;
      }
    }
    else {
      lVar10 = FUN_019b9aec(param_2,1);
      if (lVar10 == 0) goto code_r0x010406aa;
code_r0x01040640:
      uVar9 = *(uint *)(lVar10 + 0x10);
code_r0x01040642:
      *param_3 = uVar9;
      lVar10 = 0;
    }
  }
  if (lRam00000000040b6a20 == lStack_48) {
    return;
  }
  puVar3 = (uint *)&UNK_010408da;
  puVar11 = (uint *)(*(code *)&UNK_019e6a1e)(lVar10,0);
  puVar15 = extraout_a1;
code_r0x010408dc:
  puVar4 = puVar3;
  *(BADSPACEBASE **)(puVar7 + -0x10) = register0x00002010;
  *(uint **)(puVar7 + -0x20) = unaff_s2;
  *(undefined8 *)(puVar7 + -0x30) = uVar17;
  *(uint **)(puVar7 + -8) = puVar4;
  *(uint **)(puVar7 + -0x18) = unaff_s1;
  *(uint **)(puVar7 + -0x28) = unaff_s3;
  *(uint **)(puVar7 + -0x38) = unaff_retaddr;
  *(long *)(puVar7 + -0x48) = lRam00000000040b6a20;
  if (puVar15 == (uint *)0x0) {
    uVar17 = 0x201f8670;
    puVar3 = param_4;
code_r0x010409be:
    *(undefined8 *)(puVar7 + -0x58) = uVar17;
    (*(code *)&UNK_019e6ea4)(1,puVar7 + -0x58);
    (*(code *)&UNK_01a84340)(0,puVar4);
    lVar10 = lRam00000000040b6fa0;
    if (cRam00000000040ef504 != '\0') {
      *(uint *)(lRam00000000040b6fa0 + 0x11152c) =
           *(uint *)(lRam00000000040b6fa0 + 0x11152c) | 0x400000;
      puVar3 = (uint *)(lVar10 + 0x111520);
      puVar13 = (uint *)0x400000;
      *puVar3 = 0x400000;
      *(undefined4 *)(lVar10 + 0x1113d0) = 0;
    }
    ebreak();
    lVar10 = 0x1f;
  }
  else {
    puVar3 = (uint *)(long)(int)*param_4;
    unaff_s1 = param_4;
    unaff_retaddr = puVar11;
    if ((puVar3 != (uint *)0x0) && (puVar13 == (uint *)0x0)) {
      uVar17 = 0x201f8688;
      goto code_r0x010409be;
    }
    if (puVar11 == (uint *)0x0) {
      lVar10 = 0x31;
    }
    else {
      unaff_s3 = (uint *)(ulong)*(ushort *)(*(long *)(lRam00000000040ef4f8 + 0x1d0) + 0x68);
      bVar1 = *(byte *)(*(long *)(lRam00000000040ef4f8 + 0x1d0) + 0x58);
      puVar3 = puVar15;
      if ((char)*puVar15 == '\0') {
        uVar9 = 0;
      }
      else {
        do {
          puVar14 = puVar3;
          puVar3 = (uint *)((long)puVar14 + 1);
        } while (*(char *)((long)puVar14 + 1) != '\0');
        uVar9 = ((int)puVar14 - (int)puVar15) + 1U & 0xffff;
      }
      *(uint **)(puVar7 + -0x80) = puVar13;
      *(ulong *)(puVar7 + -0x78) = (ulong)bVar1;
      (*(code *)&UNK_0104035c)(puVar15,uVar9,puVar7 + -0x58);
      puVar3 = *(uint **)(puVar7 + -0x78);
      *(uint *)(puVar7 + -100) = *param_4;
      puVar13 = unaff_s3;
      iVar8 = (*(code *)&UNK_0103fab8)
                        (puVar11,1,puVar7 + -0x58,*(undefined8 *)(puVar7 + -0x80),puVar7 + -100,
                         puVar7 + -0x68);
      lVar10 = (long)iVar8;
      if (lVar10 == 0) {
        if (*(int *)(puVar7 + -0x68) == 0) {
          *param_4 = *(uint *)(puVar7 + -100);
          lVar10 = 0;
        }
        else {
          if (*(int *)(puVar7 + -0x68) == -2) {
            *(undefined8 *)(puVar7 + -0x60) = 0x201f86a0;
            (*(code *)&UNK_019e6ea4)(1,puVar7 + -0x60);
            (*(code *)&UNK_01a84340)(0,puVar4);
            lVar10 = lRam00000000040b6fa0;
            if (cRam00000000040ef504 == '\0') {
              ebreak();
            }
            else {
              *(uint *)(lRam00000000040b6fa0 + 0x11152c) =
                   *(uint *)(lRam00000000040b6fa0 + 0x11152c) | 0x400000;
              puVar3 = (uint *)(lVar10 + 0x111520);
              puVar13 = (uint *)0x400000;
              *puVar3 = 0x400000;
              *(undefined4 *)(lVar10 + 0x1113d0) = 0;
              ebreak();
            }
          }
          lVar10 = 0xffff;
        }
      }
    }
  }
  if (lRam00000000040b6a20 == *(long *)(puVar7 + -0x48)) {
    return;
  }
  puVar5 = &UNK_01040ac4;
  puVar11 = (uint *)(*(code *)&UNK_019e6a1e)(lVar10,0);
  *(undefined1 **)(puVar7 + -0x90) = puVar7;
  *(undefined8 *)(puVar7 + -0xa8) = 0x40b6a20;
  *(uint **)(puVar7 + -0xb0) = unaff_retaddr;
  *(undefined **)(puVar7 + -0x88) = puVar5;
  *(uint **)(puVar7 + -0x98) = unaff_s1;
  *(uint **)(puVar7 + -0xa0) = unaff_s3;
  *(uint **)(puVar7 + -0xb8) = unaff_s6;
  *(long *)(puVar7 + -200) = lRam00000000040b6a20;
  if (extraout_a1_00 != (uint *)0x0) {
    unaff_s1 = extraout_a1_00;
    unaff_s3 = puVar13;
    unaff_s6 = puVar11;
    if ((*puVar3 != 0) && (puVar13 == (uint *)0x0)) {
      uVar17 = 0x201f86d0;
      goto code_r0x01040b6c;
    }
    *(uint **)(puVar7 + -0xd8) = puVar3;
    iVar8 = (*(code *)&UNK_01a88c90)(extraout_a1_00,puVar13);
    lVar10 = (long)iVar8;
    param_4 = *(uint **)(puVar7 + -0xd8);
    if (lVar10 == 0) goto code_r0x01040b12;
    if (lRam00000000040b6a20 != *(long *)(puVar7 + -200)) goto code_r0x01040bda;
    register0x00002010 = *(BADSPACEBASE **)(puVar7 + -0x90);
    puVar2 = (undefined8 *)(puVar7 + -0x88);
    uVar17 = *(undefined8 *)(puVar7 + -0xa8);
    unaff_retaddr = *(uint **)(puVar7 + -0xb0);
    unaff_s3 = *(uint **)(puVar7 + -0xa0);
    unaff_s1 = *(uint **)(puVar7 + -0x98);
    unaff_s6 = *(uint **)(puVar7 + -0xb8);
    puVar7 = puVar7 + -0x80;
    puVar3 = (uint *)*puVar2;
    puVar15 = extraout_a1_00;
    unaff_s2 = puVar4;
    goto code_r0x010408dc;
  }
  uVar17 = 0x201f86b8;
code_r0x01040b6c:
  *(undefined8 *)(puVar7 + -0xd0) = uVar17;
  (*(code *)&UNK_019e6ea4)(1,puVar7 + -0xd0);
  (*(code *)&UNK_01a84340)(0,puVar5);
  lVar10 = lRam00000000040b6fa0;
  param_4 = puVar3;
  if (cRam00000000040ef504 != '\0') {
    *(uint *)(lRam00000000040b6fa0 + 0x11152c) =
         *(uint *)(lRam00000000040b6fa0 + 0x11152c) | 0x400000;
    param_4 = (uint *)(lVar10 + 0x111520);
    puVar13 = (uint *)0x400000;
    *param_4 = 0x400000;
    *(undefined4 *)(lVar10 + 0x1113d0) = 0;
  }
  ebreak();
  lVar10 = 0x1f;
  puVar3 = puVar13;
code_r0x01040b12:
  puVar13 = unaff_s3;
  puVar11 = unaff_s6;
  if (lRam00000000040b6a20 == *(long *)(puVar7 + -200)) {
    return;
  }
code_r0x01040bda:
  puVar6 = &UNK_01040be2;
  uVar17 = (*(code *)&UNK_019e6a1e)(lVar10,0);
  *(undefined1 **)(puVar7 + -0xf0) = puVar7 + -0x80;
  *(uint **)(puVar7 + -0xf8) = unaff_s1;
  *(uint **)(puVar7 + -0x100) = puVar4;
  *(undefined **)(puVar7 + -0x110) = puVar5;
  *(undefined8 *)(puVar7 + -0x118) = 0x40b6a20;
  *(uint **)(puVar7 + -0x120) = puVar11;
  *(undefined8 *)(puVar7 + -0x128) = unaff_s7;
  *(undefined **)(puVar7 + -0xe8) = puVar6;
  *(uint **)(puVar7 + -0x108) = puVar13;
  *(undefined8 *)(puVar7 + -0x130) = unaff_s8;
  *(undefined8 *)(puVar7 + -0x138) = unaff_s9;
  lVar10 = *(long *)(lRam00000000040ef4f8 + 0x1d0);
  *(long *)(puVar7 + -0x148) = lRam00000000040b6a20;
  if ((uint *)(ulong)*(byte *)(lVar10 + 0x58) < param_4) {
    *(undefined8 *)(puVar7 + -0x150) = 0x201f86e8;
    (*(code *)&UNK_019e6ea4)(1,puVar7 + -0x150,0);
    (*(code *)&UNK_01a84340)(0,puVar6);
    lVar12 = lRam00000000040b6fa0;
    if (cRam00000000040ef504 != '\0') {
      *(uint *)(lRam00000000040b6fa0 + 0x11152c) =
           *(uint *)(lRam00000000040b6fa0 + 0x11152c) | 0x400000;
      *(undefined4 *)(lVar12 + 0x111520) = 0x400000;
      *(undefined4 *)(lVar12 + 0x1113d0) = 0;
    }
    ebreak();
    if (3 < *(byte *)(lVar10 + 0x58)) goto code_r0x01040d0a;
    if (extraout_a1_01 == 0) goto code_r0x01040ce4;
  }
  else {
    if ((uint *)0x3 < (uint *)(ulong)*(byte *)(lVar10 + 0x58)) {
code_r0x01040d0a:
      *(undefined8 *)(puVar7 + -0x150) = 0x201f8700;
      (*(code *)&UNK_019e6ea4)(1,puVar7 + -0x150);
      (*(code *)&UNK_01a84340)(0,puVar6);
      lVar12 = lRam00000000040b6fa0;
      if (cRam00000000040ef504 == '\0') {
        ebreak();
      }
      else {
        *(uint *)(lRam00000000040b6fa0 + 0x11152c) =
             *(uint *)(lRam00000000040b6fa0 + 0x11152c) | 0x400000;
        *(undefined4 *)(lVar12 + 0x111520) = 0x400000;
        *(undefined4 *)(lVar12 + 0x1113d0) = 0;
        ebreak();
      }
    }
    if (extraout_a1_01 == 0) {
      if (param_4 == (uint *)0x0) goto code_r0x01040cb8;
code_r0x01040ce4:
      puVar15 = (uint *)(lVar10 + 0x5c);
      param_4 = puVar3 + (long)param_4;
      puVar13 = puVar3;
      do {
        uVar9 = *puVar15;
        puVar11 = puVar13 + 1;
        puVar15 = puVar15 + 1;
        *puVar13 = uVar9;
        puVar13 = puVar11;
      } while (param_4 != puVar11);
      goto code_r0x01040cb8;
    }
  }
  uVar9 = (*(code *)&UNK_01a533ac)(uVar17,extraout_a1_01);
  uVar17 = 0xfffff;
  *puVar3 = (uVar9 >> 0x14 ^ uVar9) & 0xfffff;
  if ((uint *)0x1 < param_4) {
    iVar8 = *(int *)(lVar10 + 0x90);
    *(long *)(puVar7 + -0x158) = (long)(int)uVar9;
    uVar9 = (*(code *)&UNK_010402e4)(lVar10 + 0x75,(long)iVar8,extraout_a1_01);
    puVar3[1] = (uVar9 ^ uVar9 >> 0x14) & 0xfffff;
    if (param_4 != (uint *)0x2) {
      uVar9 = (*(code *)&UNK_010402e4)
                        (lVar10 + 0x80,(long)*(int *)(lVar10 + 0x94),
                         *(undefined8 *)(puVar7 + -0x158),extraout_a1_01);
      puVar3[2] = (uVar9 ^ uVar9 >> 0x14) & 0xfffff;
    }
  }
code_r0x01040cb8:
  if (lRam00000000040b6a20 != *(long *)(puVar7 + -0x148)) {
    puVar5 = &UNK_01040dfa;
    lVar12 = (*(code *)&UNK_019e6a1e)(0);
    *(undefined1 **)(puVar7 + -0x170) = puVar7 + -0xe0;
    *(uint **)(puVar7 + -0x178) = param_4;
    *(undefined **)(puVar7 + -0x168) = puVar5;
    *(uint **)(puVar7 + -0x180) = puVar3;
    *(long *)(puVar7 + -0x188) = lVar10;
    *(undefined8 *)(puVar7 + -400) = uVar17;
    lVar10 = *(long *)(lVar12 + 0x20);
    if (lVar10 != 0) {
      lVar16 = *(long *)(lVar10 + 0x20);
      if (lVar16 != 0) {
        lVar18 = *(long *)(lVar16 + 0x20);
        if (lVar18 != 0) {
          if (*(long *)(lVar18 + 0x20) != 0) {
            (*(code *)&UNK_01040dfc)();
            *(undefined8 *)(lVar18 + 0x20) = 0;
          }
          if (*(long *)(lVar18 + 0x28) != 0) {
            (*(code *)&UNK_01040dfc)();
            *(undefined8 *)(lVar18 + 0x28) = 0;
          }
          (*(code *)&UNK_01854d0c)(0x40b77b0,lVar18);
          *(undefined8 *)(lVar16 + 0x20) = 0;
        }
        lVar18 = *(long *)(lVar16 + 0x28);
        if (lVar18 != 0) {
          if (*(long *)(lVar18 + 0x20) != 0) {
            (*(code *)&UNK_01040dfc)();
            *(undefined8 *)(lVar18 + 0x20) = 0;
          }
          if (*(long *)(lVar18 + 0x28) != 0) {
            (*(code *)&UNK_01040dfc)();
            *(undefined8 *)(lVar18 + 0x28) = 0;
          }
          (*(code *)&UNK_01854d0c)(0x40b77b0,lVar18);
          *(undefined8 *)(lVar16 + 0x28) = 0;
        }
        (*(code *)&UNK_01854d0c)(0x40b77b0,lVar16);
        *(undefined8 *)(lVar10 + 0x20) = 0;
      }
      lVar16 = *(long *)(lVar10 + 0x28);
      if (lVar16 != 0) {
        lVar18 = *(long *)(lVar16 + 0x20);
        if (lVar18 != 0) {
          if (*(long *)(lVar18 + 0x20) != 0) {
            (*(code *)&UNK_01040dfc)();
            *(undefined8 *)(lVar18 + 0x20) = 0;
          }
          if (*(long *)(lVar18 + 0x28) != 0) {
            (*(code *)&UNK_01040dfc)();
            *(undefined8 *)(lVar18 + 0x28) = 0;
          }
          (*(code *)&UNK_01854d0c)(0x40b77b0,lVar18);
          *(undefined8 *)(lVar16 + 0x20) = 0;
        }
        lVar18 = *(long *)(lVar16 + 0x28);
        if (lVar18 != 0) {
          if (*(long *)(lVar18 + 0x20) != 0) {
            (*(code *)&UNK_01040dfc)();
            *(undefined8 *)(lVar18 + 0x20) = 0;
          }
          if (*(long *)(lVar18 + 0x28) != 0) {
            (*(code *)&UNK_01040dfc)();
            *(undefined8 *)(lVar18 + 0x28) = 0;
          }
          (*(code *)&UNK_01854d0c)(0x40b77b0,lVar18);
          *(undefined8 *)(lVar16 + 0x28) = 0;
        }
        (*(code *)&UNK_01854d0c)(0x40b77b0,lVar16);
        *(undefined8 *)(lVar10 + 0x28) = 0;
      }
      (*(code *)&UNK_01854d0c)(0x40b77b0,lVar10);
      *(undefined8 *)(lVar12 + 0x20) = 0;
    }
    lVar10 = *(long *)(lVar12 + 0x28);
    if (lVar10 != 0) {
      lVar16 = *(long *)(lVar10 + 0x20);
      if (lVar16 != 0) {
        lVar18 = *(long *)(lVar16 + 0x20);
        if (lVar18 != 0) {
          if (*(long *)(lVar18 + 0x20) != 0) {
            (*(code *)&UNK_01040dfc)();
            *(undefined8 *)(lVar18 + 0x20) = 0;
          }
          if (*(long *)(lVar18 + 0x28) != 0) {
            (*(code *)&UNK_01040dfc)();
            *(undefined8 *)(lVar18 + 0x28) = 0;
          }
          (*(code *)&UNK_01854d0c)(0x40b77b0,lVar18);
          *(undefined8 *)(lVar16 + 0x20) = 0;
        }
        lVar18 = *(long *)(lVar16 + 0x28);
        if (lVar18 != 0) {
          if (*(long *)(lVar18 + 0x20) != 0) {
            (*(code *)&UNK_01040dfc)();
            *(undefined8 *)(lVar18 + 0x20) = 0;
          }
          if (*(long *)(lVar18 + 0x28) != 0) {
            (*(code *)&UNK_01040dfc)();
            *(undefined8 *)(lVar18 + 0x28) = 0;
          }
          (*(code *)&UNK_01854d0c)(0x40b77b0,lVar18);
          *(undefined8 *)(lVar16 + 0x28) = 0;
        }
        (*(code *)&UNK_01854d0c)(0x40b77b0,lVar16);
        *(undefined8 *)(lVar10 + 0x20) = 0;
      }
      lVar16 = *(long *)(lVar10 + 0x28);
      if (lVar16 != 0) {
        lVar18 = *(long *)(lVar16 + 0x20);
        if (lVar18 != 0) {
          if (*(long *)(lVar18 + 0x20) != 0) {
            (*(code *)&UNK_01040dfc)();
            *(undefined8 *)(lVar18 + 0x20) = 0;
          }
          if (*(long *)(lVar18 + 0x28) != 0) {
            (*(code *)&UNK_01040dfc)();
            *(undefined8 *)(lVar18 + 0x28) = 0;
          }
          (*(code *)&UNK_01854d0c)(0x40b77b0,lVar18);
          *(undefined8 *)(lVar16 + 0x20) = 0;
        }
        lVar18 = *(long *)(lVar16 + 0x28);
        if (lVar18 != 0) {
          if (*(long *)(lVar18 + 0x20) != 0) {
            (*(code *)&UNK_01040dfc)();
            *(undefined8 *)(lVar18 + 0x20) = 0;
          }
          if (*(long *)(lVar18 + 0x28) != 0) {
            (*(code *)&UNK_01040dfc)();
            *(undefined8 *)(lVar18 + 0x28) = 0;
          }
          (*(code *)&UNK_01854d0c)(0x40b77b0,lVar18);
          *(undefined8 *)(lVar16 + 0x28) = 0;
        }
        (*(code *)&UNK_01854d0c)(0x40b77b0,lVar16);
        *(undefined8 *)(lVar10 + 0x28) = 0;
      }
      (*(code *)&UNK_01854d0c)(0x40b77b0,lVar10);
      *(undefined8 *)(lVar12 + 0x28) = 0;
    }
    (*(code *)&UNK_01854d0c)(0x40b77b0,lVar12);
    return;
  }
  return;
}

