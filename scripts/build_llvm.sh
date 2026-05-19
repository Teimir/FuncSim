#!/usr/bin/env bash
# Build LLVM with experimental E32C target (llvm-mc, llc, llvm-objdump, …).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${ROOT}/toolchain/llvm-project/llvm"
BUILD="${ROOT}/toolchain/llvm-build-e32c"
TAG="${LLVM_TAG:-llvmorg-19.1.7}"
BUILD_E32C="${BUILD_E32C:-1}"

if [[ ! -d "${SRC}" ]]; then
  mkdir -p "${ROOT}/toolchain"
  git clone --depth 1 --branch "${TAG}" https://github.com/llvm/llvm-project.git "${ROOT}/toolchain/llvm-project"
fi

if [[ "${BUILD_E32C}" == "1" ]]; then
  bash "${ROOT}/scripts/install_e32c_llvm_target.sh"
  TARGETS="X86"
  EXPERIMENTAL="E32C"
else
  TARGETS="${LLVM_TARGETS_TO_BUILD:-X86}"
  EXPERIMENTAL=""
fi

mkdir -p "${BUILD}"
cd "${BUILD}"
CMAKE_ARGS=(
  -G Ninja
  "../llvm-project/llvm"
  -DCMAKE_BUILD_TYPE=Release
  -DCMAKE_C_COMPILER=gcc
  -DCMAKE_CXX_COMPILER=g++
  -DLLVM_TARGETS_TO_BUILD="${TARGETS}"
)
if [[ -n "${EXPERIMENTAL}" ]]; then
  CMAKE_ARGS+=(-DLLVM_EXPERIMENTAL_TARGETS_TO_BUILD="${EXPERIMENTAL}")
fi

cmake "${CMAKE_ARGS[@]}"
ninja -j"$(nproc)" llvm-mc llc llvm-as llvm-dis llvm-config llvm-objdump

BIN="${BUILD}/bin"
if [[ "${BUILD_E32C}" == "1" ]]; then
  echo "Smoke: llvm-mc triple"
  "${BIN}/llvm-mc" --version | head -1
  if [[ -f "${ROOT}/examples/boot_smoke.asm" ]]; then
    # Preprocess MOV -> ADDI like Python pseudo (minimal for smoke)
    TMP="$(mktemp)"
    sed -E 's/^MOV[[:space:]]+([0-9]+)[[:space:]]+([^[:space:]]+)/ADDI 0 \1 \2/I' \
      "${ROOT}/examples/boot_smoke.asm" > "${TMP}"
    "${BIN}/llvm-mc" -triple=e32c-unknown-elf -filetype=obj "${TMP}" -o /dev/null && \
      echo "llvm-mc assembled boot_smoke (MOV→ADDI) OK" || echo "llvm-mc smoke failed (expected until matcher complete)"
    rm -f "${TMP}"
  fi
fi

echo "LLVM tools in ${BIN}"
