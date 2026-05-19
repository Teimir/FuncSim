//===-- E32CMCTargetDesc.cpp - E32C Target Descriptions -----------------===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//
//
// This file provides E32C specific target descriptions.
//
//===----------------------------------------------------------------------===//

#include "E32CMCTargetDesc.h"
#include "E32CInstPrinter.h"
#include "E32CMCAsmInfo.h"
#include "TargetInfo/E32CTargetInfo.h"
#include "llvm/ADT/StringRef.h"
#include "llvm/MC/MCInst.h"
#include "llvm/MC/MCInstrAnalysis.h"
#include "llvm/MC/MCInstrInfo.h"
#include "llvm/MC/MCRegisterInfo.h"
#include "llvm/MC/MCStreamer.h"
#include "llvm/MC/MCSubtargetInfo.h"
#include "llvm/MC/TargetRegistry.h"
#include "llvm/Support/ErrorHandling.h"
#include "llvm/TargetParser/Triple.h"
#include <cstdint>
#include <string>

#define GET_INSTRINFO_MC_DESC
#define ENABLE_INSTR_PREDICATE_VERIFIER
#include "E32CGenInstrInfo.inc"

#define GET_SUBTARGETINFO_MC_DESC
#include "E32CGenSubtargetInfo.inc"

#define GET_REGINFO_MC_DESC
#include "E32CGenRegisterInfo.inc"

using namespace llvm;

static MCInstrInfo *createE32CMCInstrInfo() {
  MCInstrInfo *X = new MCInstrInfo();
  InitE32CMCInstrInfo(X);
  return X;
}

static MCRegisterInfo *createE32CMCRegisterInfo(const Triple & /*TT*/) {
  MCRegisterInfo *X = new MCRegisterInfo();
  InitE32CMCRegisterInfo(X, E32C::R0, 0, 0, E32C::PC);
  return X;
}

static MCSubtargetInfo *
createE32CMCSubtargetInfo(const Triple &TT, StringRef CPU, StringRef FS) {
  std::string CPUName = std::string(CPU);
  if (CPUName.empty())
    CPUName = "generic";

  return createE32CMCSubtargetInfoImpl(TT, CPUName, /*TuneCPU*/ CPUName, FS);
}

static MCStreamer *createMCStreamer(const Triple &T, MCContext &Context,
                                    std::unique_ptr<MCAsmBackend> &&MAB,
                                    std::unique_ptr<MCObjectWriter> &&OW,
                                    std::unique_ptr<MCCodeEmitter> &&Emitter) {
  if (!T.isOSBinFormatELF())
    llvm_unreachable("OS not supported");

  return createELFStreamer(Context, std::move(MAB), std::move(OW),
                           std::move(Emitter));
}

static MCInstPrinter *createE32CMCInstPrinter(const Triple & /*T*/,
                                               unsigned SyntaxVariant,
                                               const MCAsmInfo &MAI,
                                               const MCInstrInfo &MII,
                                               const MCRegisterInfo &MRI) {
  if (SyntaxVariant == 0)
    return new E32CInstPrinter(MAI, MII, MRI);
  return nullptr;
}

static MCRelocationInfo *createE32CElfRelocation(const Triple &TheTriple,
                                                  MCContext &Ctx) {
  return createMCRelocationInfo(TheTriple, Ctx);
}

namespace {

class E32CMCInstrAnalysis : public MCInstrAnalysis {
public:
  explicit E32CMCInstrAnalysis(const MCInstrInfo *Info)
      : MCInstrAnalysis(Info) {}

  bool evaluateBranch(const MCInst &Inst, uint64_t Addr, uint64_t Size,
                      uint64_t &Target) const override {
    if (Inst.getNumOperands() == 0)
      return false;
    if (!isConditionalBranch(Inst) && !isUnconditionalBranch(Inst) &&
        !isCall(Inst))
      return false;

    if (Info->get(Inst.getOpcode()).operands()[0].OperandType ==
        MCOI::OPERAND_PCREL) {
      int64_t Imm = Inst.getOperand(0).getImm();
      Target = Addr + Size + Imm;
      return true;
    } else {
      int64_t Imm = Inst.getOperand(0).getImm();

      // Skip case where immediate is 0 as that occurs in file that isn't linked
      // and the branch target inferred would be wrong.
      if (Imm == 0)
        return false;

      Target = Imm;
      return true;
    }
  }
};

} // end anonymous namespace

static MCInstrAnalysis *createE32CInstrAnalysis(const MCInstrInfo *Info) {
  return new E32CMCInstrAnalysis(Info);
}

extern "C" LLVM_EXTERNAL_VISIBILITY void LLVMInitializeE32CTargetMC() {
  // Register the MC asm info.
  RegisterMCAsmInfo<E32CMCAsmInfo> X(getTheE32CTarget());

  // Register the MC instruction info.
  TargetRegistry::RegisterMCInstrInfo(getTheE32CTarget(),
                                      createE32CMCInstrInfo);

  // Register the MC register info.
  TargetRegistry::RegisterMCRegInfo(getTheE32CTarget(),
                                    createE32CMCRegisterInfo);

  // Register the MC subtarget info.
  TargetRegistry::RegisterMCSubtargetInfo(getTheE32CTarget(),
                                          createE32CMCSubtargetInfo);

  // Register the MC code emitter
  TargetRegistry::RegisterMCCodeEmitter(getTheE32CTarget(),
                                        createE32CMCCodeEmitter);

  // Register the ASM Backend
  TargetRegistry::RegisterMCAsmBackend(getTheE32CTarget(),
                                       createE32CAsmBackend);

  // Register the MCInstPrinter.
  TargetRegistry::RegisterMCInstPrinter(getTheE32CTarget(),
                                        createE32CMCInstPrinter);

  // Register the ELF streamer.
  TargetRegistry::RegisterELFStreamer(getTheE32CTarget(), createMCStreamer);

  // Register the MC relocation info.
  TargetRegistry::RegisterMCRelocationInfo(getTheE32CTarget(),
                                           createE32CElfRelocation);

  // Register the MC instruction analyzer.
  TargetRegistry::RegisterMCInstrAnalysis(getTheE32CTarget(),
                                          createE32CInstrAnalysis);
}
