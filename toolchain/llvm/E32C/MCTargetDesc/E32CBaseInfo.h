//===-- E32CBaseInfo.h - Top level definitions for E32C MC ----*- C++ -*-===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//
//
// This file contains small standalone helper functions and enum definitions for
// the E32C target useful for the compiler back-end and the MC libraries.
//
//===----------------------------------------------------------------------===//

#ifndef LLVM_LIB_TARGET_E32C_MCTARGETDESC_E32CBASEINFO_H
#define LLVM_LIB_TARGET_E32C_MCTARGETDESC_E32CBASEINFO_H

#include "E32CMCTargetDesc.h"
#include "llvm/MC/MCExpr.h"
#include "llvm/Support/DataTypes.h"
#include "llvm/Support/ErrorHandling.h"

namespace llvm {

// E32CII - This namespace holds all of the target specific flags that
// instruction info tracks.
namespace E32CII {
// Target Operand Flag enum.
enum TOF {
  //===------------------------------------------------------------------===//
  // E32C Specific MachineOperand flags.
  MO_NO_FLAG,

  // MO_ABS_HI/LO - Represents the hi or low part of an absolute symbol
  // address.
  MO_ABS_HI,
  MO_ABS_LO,
};
} // namespace E32CII

static inline unsigned getE32CRegisterNumbering(unsigned Reg) {
  if (Reg >= E32C::R0 && Reg <= E32C::R31)
    return Reg - E32C::R0;
  if (Reg == E32C::SP)
    return 30;
  if (Reg == E32C::PC)
    return 31;
  llvm_unreachable("Unknown register number!");
}
} // namespace llvm
#endif // LLVM_LIB_TARGET_E32C_MCTARGETDESC_E32CBASEINFO_H
