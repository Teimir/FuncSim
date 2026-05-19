add_llvm_component_group(E32C)

set(LLVM_TARGET_DEFINITIONS E32C.td)

tablegen(LLVM E32CGenAsmMatcher.inc -gen-asm-matcher)
tablegen(LLVM E32CGenAsmWriter.inc -gen-asm-writer)
tablegen(LLVM E32CGenCallingConv.inc -gen-callingconv)
tablegen(LLVM E32CGenDAGISel.inc -gen-dag-isel)
tablegen(LLVM E32CGenDisassemblerTables.inc -gen-disassembler)
tablegen(LLVM E32CGenInstrInfo.inc -gen-instr-info)
tablegen(LLVM E32CGenMCCodeEmitter.inc -gen-emitter)
tablegen(LLVM E32CGenRegisterInfo.inc -gen-register-info)
tablegen(LLVM E32CGenSubtargetInfo.inc -gen-subtarget)

add_public_tablegen_target(E32CCommonTableGen)

add_llvm_target(E32CCodeGen
  E32CAsmPrinter.cpp
  E32CDelaySlotFiller.cpp
  E32CFrameLowering.cpp
  E32CInstrInfo.cpp
  E32CISelDAGToDAG.cpp
  E32CISelLowering.cpp
  E32CMachineFunctionInfo.cpp
  E32CMCInstLower.cpp
  E32CMemAluCombiner.cpp
  E32CRegisterInfo.cpp
  E32CSelectionDAGInfo.cpp
  E32CSubtarget.cpp
  E32CTargetMachine.cpp
  E32CTargetObjectFile.cpp

  LINK_COMPONENTS
  Analysis
  AsmPrinter
  CodeGen
  CodeGenTypes
  Core
  E32CAsmParser
  E32CDesc
  E32CInfo
  MC
  SelectionDAG
  Support
  Target
  TargetParser
  TransformUtils

  ADD_TO_COMPONENT
  E32C
  )

add_subdirectory(AsmParser)
add_subdirectory(Disassembler)
add_subdirectory(MCTargetDesc)
add_subdirectory(TargetInfo)
