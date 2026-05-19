add_llvm_component_library(LLVME32CDesc
  E32CAsmBackend.cpp
  E32CELFObjectWriter.cpp
  E32CInstPrinter.cpp
  E32CMCAsmInfo.cpp
  E32CMCCodeEmitter.cpp
  E32CMCExpr.cpp
  E32CMCTargetDesc.cpp

  LINK_COMPONENTS
  E32CInfo
  MC
  MCDisassembler
  Support
  TargetParser

  ADD_TO_COMPONENT
  E32C
)
