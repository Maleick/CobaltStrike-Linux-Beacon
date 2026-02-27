# Makefile for Cobalt Strike macOS ARM64 Implant
# Build host: macOS ARM64 (Apple Silicon M1-M4)
# Compiler: Apple Clang (Xcode Command Line Tools)
# Dependencies: Homebrew openssl@3, Homebrew curl

OUTPUT ?= beacon-macos

CC = clang

BREW_OPENSSL := $(shell brew --prefix openssl@3 2>/dev/null)
BREW_CURL    := $(shell brew --prefix curl 2>/dev/null)

CFLAGS = -Wall -Wextra -O2 \
         -arch arm64 \
         -mmacosx-version-min=12.0 \
         -I./headers \
         -I./generated \
         -I$(BREW_OPENSSL)/include \
         -I$(BREW_CURL)/include

LDFLAGS = -L$(BREW_OPENSSL)/lib \
          -L$(BREW_CURL)/lib \
          -lssl -lcrypto -lcurl

# Directories
SRC_DIR = src
INC_DIR = headers
OBJ_DIR = obj
BIN_DIR = bin

# Target binary
TARGET = $(BIN_DIR)/$(OUTPUT)
MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

# macOS source files only — no ELFLoader
SOURCES = $(wildcard $(SRC_DIR)/*.c)

# Object files (mirror source tree in obj/)
OBJECTS = $(patsubst %.c,$(OBJ_DIR)/%.o,$(SOURCES))

# Default target
all: check-deps directories $(TARGET)

# Verify Homebrew dependencies are available
check-deps:
	@if [ -z "$(BREW_OPENSSL)" ]; then \
		echo "[ERROR] openssl@3 not found. Run: brew install openssl@3"; \
		exit 1; \
	fi
	@if [ -z "$(BREW_CURL)" ]; then \
		echo "[ERROR] Homebrew curl not found. Run: brew install curl"; \
		exit 1; \
	fi

# Create necessary directories
directories:
	@mkdir -p $(BIN_DIR)
	@mkdir -p $(OBJ_DIR)/$(SRC_DIR)
	@mkdir -p generated

# Link the final binary
$(TARGET): $(OBJECTS)
	@echo "[LD] Linking $@"
	@$(CC) -arch arm64 $(OBJECTS) -o $@ $(LDFLAGS)
	@echo "[+] Build complete: $@"
	@echo "[+] Verifying ad-hoc code signature..."
	@codesign -dv $@ 2>&1 | grep -q "adhoc" && echo "[+] Ad-hoc signature present" || (codesign --sign - --force $@ && echo "[+] Ad-hoc signature applied")

# Compile source files
$(OBJ_DIR)/%.o: %.c
	@echo "[CC] Compiling $<"
	@$(CC) $(CFLAGS) -c $< -o $@

# Clean build artifacts
clean:
	@echo "[CLEAN] Removing build artifacts and generated headers"
	@rm -rf $(OBJ_DIR) $(BIN_DIR) generated/*
	@touch generated/.gitkeep

# Debug build (includes DEBUG macro for DEBUG_PRINT output)
debug: CFLAGS += -g -DDEBUG
debug: clean all

.PHONY: all clean debug directories check-deps
