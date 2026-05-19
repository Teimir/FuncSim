include_directories( ${CMAKE_CURRENT_BINARY_DIR}/.. ${CMAKE_CURRENT_SOURCE_DIR}/.. )

add_llvm_component_library(LLVME32CAsmParser
  E32CAsmParser.cpp

  LINK_COMPONENTS
  CodeGenTypes
  E32CDesc
  E32CInfo
  MC
  MCParser
  Support

  ADD_TO_COMPONENT
  E32C
  )

add_dependencies( LLVME32CAsmParser E32CCommonTableGen )
