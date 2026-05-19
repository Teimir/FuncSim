//===-- E32C.h - Top-level interface for E32C representation --*- C++ -*-===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//
//
// This file contains the entry points for global functions defined in the LLVM
// E32C back-end.
//
//===----------------------------------------------------------------------===//

#ifndef LLVM_LIB_TARGET_E32C_E32C_H
#define LLVM_LIB_TARGET_E32C_E32C_H

#include "llvm/Pass.h"

namespace llvm {
class FunctionPass;
class E32CTargetMachine;
class PassRegistry;

// createE32CISelDag - This pass converts a legalized DAG into a
// E32C-specific DAG, ready for instruction scheduling.
FunctionPass *createE32CISelDag(E32CTargetMachine &TM);

// createE32CDelaySlotFillerPass - This pass fills delay slots
// with useful instructions or nop's
FunctionPass *createE32CDelaySlotFillerPass(const E32CTargetMachine &TM);

// createE32CMemAluCombinerPass - This pass combines loads/stores and
// arithmetic operations.
FunctionPass *createE32CMemAluCombinerPass();

// createE32CSetflagAluCombinerPass - This pass combines SET_FLAG and ALU
// operations.
FunctionPass *createE32CSetflagAluCombinerPass();

void initializeE32CDAGToDAGISelLegacyPass(PassRegistry &);

} // namespace llvm

#endif // LLVM_LIB_TARGET_E32C_E32C_H
