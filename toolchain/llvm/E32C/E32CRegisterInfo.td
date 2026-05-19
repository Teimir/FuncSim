//===-- E32CRegisterInfo.td - E32C registers --------------------*- tablegen -*-===//

def e32cimm : Operand<i32>;

class E32CReg<bits<5> num, string n> : Register<n> {
  field bits<5> Num;
  let Num = num;
  let Namespace = "E32C";
}

foreach i = 0-31 in {
  def R#i : E32CReg<i, "r"#i>, DwarfRegNum<[i]>;
}

def SP : E32CReg<30, "sp">, DwarfRegAlias<R30>;
def PC : E32CReg<31, "pc">, DwarfRegAlias<R31>;

def GPR : RegisterClass<"E32C", [i32], 32, (add (sequence "R%u", 0, 31))>;
