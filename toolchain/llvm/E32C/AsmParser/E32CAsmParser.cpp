//===-- E32CAsmParser.cpp - E32C assembly parser -------------------===//
//
// Minimal asm parser for E32C (operand order matches Python assembler).
//
//===----------------------------------------------------------------------===//

#include "MCTargetDesc/E32CInstPrinter.h"
#include "MCTargetDesc/E32CMCTargetDesc.h"
#include "TargetInfo/E32CTargetInfo.h"
#include "llvm/MC/MCContext.h"
#include "llvm/MC/MCExpr.h"
#include "llvm/MC/MCInst.h"
#include "llvm/MC/MCParser/MCAsmLexer.h"
#include "llvm/MC/MCParser/MCParsedAsmOperand.h"
#include "llvm/MC/MCParser/MCTargetAsmParser.h"
#include "llvm/MC/MCStreamer.h"
#include "llvm/MC/MCSubtargetInfo.h"
#include "llvm/MC/TargetRegistry.h"
#include "llvm/Support/Casting.h"
#include "llvm/Support/SMLoc.h"

using namespace llvm;

namespace {

struct E32COperand : public MCParsedAsmOperand {
  enum KindTy { Token, Register, Immediate } Kind;
  SMLoc StartLoc, EndLoc;
  StringRef Tok;
  unsigned RegNum = 0;
  const MCExpr *ImmExpr = nullptr;

  explicit E32COperand(KindTy K) : Kind(K) {}

  static std::unique_ptr<E32COperand> createToken(StringRef T, SMLoc S) {
    auto Op = std::make_unique<E32COperand>(Token);
    Op->Tok = T;
    Op->StartLoc = S;
    Op->EndLoc = S;
    return Op;
  }

  static std::unique_ptr<E32COperand> createReg(unsigned R, SMLoc S, SMLoc E) {
    auto Op = std::make_unique<E32COperand>(Register);
    Op->RegNum = R;
    Op->StartLoc = S;
    Op->EndLoc = E;
    return Op;
  }

  static std::unique_ptr<E32COperand> createImm(const MCExpr *Expr, SMLoc S,
                                                SMLoc E) {
    auto Op = std::make_unique<E32COperand>(Immediate);
    Op->ImmExpr = Expr;
    Op->StartLoc = S;
    Op->EndLoc = E;
    return Op;
  }

  bool isToken() const override { return Kind == Token; }
  bool isReg() const override { return Kind == Register; }
  bool isImm() const override { return Kind == Immediate; }
  bool isMem() const override { return false; }

  SMLoc getStartLoc() const override { return StartLoc; }
  SMLoc getEndLoc() const override { return EndLoc; }

  StringRef getToken() const {
    assert(Kind == Token);
    return Tok;
  }

  MCRegister getReg() const override {
    assert(Kind == Register);
    return MCRegister(RegNum);
  }

  const MCExpr *getImm() const {
    assert(Kind == Immediate);
    return ImmExpr;
  }

  void addRegOperands(MCInst &Inst, unsigned N) const {
    assert(Kind == Register && N == 1);
    Inst.addOperand(MCOperand::createReg(getReg().id()));
  }

  void addImmOperands(MCInst &Inst, unsigned N) const {
    assert(Kind == Immediate && N == 1);
    if (const auto *CE = dyn_cast<MCConstantExpr>(ImmExpr))
      Inst.addOperand(MCOperand::createImm(CE->getValue()));
    else
      Inst.addOperand(MCOperand::createExpr(ImmExpr));
  }

  void print(raw_ostream &O) const override { O << "E32COperand"; }
};

class E32CAsmParser : public MCTargetAsmParser {
  MCAsmParser &Parser;

#define GET_ASSEMBLER_HEADER
#include "E32CGenAsmMatcher.inc"

public:
  E32CAsmParser(const MCSubtargetInfo &STI, MCAsmParser &P, const MCInstrInfo &MII,
                const MCTargetOptions &Options)
      : MCTargetAsmParser(Options, STI, MII), Parser(P) {
    setAvailableFeatures(ComputeAvailableFeatures(STI.getFeatureBits()));
  }

  MCAsmParser &getParser() const { return Parser; }
  MCAsmLexer &getLexer() const { return Parser.getLexer(); }

  bool MatchAndEmitInstruction(SMLoc IDLoc, unsigned &Opcode, OperandVector &Operands,
                               MCStreamer &Out, uint64_t &ErrorInfo,
                               bool MatchingInlineAsm) override;

  bool ParseInstruction(ParseInstructionInfo &Info, StringRef Name, SMLoc NameLoc,
                        OperandVector &Operands) override;

  bool parseRegister(MCRegister &Reg, SMLoc &StartLoc, SMLoc &EndLoc) override;
  ParseStatus tryParseRegister(MCRegister &Reg, SMLoc &StartLoc,
                               SMLoc &EndLoc) override;

private:
  bool parseOperand(OperandVector &Operands);
};

static MCRegister e32cRegFromIndex(unsigned N) {
  static const MCRegister Table[] = {
      E32C::R0,  E32C::R1,  E32C::R2,  E32C::R3,  E32C::R4,  E32C::R5,
      E32C::R6,  E32C::R7,  E32C::R8,  E32C::R9,  E32C::R10, E32C::R11,
      E32C::R12, E32C::R13, E32C::R14, E32C::R15, E32C::R16, E32C::R17,
      E32C::R18, E32C::R19, E32C::R20, E32C::R21, E32C::R22, E32C::R23,
      E32C::R24, E32C::R25, E32C::R26, E32C::R27, E32C::R28, E32C::R29,
      E32C::SP,  E32C::PC};
  return Table[N];
}

bool E32CAsmParser::parseRegister(MCRegister &Reg, SMLoc &StartLoc, SMLoc &EndLoc) {
  if (!getLexer().is(AsmToken::Identifier))
    return true;
  StringRef Name = Parser.getTok().getString();
  if (Name.starts_with_insensitive("r")) {
    unsigned N;
    if (Name.drop_front(1).getAsInteger(10, N) || N > 31)
      return true;
    StartLoc = Parser.getTok().getLoc();
    EndLoc = StartLoc;
    Reg = e32cRegFromIndex(N);
    Parser.Lex();
    return false;
  }
  if (Name.equals_insensitive("sp")) {
    StartLoc = EndLoc = Parser.getTok().getLoc();
    Reg = MCRegister(E32C::SP);
    Parser.Lex();
    return false;
  }
  if (Name.equals_insensitive("pc")) {
    StartLoc = EndLoc = Parser.getTok().getLoc();
    Reg = MCRegister(E32C::PC);
    Parser.Lex();
    return false;
  }
  return true;
}

ParseStatus E32CAsmParser::tryParseRegister(MCRegister &Reg, SMLoc &StartLoc,
                                            SMLoc &EndLoc) {
  return parseRegister(Reg, StartLoc, EndLoc) ? ParseStatus::NoMatch
                                              : ParseStatus::Success;
}

bool E32CAsmParser::parseOperand(OperandVector &Operands) {
  if (getLexer().is(AsmToken::EndOfStatement))
    return true;
  if (getLexer().is(AsmToken::Identifier)) {
    StringRef Name = Parser.getTok().getString();
    if (Name.starts_with_insensitive("r") || Name.equals_insensitive("sp") ||
        Name.equals_insensitive("pc")) {
      SMLoc S = Parser.getTok().getLoc();
      MCRegister Reg;
      SMLoc E;
      if (parseRegister(Reg, S, E))
        return true;
      Operands.push_back(E32COperand::createReg(Reg.id(), S, E));
      return false;
    }
  }
  SMLoc S = Parser.getTok().getLoc();
  const MCExpr *Expr = nullptr;
  if (Parser.parseExpression(Expr))
    return true;
  SMLoc E = S;
  Operands.push_back(E32COperand::createImm(Expr, S, E));
  return false;
}

bool E32CAsmParser::ParseInstruction(ParseInstructionInfo &Info, StringRef Name,
                                     SMLoc NameLoc, OperandVector &Operands) {
  Operands.push_back(E32COperand::createToken(Name, NameLoc));
  while (!getLexer().is(AsmToken::EndOfStatement)) {
    if (parseOperand(Operands))
      return true;
  }
  Parser.Lex();
  return false;
}

bool E32CAsmParser::MatchAndEmitInstruction(SMLoc IDLoc, unsigned &Opcode,
                                            OperandVector &Operands, MCStreamer &Out,
                                            uint64_t &ErrorInfo,
                                            bool MatchingInlineAsm) {
  MCInst Inst;
  unsigned MatchResult =
      MatchInstructionImpl(Operands, Inst, ErrorInfo, MatchingInlineAsm);
  switch (MatchResult) {
  case Match_Success:
    Inst.setLoc(IDLoc);
    Out.emitInstruction(Inst, getSTI());
    return false;
  case Match_MnemonicFail:
    return Error(IDLoc, "invalid instruction");
  case Match_InvalidOperand:
    return Error(IDLoc, "invalid operand for instruction");
  default:
    return Error(IDLoc, "failed to match instruction");
  }
}

} // namespace

#define GET_REGISTER_MATCHER
#define GET_MATCHER_IMPLEMENTATION
#include "E32CGenAsmMatcher.inc"

extern "C" LLVM_EXTERNAL_VISIBILITY void LLVMInitializeE32CAsmParser() {
  RegisterMCAsmParser<E32CAsmParser> X(getTheE32CTarget());
}
