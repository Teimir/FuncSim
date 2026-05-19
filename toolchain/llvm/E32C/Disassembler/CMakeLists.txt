add_llvm_component_library(LLVME32CDisassembler
  E32CDisassembler.cpp

  LINK_COMPONENTS
  CodeGenTypes
  E32CDesc
  E32CInfo
  MC
  MCDisassembler
  Support

  ADD_TO_COMPONENT
  E32C
  )
