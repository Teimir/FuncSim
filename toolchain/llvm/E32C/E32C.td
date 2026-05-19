//===-- E32C.td - E32C target description -----------------------*- tablegen -*-===//

include "llvm/Target/Target.td"

def FeatureE32C : SubtargetFeature<"e32c", "IsE32C", "true", "E32C ISA">;

include "E32CSchedule.td"

def : ProcessorModel<"generic", E32CSchedModel, [FeatureE32C]>;
def : ProcessorModel<"e32c", E32CSchedModel, [FeatureE32C]>;

include "E32CRegisterInfo.td"
include "E32CInstrFormats.td"
include "E32CInstrInfo.generated.td"

def E32CInstrInfo : InstrInfo;

def E32CInstPrinter : AsmWriter {
  string AsmWriterClassName = "InstPrinter";
  bit isMCAsmWriter = 1;
}

def E32C : Target {
  let InstructionSet = E32CInstrInfo;
  let AssemblyWriters = [E32CInstPrinter];
}
