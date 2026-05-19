//===-- E32CTargetInfo.h - E32C Target Implementation ---------*- C++ -*-===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#ifndef LLVM_LIB_TARGET_E32C_TARGETINFO_E32CTARGETINFO_H
#define LLVM_LIB_TARGET_E32C_TARGETINFO_E32CTARGETINFO_H

namespace llvm {

class Target;

Target &getTheE32CTarget();

} // namespace llvm

#endif // LLVM_LIB_TARGET_E32C_TARGETINFO_E32CTARGETINFO_H
