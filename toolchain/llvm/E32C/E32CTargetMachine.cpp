//===-- E32CTargetMachine.cpp - Define TargetMachine for E32C ---------===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//
//
// Implements the info about E32C target spec.
//
//===----------------------------------------------------------------------===//

#include "E32CTargetMachine.h"

#include "E32C.h"
#include "E32CMachineFunctionInfo.h"
#include "E32CTargetObjectFile.h"
#include "E32CTargetTransformInfo.h"
#include "TargetInfo/E32CTargetInfo.h"
#include "llvm/Analysis/TargetTransformInfo.h"
#include "llvm/CodeGen/Passes.h"
#include "llvm/CodeGen/TargetLoweringObjectFileImpl.h"
#include "llvm/CodeGen/TargetPassConfig.h"
#include "llvm/MC/TargetRegistry.h"
#include "llvm/Support/FormattedStream.h"
#include "llvm/Target/TargetOptions.h"
#include <optional>

using namespace llvm;

namespace llvm {
void initializeE32CMemAluCombinerPass(PassRegistry &);
} // namespace llvm

extern "C" LLVM_EXTERNAL_VISIBILITY void LLVMInitializeE32CTarget() {
  // Register the target.
  RegisterTargetMachine<E32CTargetMachine> registered_target(
      getTheE32CTarget());
  PassRegistry &PR = *PassRegistry::getPassRegistry();
  initializeE32CDAGToDAGISelLegacyPass(PR);
}

static std::string computeDataLayout() {
  // Little-endian ELF32 (matches src/core/elf.py)
  return "e"        // Little endian
         "-m:e"     // ELF name manging
         "-p:32:32" // 32-bit pointers, 32 bit aligned
         "-i64:64"  // 64 bit integers, 64 bit aligned
         "-a:0:32"  // 32 bit alignment of objects of aggregate type
         "-n32"     // 32 bit native integer width
         "-S64";    // 64 bit natural stack alignment
}

static Reloc::Model getEffectiveRelocModel(std::optional<Reloc::Model> RM) {
  return RM.value_or(Reloc::PIC_);
}

E32CTargetMachine::E32CTargetMachine(
    const Target &T, const Triple &TT, StringRef Cpu, StringRef FeatureString,
    const TargetOptions &Options, std::optional<Reloc::Model> RM,
    std::optional<CodeModel::Model> CodeModel, CodeGenOptLevel OptLevel,
    bool JIT)
    : LLVMTargetMachine(T, computeDataLayout(), TT, Cpu, FeatureString, Options,
                        getEffectiveRelocModel(RM),
                        getEffectiveCodeModel(CodeModel, CodeModel::Medium),
                        OptLevel),
      Subtarget(TT, Cpu, FeatureString, *this, Options, getCodeModel(),
                OptLevel),
      TLOF(new E32CTargetObjectFile()) {
  initAsmInfo();
}

TargetTransformInfo
E32CTargetMachine::getTargetTransformInfo(const Function &F) const {
  return TargetTransformInfo(E32CTTIImpl(this, F));
}

MachineFunctionInfo *E32CTargetMachine::createMachineFunctionInfo(
    BumpPtrAllocator &Allocator, const Function &F,
    const TargetSubtargetInfo *STI) const {
  return E32CMachineFunctionInfo::create<E32CMachineFunctionInfo>(Allocator,
                                                                    F, STI);
}

namespace {
// E32C Code Generator Pass Configuration Options.
class E32CPassConfig : public TargetPassConfig {
public:
  E32CPassConfig(E32CTargetMachine &TM, PassManagerBase *PassManager)
      : TargetPassConfig(TM, *PassManager) {}

  E32CTargetMachine &getE32CTargetMachine() const {
    return getTM<E32CTargetMachine>();
  }

  void addIRPasses() override;
  bool addInstSelector() override;
  void addPreSched2() override;
  void addPreEmitPass() override;
};
} // namespace

TargetPassConfig *
E32CTargetMachine::createPassConfig(PassManagerBase &PassManager) {
  return new E32CPassConfig(*this, &PassManager);
}

void E32CPassConfig::addIRPasses() {
  addPass(createAtomicExpandLegacyPass());

  TargetPassConfig::addIRPasses();
}

// Install an instruction selector pass.
bool E32CPassConfig::addInstSelector() {
  addPass(createE32CISelDag(getE32CTargetMachine()));
  return false;
}

// Implemented by targets that want to run passes immediately before
// machine code is emitted.
void E32CPassConfig::addPreEmitPass() {
  addPass(createE32CDelaySlotFillerPass(getE32CTargetMachine()));
}

// Run passes after prolog-epilog insertion and before the second instruction
// scheduling pass.
void E32CPassConfig::addPreSched2() {
  addPass(createE32CMemAluCombinerPass());
}
