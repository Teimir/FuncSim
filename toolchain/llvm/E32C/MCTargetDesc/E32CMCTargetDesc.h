//===-- E32CMCTargetDesc.h - E32C Target Descriptions ---------*- C++ -*-===//
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

#ifndef LLVM_LIB_TARGET_E32C_MCTARGETDESC_E32CMCTARGETDESC_H
#define LLVM_LIB_TARGET_E32C_MCTARGETDESC_E32CMCTARGETDESC_H

#include "llvm/MC/MCRegisterInfo.h"
#include "llvm/MC/MCTargetOptions.h"
#include "llvm/Support/DataTypes.h"

namespace llvm {
class MCAsmBackend;
class MCCodeEmitter;
class MCContext;
class MCInstrInfo;
class MCObjectTargetWriter;
class MCSubtargetInfo;
class Target;

MCCodeEmitter *createE32CMCCodeEmitter(const MCInstrInfo &MCII,
                                        MCContext &Ctx);

MCAsmBackend *createE32CAsmBackend(const Target &T, const MCSubtargetInfo &STI,
                                    const MCRegisterInfo &MRI,
                                    const MCTargetOptions &Options);

std::unique_ptr<MCObjectTargetWriter> createE32CELFObjectWriter(uint8_t OSABI);
} // namespace llvm

// Defines symbolic names for E32C registers.  This defines a mapping from
// register name to register number.
#define GET_REGINFO_ENUM
#include "E32CGenRegisterInfo.inc"

// Defines symbolic names for the E32C instructions.
#define GET_INSTRINFO_ENUM
#define GET_INSTRINFO_MC_HELPER_DECLS
#include "E32CGenInstrInfo.inc"

#define GET_SUBTARGETINFO_ENUM
#include "E32CGenSubtargetInfo.inc"

#endif // LLVM_LIB_TARGET_E32C_MCTARGETDESC_E32CMCTARGETDESC_H
