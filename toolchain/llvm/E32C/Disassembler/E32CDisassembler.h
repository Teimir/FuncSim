//===- E32CDisassembler.cpp - Disassembler for E32C -----------*- C++ -*-===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//
//
// This file is part of the E32C Disassembler.
//
//===----------------------------------------------------------------------===//

#ifndef LLVM_LIB_TARGET_E32C_DISASSEMBLER_E32CDISASSEMBLER_H
#define LLVM_LIB_TARGET_E32C_DISASSEMBLER_E32CDISASSEMBLER_H

#include "llvm/MC/MCDisassembler/MCDisassembler.h"

#define DEBUG_TYPE "e32c-disassembler"

namespace llvm {

class E32CDisassembler : public MCDisassembler {
public:
  E32CDisassembler(const MCSubtargetInfo &STI, MCContext &Ctx);

  ~E32CDisassembler() override = default;

  // getInstruction - See MCDisassembler.
  MCDisassembler::DecodeStatus
  getInstruction(MCInst &Instr, uint64_t &Size, ArrayRef<uint8_t> Bytes,
                 uint64_t Address, raw_ostream &CStream) const override;
};

} // end namespace llvm

#endif // LLVM_LIB_TARGET_E32C_DISASSEMBLER_E32CDISASSEMBLER_H
