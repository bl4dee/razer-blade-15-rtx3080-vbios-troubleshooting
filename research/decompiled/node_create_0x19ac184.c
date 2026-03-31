// Function: node_create
// Address: 0x19ac184


/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_019ac184(undefined8 *param_1,undefined8 **param_2)

{
  char *pcVar1;
  int iVar2;
  long lVar3;
  undefined8 *puVar4;
  undefined *puVar5;
  ulong uVar6;
  undefined1 *puVar7;
  uint uVar8;
  int iVar9;
  undefined8 uVar10;
  undefined4 *puVar11;
  undefined4 *puVar12;
  long lVar13;
  undefined8 *puVar14;
  undefined1 *puVar15;
  undefined8 **ppuVar16;
  undefined8 *puVar17;
  ulong uVar18;
  undefined1 *puVar19;
  undefined1 *puVar20;
  undefined8 **unaff_s2;
  undefined8 *unaff_s3;
  long lVar21;
  undefined1 auStack_150 [8];
  ulong auStack_148 [4];
  long lStack_128;
  int iStack_124;
  undefined1 *puStack_120;
  undefined8 uStack_118;
  undefined8 uStack_110;
  long lStack_108;
  long lStack_f8;
  undefined8 uStack_f0;
  undefined8 *puStack_e8;
  undefined8 **ppuStack_e0;
  undefined4 *puStack_d8;
  undefined8 *puStack_d0;
  undefined *puStack_c8;
  undefined8 *puStack_b8;
  undefined8 uStack_b0;
  long lStack_a8;
  undefined8 uStack_50;
  long lStack_48;
  
  lVar21 = 0x40b6a20;
  lStack_48 = lRam00000000040b6a20;
  if (param_2 == (undefined8 **)0x0) {
    uStack_50 = 0x2030da10;
code_r0x019ac262:
    (*(code *)&UNK_019e6ea4)(1,&uStack_50);
    (*(code *)&UNK_01a84340)(0);
    lVar13 = lRam00000000040b6fa0;
    if (cRam00000000040ef504 != '\0') {
      *(uint *)(lRam00000000040b6fa0 + 0x11152c) =
           *(uint *)(lRam00000000040b6fa0 + 0x11152c) | 0x400000;
      *(undefined4 *)(lVar13 + 0x111520) = 0x400000;
      *(undefined4 *)(lVar13 + 0x1113d0) = 0;
    }
    ebreak();
    uVar10 = 0x1f;
  }
  else {
    *param_1 = 0;
    ppuVar16 = param_2;
    unaff_s2 = param_2;
    if (*(char *)param_2 == '\0') {
      lVar13 = 0x21;
      uVar6 = 1;
    }
    else {
      do {
        pcVar1 = (char *)((long)ppuVar16 + 1);
        ppuVar16 = (undefined8 **)((long)ppuVar16 + 1);
      } while (*pcVar1 != '\0');
      uVar8 = ((int)ppuVar16 - (int)param_2) + 1;
      if (0x100 < uVar8) {
        uStack_50 = 0x2030da28;
        goto code_r0x019ac262;
      }
      uVar6 = (ulong)uVar8;
      lVar13 = uVar6 + 0x20;
    }
    unaff_s3 = (undefined8 *)FUN_018543c4(0x40b77d8,lVar13);
    if (unaff_s3 == (undefined8 *)0x0) {
      uStack_50 = 0x2030da40;
      (*(code *)&UNK_019e6ea4)(1,&uStack_50);
      uVar10 = 0x51;
    }
    else {
      (*(code *)&UNK_01b0e04c)(0,0x20);
      lVar13 = FUN_018514b0((undefined *)((long)unaff_s3 + 0x19),uVar6,param_2,uVar6);
      if (lVar13 == 0) {
        uStack_50 = 0x2030da58;
        (*(code *)&UNK_019e6ea4)(1,&uStack_50);
        FUN_01854d0c(0x40b77b0,unaff_s3);
        uVar10 = 0x40;
      }
      else {
        *(undefined1 *)(unaff_s3 + 3) = 0;
        uVar10 = 0;
        *unaff_s3 = puRam00000000040ef620;
        puRam00000000040ef620 = unaff_s3;
        *param_1 = unaff_s3;
      }
    }
  }
  if (lRam00000000040b6a20 == lStack_48) {
    return;
  }
  puVar4 = (undefined8 *)&UNK_019ac332;
  puVar11 = (undefined4 *)(*(code *)&UNK_019e6a1e)(uVar10,0);
  lVar3 = lRam00000000040b7720;
  lVar13 = lRam00000000040b7718;
  lStack_a8 = lRam00000000040b6a20;
  *puVar11 = 0;
  if (*(uint *)(lRam00000000040b7720 + 8) < 0x20) {
    lVar21 = -0xeffffe;
  }
  else {
    if (*(int *)(lVar3 + 0x24) == 0x40) {
      *(undefined1 *)(lVar13 + 0x535) = 1;
    }
    *(undefined1 *)(lVar13 + 0x533) = *(undefined1 *)(lVar3 + 0x20);
    if (*(char *)(lVar3 + 0x21) != '\0') {
      *(undefined4 *)(lVar13 + 0x5b7c) = 1;
      *(undefined1 *)(lVar13 + 0x573) = 1;
      *(undefined1 *)(lVar13 + 0x587) = 1;
    }
    if (*(char *)(lVar3 + 0x20) == '\0') {
      uVar10 = 0;
      goto code_r0x019ac3b2;
    }
    iVar9 = *(int *)(lVar3 + 0x24);
    if ((uRam00000000040b828c & 8) == 0) {
      unaff_s3 = (undefined8 *)0x40;
      lVar21 = 0x40;
    }
    else {
      lVar21 = (long)*(int *)(*(long *)(lRam00000000040ef4f8 + 0x1a0) + 0x3c1a0);
      iVar2 = iRam00000000040ef550 + 1;
      if (lVar21 != 0) {
        puVar17 = (undefined8 *)(*(long *)(lRam00000000040ef4f8 + 0x1a0) + 0x3bfa0);
        puVar14 = (undefined8 *)(((ulong)(lVar21 << 0x20) >> 0x1c) + (long)puVar17);
        do {
          if ((*(int *)(puVar17 + 1) == iRam00000000040b8288) &&
             (unaff_s2 = (undefined8 **)*puVar17, unaff_s2 != (undefined8 **)0x0)) {
            if (*(char *)((long)unaff_s2 + 0x533) == '\0') {
              unaff_s3 = (undefined8 *)0x40;
              lVar21 = 0x40;
              goto code_r0x019ac454;
            }
            iRam00000000040ef550 = iVar2;
            if (*(char *)((long)unaff_s2[0x39b] + 0x1514) != '\0') {
              *(undefined4 *)(unaff_s2[0x39b] + 0x2a0) = 0;
            }
            (*(code *)&UNK_019ec206)();
            uVar8 = (*(code *)&UNK_0142131c)(unaff_s2);
            lVar21 = (long)(int)uVar8;
            if (lVar21 == 0) {
              if (*(int *)((long)unaff_s2 + 0x5b7c) == 1) {
                uVar10 = 0x25;
              }
              else {
                uVar10 = 5;
              }
              uVar8 = (*(code *)&UNK_013f4a14)(unaff_s2,uVar10);
              lVar21 = (long)(int)uVar8;
              if (lVar21 == 0) {
                uVar8 = (*(code *)&UNK_01421528)(unaff_s2,(long)iVar9);
                lVar21 = (long)(int)uVar8;
                if (lVar21 == 0) {
                  if ((long)iVar9 == 7) {
                    *(char *)((long)unaff_s2 + 0x532) = '\x01';
                  }
                  else {
                    *(char *)((long)unaff_s2 + 0x531) = '\x01';
                    *(char *)((long)unaff_s2 + 0x4051) = '\x01';
                  }
                  iRam00000000040ef550 = iRam00000000040ef550 + -1;
                  if (*(int *)((long)unaff_s2 + 0x5b7c) == 1) {
                    pcVar1 = (char *)((long)unaff_s2 + 0x5b7c);
                    pcVar1[0] = '\x03';
                    pcVar1[1] = '\0';
                    pcVar1[2] = '\0';
                    pcVar1[3] = '\0';
                    uVar10 = 0;
                  }
                  else {
                    uVar10 = 0;
                  }
                  goto code_r0x019ac3b2;
                }
                puStack_b8 = (undefined8 *)(ulong)uVar8;
                uStack_b0 = 0x2030daa0;
              }
              else {
                puStack_b8 = (undefined8 *)(ulong)uVar8;
                uStack_b0 = 0x2030da88;
              }
            }
            else {
              puStack_b8 = (undefined8 *)(ulong)uVar8;
              uStack_b0 = 0x2030da70;
            }
            (*(code *)&UNK_019e6ea4)(2,&puStack_b8);
            (*(code *)&UNK_01a84340)(lVar21,puVar4);
            lVar13 = lRam00000000040b6fa0;
            if (cRam00000000040ef504 != '\0') {
              *(uint *)(lRam00000000040b6fa0 + 0x11152c) =
                   *(uint *)(lRam00000000040b6fa0 + 0x11152c) | 0x400000;
              *(undefined4 *)(lVar13 + 0x111520) = 0x400000;
              *(undefined4 *)(lVar13 + 0x1113d0) = 0;
            }
            ebreak();
            unaff_s3 = (undefined8 *)(long)(int)lVar21;
            iRam00000000040ef550 = iRam00000000040ef550 + -1;
            goto code_r0x019ac454;
          }
          puVar17 = puVar17 + 2;
        } while (puVar17 != puVar14);
      }
      unaff_s3 = (undefined8 *)0x57;
      lVar21 = 0x57;
code_r0x019ac454:
      puStack_b8 = (undefined8 *)0x2030dab8;
      (*(code *)&UNK_019e6ea4)(1,&puStack_b8);
    }
    unaff_s2 = &puStack_b8;
    uStack_b0 = 0x2030dad0;
    puStack_b8 = unaff_s3;
    (*(code *)&UNK_019e6ea4)(2,unaff_s2);
  }
  *puVar11 = (int)lVar21;
  uVar10 = 0xffffffffffffffff;
  puVar4 = unaff_s3;
code_r0x019ac3b2:
  if (lRam00000000040b6a20 == lStack_a8) {
    return;
  }
  puVar5 = &UNK_019ac62a;
  puVar12 = (undefined4 *)(*(code *)&UNK_019e6a1e)(uVar10,0);
  lVar13 = lRam00000000040b7720;
  puVar7 = auStack_150;
  uStack_f0 = 0x40b6a20;
  lStack_108 = lRam00000000040b6a20;
  *puVar12 = 0;
  auStack_148[2] = 0;
  auStack_148[3] = 0;
  lStack_128 = 0;
  puStack_120 = (undefined1 *)0x0;
  uStack_118 = 0;
  uStack_110 = 0;
  lStack_f8 = lVar21;
  puStack_e8 = puVar4;
  ppuStack_e0 = unaff_s2;
  puStack_d8 = puVar11;
  puStack_d0 = &uStack_50;
  puStack_c8 = puVar5;
  if (*(uint *)(lRam00000000040b7720 + 8) < 0x58) {
    auStack_148[0] = 0x2030dae8;
    (*(code *)&UNK_019e6ea4)(1,auStack_148);
    uVar6 = 0xffffffffff100002;
    goto code_r0x019ac744;
  }
  uVar8 = *(uint *)(lVar13 + 0x3c);
  if ((long)(int)uVar8 == 0) {
    auStack_148[2] = *(undefined8 *)(lVar13 + 0x28);
    puStack_120 = auStack_150;
  }
  else {
    puVar15 = (undefined1 *)(lVar13 + 0x58);
    uVar6 = (ulong)((long)(int)uVar8 << 0x20) >> 0x1b;
    puVar7 = puVar15;
    do {
      uVar18 = (ulong)(byte)puVar7[1];
      if (0x40 < uVar18) {
        if (uVar18 == 0x80) {
code_r0x019ac71c:
          puVar7[2] = 8;
          auStack_148[1] = 0x2030db00;
          uVar6 = 0x56;
          auStack_148[0] = uVar18;
          (*(code *)&UNK_019e6ea4)(2,auStack_148);
          goto code_r0x019ac744;
        }
code_r0x019ac6c0:
        auStack_148[1] = 0x2030db18;
        auStack_148[0] = uVar18;
        (*(code *)&UNK_019e6ea4)(2,auStack_148);
        puVar7[2] = 8;
        uVar6 = 0x56;
        *puVar12 = 0x56;
        uVar10 = 0xffffffffffffffff;
        goto code_r0x019ac6ee;
      }
      if (uVar18 < 4) {
        if (uVar18 == 3) goto code_r0x019ac6c0;
      }
      else if ((1L << ((long)(int)((byte)puVar7[1] - 4) & 0x3fU) & _UNK_01d72638) == 0) {
        if (uVar18 == 0x20) goto code_r0x019ac71c;
        goto code_r0x019ac6c0;
      }
      puVar7 = puVar7 + 0x20;
    } while (puVar7 != puVar15 + uVar6);
    auStack_148[2] = *(undefined8 *)(lVar13 + 0x28);
    lVar21 = -uVar6;
    puStack_120 = auStack_150 + lVar21;
    puVar7 = auStack_150 + lVar21;
    lStack_128 = (ulong)uVar8 << 0x20;
    puVar19 = auStack_150 + lVar21;
    do {
      puVar20 = puVar19 + 0x20;
      *puVar19 = *puVar15;
      puVar19[1] = puVar15[1];
      puVar19[2] = puVar15[2];
      puVar19[3] = puVar15[3];
      *(undefined4 *)(puVar19 + 4) = *(undefined4 *)(puVar15 + 4);
      *(undefined4 *)(puVar19 + 8) = *(undefined4 *)(puVar15 + 8);
      *(undefined4 *)(puVar19 + 0xc) = *(undefined4 *)(puVar15 + 0xc);
      *(undefined4 *)(puVar19 + 0x10) = *(undefined4 *)(puVar15 + 0x10);
      *(undefined4 *)(puVar19 + 0x14) = *(undefined4 *)(puVar15 + 0x14);
      *(undefined4 *)(puVar19 + 0x18) = *(undefined4 *)(puVar15 + 0x18);
      *(undefined4 *)(puVar19 + 0x1c) = *(undefined4 *)(puVar15 + 0x1c);
      puVar15 = puVar15 + 0x20;
      puVar19 = puVar20;
    } while (puVar20 != auStack_150);
  }
  uStack_110 = *(undefined8 *)(lVar13 + 0x48);
  uStack_118 = CONCAT44(uStack_118._4_4_,*(undefined4 *)(lVar13 + 0x40));
  iVar9 = (*pcRam00000000040b7580)
                    (0x40b7548,(long)*(int *)(lVar13 + 0x20),(long)*(int *)(lVar13 + 0x24),
                     0x20800122,auStack_148 + 2,0x30,pcRam00000000040b7580);
  uVar6 = (ulong)iVar9;
  if (uVar6 != 0) goto code_r0x019ac89a;
  uVar18 = 0;
  if (iStack_124 != 0) {
    do {
      uVar6 = (uVar18 << 0x20) >> 0x1b;
      lVar21 = uVar6 + lVar13 + 0x58;
      uVar18 = (ulong)((int)uVar18 + 1);
      *(undefined1 *)(lVar21 + 2) = puVar7[uVar6 + 2];
      *(undefined4 *)(lVar21 + 0x10) = *(undefined4 *)(puVar7 + uVar6 + 0x10);
      *(undefined4 *)(lVar21 + 0x14) = *(undefined4 *)(puVar7 + uVar6 + 0x14);
      uVar6 = uVar18;
    } while (uVar18 < (ulong)(long)iStack_124);
  }
  uVar10 = 0;
code_r0x019ac6ee:
  while (lRam00000000040b6a20 != lStack_108) {
    (*(code *)&UNK_019e6a1e)(uVar10,0);
code_r0x019ac89a:
    auStack_148[0] = uVar6 & 0xffffffff;
    auStack_148[1] = 0x2030db30;
    (*(code *)&UNK_019e6ea4)(2,auStack_148);
code_r0x019ac744:
    *puVar12 = (int)uVar6;
    uVar10 = 0xffffffffffffffff;
  }
  return;
}

