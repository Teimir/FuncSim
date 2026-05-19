add_llvm_component_library(LLVME32CInfo
  E32CTargetInfo.cpp

  LINK_COMPONENTS
  MC
  Support

  ADD_TO_COMPONENT
  E32C
  )
