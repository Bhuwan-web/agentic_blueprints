#!/bin/sh
set -e

PYTHON_VERSION="3.11.13"
INSTALL_PREFIX="/usr/local"

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

if command_exists python3; then
  INSTALLED_VERSION=$(python3 --version | awk '{print $2}')
  echo "Python $INSTALLED_VERSION already installed."
  exit 0
fi

if command_exists apk; then
  echo "Detected apk package manager (Alpine). Installing build dependencies and Python $PYTHON_VERSION from source..."

  apk update
  apk add --no-cache build-base libffi-dev openssl-dev bzip2-dev xz-dev zlib-dev wget

  wget "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz"
  tar -xzf "Python-${PYTHON_VERSION}.tgz"
  cd "Python-${PYTHON_VERSION}"

  ./configure --prefix="$INSTALL_PREFIX" 
  make -j$(nproc)
  make altinstall

  cd ..
  rm -rf "Python-${PYTHON_VERSION}" "Python-${PYTHON_VERSION}.tgz"

  apk add --no-cache py3-pip

  # Create and activate virtual environment in Alpine
  echo "Setting up virtual environment..."
  python3 -m venv /venv
  python3 --version

  echo "Python $PYTHON_VERSION installed on Alpine with virtual environment activated."

elif command_exists apt-get; then
  # install build deps
  apt-get update
  apt-get install -y build-essential libssl-dev libffi-dev libbz2-dev libreadline-dev libsqlite3-dev zlib1g-dev wget

  # download, build, install Python 3.11.13
  wget "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz"
  tar -xzf "Python-${PYTHON_VERSION}.tgz"
  cd "Python-${PYTHON_VERSION}"

  ./configure --prefix="$INSTALL_PREFIX" 
  make -j$(nproc)
  make altinstall

  cd ..
  rm -rf "Python-${PYTHON_VERSION}" "Python-${PYTHON_VERSION}.tgz"

  apt-get install -y python3-pip python3-venv

  python3 -m venv /venv
 
  python3 --version
else
  echo "Unsupported OS or package manager. Please install Python $PYTHON_VERSION manually."
  exit 1
fi