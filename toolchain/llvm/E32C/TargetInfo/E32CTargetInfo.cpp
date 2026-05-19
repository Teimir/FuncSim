//===-- E32CTargetInfo.cpp - E32C Target Implementation -----------------===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#include "TargetInfo/E32CTargetInfo.h"
#include "llvm/MC/TargetRegistry.h"

using namespace llvm;

Target &llvm::getTheE32CTarget() {
  static Target TheE32CTarget;
  return TheE32CTarget;
}

extern "C" LLVM_EXTERNAL_VISIBILITY void LLVMInitializeE32CTargetInfo() {
  RegisterTarget<Triple::e32c> X(getTheE32CTarget(), "e32c", "E32C",
                                  "E32C");
}
