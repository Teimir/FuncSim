#!/usr/bin/env bash
# Install E32C LLVM backend into llvm-project and patch Triple/ELF/CMake.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LLVM="${ROOT}/toolchain/llvm-project/llvm"
SRC="${ROOT}/toolchain/llvm/E32C"
DEST="${LLVM}/lib/Target/E32C"

if [[ ! -d "${LLVM}" ]]; then
  echo "Run scripts/build_llvm.sh first (clones llvm-project)." >&2
  exit 1
fi

python3 "${ROOT}/scripts/gen_llvm_e32c_td.py"

rm -rf "${DEST}"
mkdir -p "${LLVM}/lib/Target"
cp -a "${SRC}" "${DEST}"

# Experimental target registration
if ! grep -q 'E32C' "${LLVM}/CMakeLists.txt"; then
  sed -i '/^set(LLVM_ALL_EXPERIMENTAL_TARGETS$/,/)$/ {
    /Xtensa$/a\  E32C
  }' "${LLVM}/CMakeLists.txt"
fi

# Triple::e32c
TRIPLE_H="${LLVM}/include/llvm/TargetParser/Triple.h"
if ! grep -q 'e32c,' "${TRIPLE_H}"; then
  sed -i '/lanai,.*Lanai/a\    e32c,           // E32C: 32-bit embedded' "${TRIPLE_H}"
fi

python3 "${ROOT}/scripts/patch_llvm_triple_e32c.py"

ELF_H="${LLVM}/include/llvm/BinaryFormat/ELF.h"
if ! grep -q 'EM_E32C' "${ELF_H}"; then
  sed -i '/EM_LANAI = 244/a\  EM_E32C = 0xE32C,        // E32C 32-bit embedded' "${ELF_H}"
fi

echo "E32C target installed at ${DEST}"
