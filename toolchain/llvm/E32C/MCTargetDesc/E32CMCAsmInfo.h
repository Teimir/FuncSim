//=====-- E32CMCAsmInfo.h - E32C asm properties -----------*- C++ -*--====//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//
//
// This file contains the declaration of the E32CMCAsmInfo class.
//
//===----------------------------------------------------------------------===//

#ifndef LLVM_LIB_TARGET_E32C_MCTARGETDESC_E32CMCASMINFO_H
#define LLVM_LIB_TARGET_E32C_MCTARGETDESC_E32CMCASMINFO_H

#include "llvm/MC/MCAsmInfoELF.h"

namespace llvm {
class Triple;

class E32CMCAsmInfo : public MCAsmInfoELF {
  void anchor() override;

public:
  explicit E32CMCAsmInfo(const Triple &TheTriple,
                          const MCTargetOptions &Options);
};

} // namespace llvm

#endif // LLVM_LIB_TARGET_E32C_MCTARGETDESC_E32CMCASMINFO_H
