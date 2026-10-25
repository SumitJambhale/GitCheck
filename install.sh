#!/usr/bin/env bash
set -e

# GitCheck 1-Line Installer
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/SumitJambhale/GitCheck/main/install.sh | bash

REPO="SumitJambhale/GitCheck"
BIN_NAME="git-check"

# Visual formatting
BOLD="\033[1m"
GREEN="\033[32m"
CYAN="\033[36m"
YELLOW="\033[33m"
RED="\033[31m"
RESET="\033[0m"

echo -e "${CYAN}${BOLD}"
echo "=================================================="
echo "          Installing GitCheck CLI                "
echo "=================================================="
echo -e "${RESET}"

# 1. Detect Operating System
OS="$(uname -s)"
case "${OS}" in
  Darwin*)
    OS_TYPE="darwin"
    ;;
  Linux*)
    OS_TYPE="linux"
    ;;
  *)
    echo -e "${RED}Error: Unsupported operating system: ${OS}${RESET}"
    echo "For Windows, use the PowerShell installer: install.ps1"
    exit 1
    ;;
esac

# 2. Detect CPU Architecture
ARCH="$(uname -m)"
case "${ARCH}" in
  x86_64|amd64)
    ARCH_TYPE="amd64"
    ;;
  arm64|aarch64)
    ARCH_TYPE="arm64"
    ;;
  *)
    echo -e "${RED}Error: Unsupported architecture: ${ARCH}${RESET}"
    exit 1
    ;;
esac

ASSET_NAME="git-check-${OS_TYPE}-${ARCH_TYPE}"
echo -e "Detected platform: ${BOLD}${OS_TYPE}/${ARCH_TYPE}${RESET} (Target: ${ASSET_NAME})"

# 3. Resolve Target Version
if [ -z "${GITCHECK_VERSION}" ]; then
  echo "Checking latest release on GitHub..."
  LATEST_RELEASE_URL="https://api.github.com/repos/${REPO}/releases/latest"
  TAG=$(curl -sSL "${LATEST_RELEASE_URL}" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
  
  if [ -z "${TAG}" ] || [ "${TAG}" = "null" ]; then
    echo -e "${YELLOW}Notice: Could not query latest GitHub tag automatically. Falling back to 'v0.1.0'${RESET}"
    TAG="v0.1.0"
  fi
else
  TAG="${GITCHECK_VERSION}"
fi

echo -e "Installing version: ${GREEN}${BOLD}${TAG}${RESET}"

DOWNLOAD_URL="https://github.com/${REPO}/releases/download/${TAG}/${ASSET_NAME}"
TMP_DIR=$(mktemp -d)
TMP_BIN="${TMP_DIR}/${BIN_NAME}"

# Clean up temporary directory on exit
trap 'rm -rf "${TMP_DIR}"' EXIT

# 4. Download Binary
echo -e "Downloading from: ${DOWNLOAD_URL}..."
if ! curl -fSL --progress-bar "${DOWNLOAD_URL}" -o "${TMP_BIN}"; then
  echo -e "${RED}Failed to download binary from ${DOWNLOAD_URL}.${RESET}"
  echo -e "Please check if release ${TAG} contains asset ${ASSET_NAME} at:"
  echo -e "https://github.com/${REPO}/releases"
  exit 1
fi

chmod +x "${TMP_BIN}"

# 5. Choose Install Destination
INSTALL_DIR="/usr/local/bin"
USE_SUDO=0

if [ -w "${INSTALL_DIR}" ]; then
  DEST="${INSTALL_DIR}/${BIN_NAME}"
elif sudo -n true 2>/dev/null; then
  DEST="${INSTALL_DIR}/${BIN_NAME}"
  USE_SUDO=1
else
  INSTALL_DIR="${HOME}/.local/bin"
  mkdir -p "${INSTALL_DIR}"
  DEST="${INSTALL_DIR}/${BIN_NAME}"
fi

echo -e "Installing to ${BOLD}${DEST}${RESET}..."

if [ "${USE_SUDO}" -eq 1 ]; then
  sudo cp "${TMP_BIN}" "${DEST}"
  sudo chmod +x "${DEST}"
else
  cp "${TMP_BIN}" "${DEST}"
  chmod +x "${DEST}"
fi

# 6. Verify Installation
echo ""
echo -e "${GREEN}${BOLD}✔ GitCheck CLI installed successfully!${RESET}"

# Check if INSTALL_DIR is in PATH
case ":$PATH:" in
  *":${INSTALL_DIR}:"*) ;;
  *)
    echo -e "${YELLOW}Warning: ${INSTALL_DIR} is not in your \$PATH.${RESET}"
    echo -e "Add it to your shell profile by running:"
    echo -e "  echo 'export PATH=\"${INSTALL_DIR}:\$PATH\"' >> ~/.zshrc   # for zsh"
    echo -e "  echo 'export PATH=\"${INSTALL_DIR}:\$PATH\"' >> ~/.bashrc  # for bash"
    echo ""
    ;;
esac

echo -e "Quick Start:"
echo -e "  1. Set your LLM key: ${CYAN}export GEMINI_API_KEY=\"your-key\"${RESET}"
echo -e "  2. Go to any Git project: ${CYAN}cd /path/to/repo${RESET}"
echo -e "  3. Install the pre-commit gate: ${CYAN}git-check install-hook${RESET}"
echo -e "  4. Test verification manually: ${CYAN}git-check run${RESET}"
echo ""
