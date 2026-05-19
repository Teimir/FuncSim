//===-- E32CFixupKinds.h - E32C Specific Fixup Entries --------*- C++ -*-===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#ifndef LLVM_LIB_TARGET_E32C_MCTARGETDESC_E32CFIXUPKINDS_H
#define LLVM_LIB_TARGET_E32C_MCTARGETDESC_E32CFIXUPKINDS_H

#include "llvm/MC/MCFixup.h"

namespace llvm {
namespace E32C {
// Although most of the current fixup types reflect a unique relocation
// one can have multiple fixup types for a given relocation and thus need
// to be uniquely named.
//
// This table *must* be in the save order of
// MCFixupKindInfo Infos[E32C::NumTargetFixupKinds]
// in E32CAsmBackend.cpp.
//
enum Fixups {
  // Results in R_E32C_NONE
  FIXUP_E32C_NONE = FirstTargetFixupKind,

  FIXUP_E32C_21,   // 21-bit symbol relocation
  FIXUP_E32C_21_F, // 21-bit symbol relocation, last two bits masked to 0
  FIXUP_E32C_25,   // 25-bit branch targets
  FIXUP_E32C_32,   // general 32-bit relocation
  FIXUP_E32C_HI16, // upper 16-bits of a symbolic relocation
  FIXUP_E32C_LO16, // lower 16-bits of a symbolic relocation

  // Marker
  LastTargetFixupKind,
  NumTargetFixupKinds = LastTargetFixupKind - FirstTargetFixupKind
};
} // namespace E32C
} // namespace llvm

#endif // LLVM_LIB_TARGET_E32C_MCTARGETDESC_E32CFIXUPKINDS_H
