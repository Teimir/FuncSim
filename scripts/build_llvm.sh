#!/usr/bin/env bash
# Build upstream LLVM (X86) for local experiments. E32C code generation uses Python tools (docs/toolchain.md).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${ROOT}/toolchain/llvm-project/llvm"
BUILD="${ROOT}/toolchain/llvm-build"
TAG="${LLVM_TAG:-llvmorg-19.1.7}"

if [[ ! -d "${SRC}" ]]; then
  mkdir -p "${ROOT}/toolchain"
  git clone --depth 1 --branch "${TAG}" https://github.com/llvm/llvm-project.git "${ROOT}/toolchain/llvm-project"
fi

mkdir -p "${BUILD}"
cd "${BUILD}"
cmake -G Ninja ../llvm-project/llvm \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER=gcc \
  -DCMAKE_CXX_COMPILER=g++ \
  -DLLVM_TARGETS_TO_BUILD="${LLVM_TARGETS_TO_BUILD:-X86}" \
  -DLLVM_ENABLE_PROJECTS=""

ninja -j"$(nproc)" llvm-mc llc opt llvm-as llvm-dis llvm-config FileCheck

echo "LLVM tools in ${BUILD}/bin (not an E32C backend; see docs/toolchain.md)"
