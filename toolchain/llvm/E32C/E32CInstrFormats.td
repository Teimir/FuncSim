//===-- E32CInstrFormats.td - E32C instruction formats ---------*- tablegen -*-===//

class E32CInst<dag outs, dag ins, string asmstr, list<dag> pattern>
    : Instruction {
  field bits<32> Inst;
  field bits<32> SoftFail = 0;
  let Size = 4;
  let Namespace = "E32C";
  let DecoderNamespace = "E32C";
  bits<6> opcode;
  let Inst{31-26} = opcode;
  dag OutOperandList = outs;
  dag InOperandList = ins;
  let AsmString = asmstr;
  let Pattern = pattern;
}

class E32CRrr<bits<6> op> : E32CInst<(outs), (ins GPR:$r1, GPR:$r2, GPR:$res), "", []> {
  bits<5> r1;
  bits<5> r2;
  bits<5> res;
  let Inst{25-21} = r1;
  let Inst{20-16} = r2;
  let Inst{15-11} = res;
  let opcode = op;
}

class E32CLoadStore<bits<6> op>
    : E32CInst<(outs), (ins GPR:$raddr, GPR:$rdest, GPR:$mask, e32cimm:$imm11), "", []> {
  bits<5> raddr;
  bits<5> rdest;
  bits<5> mask;
  bits<11> imm11;
  let Inst{25-21} = raddr;
  let Inst{20-16} = rdest;
  let Inst{15-11} = mask;
  let Inst{10-0} = imm11;
  let opcode = op;
}

class E32CStore<bits<6> op>
    : E32CInst<(outs), (ins GPR:$raddr, GPR:$rdata, GPR:$mask, e32cimm:$imm11), "", []> {
  bits<5> raddr;
  bits<5> rdata;
  bits<5> mask;
  bits<11> imm11;
  let Inst{25-21} = raddr;
  let Inst{20-16} = rdata;
  let Inst{15-11} = mask;
  let Inst{10-0} = imm11;
  let opcode = op;
}

class E32CBranch<bits<6> op>
    : E32CInst<(outs), (ins GPR:$raddr, e32cimm:$imm11), "", []> {
  bits<5> raddr;
  bits<11> imm11;
  let Inst{25-21} = raddr;
  let Inst{10-0} = imm11;
  let opcode = op;
}

class E32CBranchCond<bits<6> op, bits<4> cond_val>
    : E32CInst<(outs), (ins GPR:$raddr, e32cimm:$imm11), "", []> {
  bits<5> raddr;
  bits<11> imm11;
  let Inst{25-22} = cond_val;
  let Inst{21-17} = raddr;
  let Inst{16-6} = imm11;
  let opcode = op;
}

class E32CBranchCondVar<bits<6> op>
    : E32CInst<(outs), (ins e32cimm:$cond, GPR:$raddr, e32cimm:$imm11), "", []> {
  bits<4> cond;
  bits<5> raddr;
  bits<11> imm11;
  let Inst{25-22} = cond;
  let Inst{21-17} = raddr;
  let Inst{16-6} = imm11;
  let opcode = op;
}

class E32CImm16<bits<6> op>
    : E32CInst<(outs), (ins GPR:$r1, GPR:$res, e32cimm:$imm16), "", []> {
  bits<5> r1;
  bits<5> res;
  bits<16> imm16;
  let Inst{25-21} = r1;
  let Inst{20-16} = imm16{15-11};
  let Inst{15-11} = res;
  let Inst{10-0} = imm16{10-0};
  let opcode = op;
}

class E32CMul<bits<6> op>
    : E32CInst<(outs), (ins GPR:$r1, GPR:$r2, GPR:$res, GPR:$resh), "", []> {
  bits<5> r1;
  bits<5> r2;
  bits<5> res;
  bits<5> resh;
  let Inst{25-21} = r1;
  let Inst{20-16} = r2;
  let Inst{15-11} = res;
  let Inst{10-6} = resh;
  let opcode = op;
}

class E32CMla<bits<6> op>
    : E32CInst<(outs), (ins GPR:$r1, GPR:$r2, GPR:$racc, GPR:$res), "", []> {
  bits<5> r1;
  bits<5> r2;
  bits<5> racc;
  bits<5> res;
  let Inst{25-21} = r1;
  let Inst{20-16} = r2;
  let Inst{15-11} = racc;
  let Inst{10-6} = res;
  let opcode = op;
}

class E32CSpr<bits<6> op> : E32CInst<(outs), (ins GPR:$r1, GPR:$spr), "", []> {
  bits<5> r1;
  bits<5> spr;
  let Inst{25-21} = r1;
  let Inst{15-11} = spr;
  let opcode = op;
}

class E32CStrex<bits<6> op>
    : E32CInst<(outs), (ins GPR:$raddr, GPR:$rsrc, GPR:$rstatus, e32cimm:$imm11), "", []> {
  bits<5> raddr;
  bits<5> rsrc;
  bits<5> rstatus;
  bits<11> imm11;
  let Inst{25-21} = raddr;
  let Inst{20-16} = rsrc;
  let Inst{15-11} = rstatus;
  let Inst{10-0} = imm11;
  let opcode = op;
}

class E32CBare<bits<6> op> : E32CInst<(outs), (ins), "", []> {
  let opcode = op;
}

def NOP : E32CInst<(outs), (ins), "NOP", []> {
  let Inst = 0;
  let Size = 4;
  let opcode = 0;
  let hasSideEffects = 0;
  let mayLoad = 0;
  let mayStore = 0;
}

def HALT : E32CInst<(outs), (ins), "HALT", []> {
  let Inst = 0xFFFFFFFF;
  let Size = 4;
  let opcode = 0b111111;
  let hasSideEffects = 1;
}
