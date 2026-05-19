//===-- E32CTargetMachine.h - Define TargetMachine for E32C --- C++ ---===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//
//
// This file declares the E32C specific subclass of TargetMachine.
//
//===----------------------------------------------------------------------===//

#ifndef LLVM_LIB_TARGET_E32C_E32CTARGETMACHINE_H
#define LLVM_LIB_TARGET_E32C_E32CTARGETMACHINE_H

#include "E32CISelLowering.h"
#include "E32CInstrInfo.h"
#include "E32CSelectionDAGInfo.h"
#include "E32CSubtarget.h"
#include "llvm/Target/TargetMachine.h"
#include <optional>

namespace llvm {

class E32CTargetMachine : public LLVMTargetMachine {
  E32CSubtarget Subtarget;
  std::unique_ptr<TargetLoweringObjectFile> TLOF;

public:
  E32CTargetMachine(const Target &TheTarget, const Triple &TargetTriple,
                     StringRef Cpu, StringRef FeatureString,
                     const TargetOptions &Options,
                     std::optional<Reloc::Model> RM,
                     std::optional<CodeModel::Model> CodeModel,
                     CodeGenOptLevel OptLevel, bool JIT);

  const E32CSubtarget *
  getSubtargetImpl(const llvm::Function & /*Fn*/) const override {
    return &Subtarget;
  }

  TargetTransformInfo getTargetTransformInfo(const Function &F) const override;

  // Pass Pipeline Configuration
  TargetPassConfig *createPassConfig(PassManagerBase &pass_manager) override;

  TargetLoweringObjectFile *getObjFileLowering() const override {
    return TLOF.get();
  }

  MachineFunctionInfo *
  createMachineFunctionInfo(BumpPtrAllocator &Allocator, const Function &F,
                            const TargetSubtargetInfo *STI) const override;

  bool isMachineVerifierClean() const override {
    return false;
  }
};
} // namespace llvm

#endif // LLVM_LIB_TARGET_E32C_E32CTARGETMACHINE_H
