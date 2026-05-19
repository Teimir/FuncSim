//===-- E32CELFObjectWriter.cpp - E32C ELF Writer -----------------------===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#include "MCTargetDesc/E32CBaseInfo.h"
#include "MCTargetDesc/E32CFixupKinds.h"
#include "llvm/BinaryFormat/ELF.h"
#include "llvm/MC/MCELFObjectWriter.h"
#include "llvm/MC/MCObjectWriter.h"
#include "llvm/Support/ErrorHandling.h"

using namespace llvm;

// Private E32C ELF reloc types (EM_E32C); not yet in upstream llvm/BinaryFormat/ELF.h.
namespace E32CElf {
enum : unsigned {
  R_E32C_NONE = 0,
  R_E32C_32 = 1,
  R_E32C_HI16 = 2,
  R_E32C_LO16 = 3,
  R_E32C_21 = 4,
  R_E32C_21_F = 5,
  R_E32C_25 = 6,
};
} // namespace E32CElf

namespace {

class E32CELFObjectWriter : public MCELFObjectTargetWriter {
public:
  explicit E32CELFObjectWriter(uint8_t OSABI);

  ~E32CELFObjectWriter() override = default;

protected:
  unsigned getRelocType(MCContext &Ctx, const MCValue &Target,
                        const MCFixup &Fixup, bool IsPCRel) const override;
  bool needsRelocateWithSymbol(const MCValue &Val, const MCSymbol &Sym,
                               unsigned Type) const override;
};

} // end anonymous namespace

E32CELFObjectWriter::E32CELFObjectWriter(uint8_t OSABI)
    : MCELFObjectTargetWriter(/*Is64Bit_=*/false, OSABI, ELF::EM_E32C,
                              /*HasRelocationAddend_=*/true) {}

unsigned E32CELFObjectWriter::getRelocType(MCContext & /*Ctx*/,
                                            const MCValue & /*Target*/,
                                            const MCFixup &Fixup,
                                            bool /*IsPCRel*/) const {
  unsigned Type;
  unsigned Kind = static_cast<unsigned>(Fixup.getKind());
  switch (Kind) {
  case E32C::FIXUP_E32C_21:
    Type = E32CElf::R_E32C_21;
    break;
  case E32C::FIXUP_E32C_21_F:
    Type = E32CElf::R_E32C_21_F;
    break;
  case E32C::FIXUP_E32C_25:
    Type = E32CElf::R_E32C_25;
    break;
  case E32C::FIXUP_E32C_32:
  case FK_Data_4:
    Type = E32CElf::R_E32C_32;
    break;
  case E32C::FIXUP_E32C_HI16:
    Type = E32CElf::R_E32C_HI16;
    break;
  case E32C::FIXUP_E32C_LO16:
    Type = E32CElf::R_E32C_LO16;
    break;
  case E32C::FIXUP_E32C_NONE:
    Type = E32CElf::R_E32C_NONE;
    break;

  default:
    llvm_unreachable("Invalid fixup kind!");
  }
  return Type;
}

bool E32CELFObjectWriter::needsRelocateWithSymbol(const MCValue &,
                                                   const MCSymbol &,
                                                   unsigned Type) const {
  switch (Type) {
  case E32CElf::R_E32C_21:
  case E32CElf::R_E32C_21_F:
  case E32CElf::R_E32C_25:
  case E32CElf::R_E32C_32:
  case E32CElf::R_E32C_HI16:
    return true;
  default:
    return false;
  }
}

std::unique_ptr<MCObjectTargetWriter>
llvm::createE32CELFObjectWriter(uint8_t OSABI) {
  return std::make_unique<E32CELFObjectWriter>(OSABI);
}
