//===-- E32CMCCodeEmitter.cpp - Convert E32C code to machine code -------===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//
//
// This file implements the E32CMCCodeEmitter class.
//
//===----------------------------------------------------------------------===//

#include "E32CAluCode.h"
#include "MCTargetDesc/E32CBaseInfo.h"
#include "MCTargetDesc/E32CFixupKinds.h"
#include "MCTargetDesc/E32CMCExpr.h"
#include "llvm/ADT/SmallVector.h"
#include "llvm/ADT/Statistic.h"
#include "llvm/MC/MCCodeEmitter.h"
#include "llvm/MC/MCExpr.h"
#include "llvm/MC/MCFixup.h"
#include "llvm/MC/MCInst.h"
#include "llvm/MC/MCInstrInfo.h"
#include "llvm/MC/MCRegisterInfo.h"
#include "llvm/MC/MCSubtargetInfo.h"
#include "llvm/Support/Casting.h"
#include "llvm/Support/EndianStream.h"
#include "llvm/Support/raw_ostream.h"
#include <cassert>
#include <cstdint>

#define DEBUG_TYPE "mccodeemitter"

STATISTIC(MCNumEmitted, "Number of MC instructions emitted");

namespace llvm {

namespace {

class E32CMCCodeEmitter : public MCCodeEmitter {
public:
  E32CMCCodeEmitter(const MCInstrInfo &MCII, MCContext &C) {}
  E32CMCCodeEmitter(const E32CMCCodeEmitter &) = delete;
  void operator=(const E32CMCCodeEmitter &) = delete;
  ~E32CMCCodeEmitter() override = default;

  // The functions below are called by TableGen generated functions for getting
  // the binary encoding of instructions/opereands.

  // getBinaryCodeForInstr - TableGen'erated function for getting the
  // binary encoding for an instruction.
  uint64_t getBinaryCodeForInstr(const MCInst &Inst,
                                 SmallVectorImpl<MCFixup> &Fixups,
                                 const MCSubtargetInfo &SubtargetInfo) const;

  // getMachineOpValue - Return binary encoding of operand. If the machine
  // operand requires relocation, record the relocation and return zero.
  unsigned getMachineOpValue(const MCInst &Inst, const MCOperand &MCOp,
                             SmallVectorImpl<MCFixup> &Fixups,
                             const MCSubtargetInfo &SubtargetInfo) const;

  unsigned getRiMemoryOpValue(const MCInst &Inst, unsigned OpNo,
                              SmallVectorImpl<MCFixup> &Fixups,
                              const MCSubtargetInfo &SubtargetInfo) const;

  unsigned getRrMemoryOpValue(const MCInst &Inst, unsigned OpNo,
                              SmallVectorImpl<MCFixup> &Fixups,
                              const MCSubtargetInfo &SubtargetInfo) const;

  unsigned getSplsOpValue(const MCInst &Inst, unsigned OpNo,
                          SmallVectorImpl<MCFixup> &Fixups,
                          const MCSubtargetInfo &SubtargetInfo) const;

  unsigned getBranchTargetOpValue(const MCInst &Inst, unsigned OpNo,
                                  SmallVectorImpl<MCFixup> &Fixups,
                                  const MCSubtargetInfo &SubtargetInfo) const;

  void encodeInstruction(const MCInst &Inst, SmallVectorImpl<char> &CB,
                         SmallVectorImpl<MCFixup> &Fixups,
                         const MCSubtargetInfo &SubtargetInfo) const override;

  unsigned adjustPqBitsRmAndRrm(const MCInst &Inst, unsigned Value,
                                const MCSubtargetInfo &STI) const;

  unsigned adjustPqBitsSpls(const MCInst &Inst, unsigned Value,
                            const MCSubtargetInfo &STI) const;
};

} // end anonymous namespace

static E32C::Fixups FixupKind(const MCExpr *Expr) {
  if (isa<MCSymbolRefExpr>(Expr))
    return E32C::FIXUP_E32C_21;
  if (const E32CMCExpr *McExpr = dyn_cast<E32CMCExpr>(Expr)) {
    E32CMCExpr::VariantKind ExprKind = McExpr->getKind();
    switch (ExprKind) {
    case E32CMCExpr::VK_E32C_None:
      return E32C::FIXUP_E32C_21;
    case E32CMCExpr::VK_E32C_ABS_HI:
      return E32C::FIXUP_E32C_HI16;
    case E32CMCExpr::VK_E32C_ABS_LO:
      return E32C::FIXUP_E32C_LO16;
    }
  }
  return E32C::Fixups(0);
}

// getMachineOpValue - Return binary encoding of operand. If the machine
// operand requires relocation, record the relocation and return zero.
unsigned E32CMCCodeEmitter::getMachineOpValue(
    const MCInst &Inst, const MCOperand &MCOp, SmallVectorImpl<MCFixup> &Fixups,
    const MCSubtargetInfo &SubtargetInfo) const {
  if (MCOp.isReg())
    return getE32CRegisterNumbering(MCOp.getReg());
  if (MCOp.isImm())
    return static_cast<unsigned>(MCOp.getImm());

  // MCOp must be an expression
  assert(MCOp.isExpr());
  const MCExpr *Expr = MCOp.getExpr();

  // Extract the symbolic reference side of a binary expression.
  if (Expr->getKind() == MCExpr::Binary) {
    const MCBinaryExpr *BinaryExpr = static_cast<const MCBinaryExpr *>(Expr);
    Expr = BinaryExpr->getLHS();
  }

  assert(isa<E32CMCExpr>(Expr) || Expr->getKind() == MCExpr::SymbolRef);
  // Push fixup (all info is contained within)
  Fixups.push_back(
      MCFixup::create(0, MCOp.getExpr(), MCFixupKind(FixupKind(Expr))));
  return 0;
}

// Helper function to adjust P and Q bits on load and store instructions.
static unsigned adjustPqBits(const MCInst &Inst, unsigned Value,
                             unsigned PBitShift, unsigned QBitShift) {
  const MCOperand AluOp = Inst.getOperand(3);
  unsigned AluCode = AluOp.getImm();

  // Set the P bit to one iff the immediate is nonzero and not a post-op
  // instruction.
  const MCOperand Op2 = Inst.getOperand(2);
  Value &= ~(1 << PBitShift);
  if (!LPAC::isPostOp(AluCode) &&
      ((Op2.isImm() && Op2.getImm() != 0) ||
       (Op2.isReg() && Op2.getReg() != E32C::R0) || (Op2.isExpr())))
    Value |= (1 << PBitShift);

  // Set the Q bit to one iff it is a post- or pre-op instruction.
  assert(Inst.getOperand(0).isReg() && Inst.getOperand(1).isReg() &&
         "Expected register operand.");
  Value &= ~(1 << QBitShift);
  if (LPAC::modifiesOp(AluCode) && ((Op2.isImm() && Op2.getImm() != 0) ||
                                    (Op2.isReg() && Op2.getReg() != E32C::R0)))
    Value |= (1 << QBitShift);

  return Value;
}

unsigned
E32CMCCodeEmitter::adjustPqBitsRmAndRrm(const MCInst &Inst, unsigned Value,
                                         const MCSubtargetInfo &STI) const {
  return adjustPqBits(Inst, Value, 17, 16);
}

unsigned
E32CMCCodeEmitter::adjustPqBitsSpls(const MCInst &Inst, unsigned Value,
                                     const MCSubtargetInfo &STI) const {
  return adjustPqBits(Inst, Value, 11, 10);
}

void E32CMCCodeEmitter::encodeInstruction(
    const MCInst &Inst, SmallVectorImpl<char> &CB,
    SmallVectorImpl<MCFixup> &Fixups,
    const MCSubtargetInfo &SubtargetInfo) const {
  // Get instruction encoding and emit it
  unsigned Value = getBinaryCodeForInstr(Inst, Fixups, SubtargetInfo);
  ++MCNumEmitted; // Keep track of the number of emitted insns.

  support::endian::write<uint32_t>(CB, Value, llvm::endianness::big);
}

// Encode E32C Memory Operand
unsigned E32CMCCodeEmitter::getRiMemoryOpValue(
    const MCInst &Inst, unsigned OpNo, SmallVectorImpl<MCFixup> &Fixups,
    const MCSubtargetInfo &SubtargetInfo) const {
  unsigned Encoding;
  const MCOperand Op1 = Inst.getOperand(OpNo + 0);
  const MCOperand Op2 = Inst.getOperand(OpNo + 1);
  const MCOperand AluOp = Inst.getOperand(OpNo + 2);

  assert(Op1.isReg() && "First operand is not register.");
  assert((Op2.isImm() || Op2.isExpr()) &&
         "Second operand is neither an immediate nor an expression.");
  assert((LPAC::getAluOp(AluOp.getImm()) == LPAC::ADD) &&
         "Register immediate only supports addition operator");

  Encoding = (getE32CRegisterNumbering(Op1.getReg()) << 18);
  if (Op2.isImm()) {
    assert(isInt<16>(Op2.getImm()) &&
           "Constant value truncated (limited to 16-bit)");

    Encoding |= (Op2.getImm() & 0xffff);
    if (Op2.getImm() != 0) {
      if (LPAC::isPreOp(AluOp.getImm()))
        Encoding |= (0x3 << 16);
      if (LPAC::isPostOp(AluOp.getImm()))
        Encoding |= (0x1 << 16);
    }
  } else
    getMachineOpValue(Inst, Op2, Fixups, SubtargetInfo);

  return Encoding;
}

unsigned E32CMCCodeEmitter::getRrMemoryOpValue(
    const MCInst &Inst, unsigned OpNo, SmallVectorImpl<MCFixup> &Fixups,
    const MCSubtargetInfo &SubtargetInfo) const {
  unsigned Encoding;
  const MCOperand Op1 = Inst.getOperand(OpNo + 0);
  const MCOperand Op2 = Inst.getOperand(OpNo + 1);
  const MCOperand AluMCOp = Inst.getOperand(OpNo + 2);

  assert(Op1.isReg() && "First operand is not register.");
  Encoding = (getE32CRegisterNumbering(Op1.getReg()) << 15);
  assert(Op2.isReg() && "Second operand is not register.");
  Encoding |= (getE32CRegisterNumbering(Op2.getReg()) << 10);

  assert(AluMCOp.isImm() && "Third operator is not immediate.");
  // Set BBB
  unsigned AluOp = AluMCOp.getImm();
  Encoding |= LPAC::encodeE32CAluCode(AluOp) << 5;
  // Set P and Q
  if (LPAC::isPreOp(AluOp))
    Encoding |= (0x3 << 8);
  if (LPAC::isPostOp(AluOp))
    Encoding |= (0x1 << 8);
  // Set JJJJ
  switch (LPAC::getAluOp(AluOp)) {
  case LPAC::SHL:
  case LPAC::SRL:
    Encoding |= 0x10;
    break;
  case LPAC::SRA:
    Encoding |= 0x18;
    break;
  default:
    break;
  }

  return Encoding;
}

unsigned
E32CMCCodeEmitter::getSplsOpValue(const MCInst &Inst, unsigned OpNo,
                                   SmallVectorImpl<MCFixup> &Fixups,
                                   const MCSubtargetInfo &SubtargetInfo) const {
  unsigned Encoding;
  const MCOperand Op1 = Inst.getOperand(OpNo + 0);
  const MCOperand Op2 = Inst.getOperand(OpNo + 1);
  const MCOperand AluOp = Inst.getOperand(OpNo + 2);

  assert(Op1.isReg() && "First operand is not register.");
  assert((Op2.isImm() || Op2.isExpr()) &&
         "Second operand is neither an immediate nor an expression.");
  assert((LPAC::getAluOp(AluOp.getImm()) == LPAC::ADD) &&
         "Register immediate only supports addition operator");

  Encoding = (getE32CRegisterNumbering(Op1.getReg()) << 12);
  if (Op2.isImm()) {
    assert(isInt<10>(Op2.getImm()) &&
           "Constant value truncated (limited to 10-bit)");

    Encoding |= (Op2.getImm() & 0x3ff);
    if (Op2.getImm() != 0) {
      if (LPAC::isPreOp(AluOp.getImm()))
        Encoding |= (0x3 << 10);
      if (LPAC::isPostOp(AluOp.getImm()))
        Encoding |= (0x1 << 10);
    }
  } else
    getMachineOpValue(Inst, Op2, Fixups, SubtargetInfo);

  return Encoding;
}

unsigned E32CMCCodeEmitter::getBranchTargetOpValue(
    const MCInst &Inst, unsigned OpNo, SmallVectorImpl<MCFixup> &Fixups,
    const MCSubtargetInfo &SubtargetInfo) const {
  const MCOperand &MCOp = Inst.getOperand(OpNo);
  if (MCOp.isReg() || MCOp.isImm())
    return getMachineOpValue(Inst, MCOp, Fixups, SubtargetInfo);

  Fixups.push_back(MCFixup::create(
      0, MCOp.getExpr(), static_cast<MCFixupKind>(E32C::FIXUP_E32C_25)));

  return 0;
}

#include "E32CGenMCCodeEmitter.inc"

} // end namespace llvm

llvm::MCCodeEmitter *
llvm::createE32CMCCodeEmitter(const MCInstrInfo &InstrInfo,
                               MCContext &context) {
  return new E32CMCCodeEmitter(InstrInfo, context);
}
