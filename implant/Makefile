# Makefile for Cobalt Strike Linux Implant

OUTPUT ?= beacon

CC = gcc
CFLAGS = -Wall -Wextra -O2 \
         -I./headers \
         -I./elfloader/elfloader-headers

LDFLAGS = -lssl -lcrypto -lcurl

# Directories
SRC_DIR            = src
ELFLOADER_SRC_DIR  = elfloader/elfloader-src
INC_DIR            = headers
ELFLOADER_INC_DIR  = elfloader/elfloader-headers
OBJ_DIR            = obj
BIN_DIR            = bin

# Target binary
TARGET = $(BIN_DIR)/$(OUTPUT)
MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
TEST_DIR := $(MAKEFILE_DIR)tests

# Source files
SOURCES = \
    $(wildcard $(SRC_DIR)/*.c) \
    $(wildcard $(ELFLOADER_SRC_DIR)/*.c)

# Object files (mirror source tree in obj/)
OBJECTS = $(patsubst %.c,$(OBJ_DIR)/%.o,$(SOURCES))

# Default target
all: directories $(TARGET)

# Create necessary directories
directories:
	@mkdir -p $(BIN_DIR)
	@mkdir -p $(OBJ_DIR)/$(SRC_DIR)
	@mkdir -p $(OBJ_DIR)/$(ELFLOADER_SRC_DIR)

# Link the final binary
$(TARGET): $(OBJECTS)
	@echo "[LD] Linking $@"
	@$(CC) $(OBJECTS) -o $@ $(LDFLAGS)
	@echo "[+] Build complete: $@"

# Compile source files (works for all source dirs)
$(OBJ_DIR)/%.o: %.c
	@echo "[CC] Compiling $<"
	@$(CC) $(CFLAGS) -c $< -o $@

# Clean build artifacts
clean:
	@echo "[CLEAN] Removing build artifacts"
	@rm -rf $(OBJ_DIR) $(BIN_DIR)

# Debug build
debug: CFLAGS += -g -DDEBUG
debug: clean all

test-quick:
	@bash $(TEST_DIR)/run_regression.sh --mode quick

test-full:
	@bash $(TEST_DIR)/run_regression.sh --mode full

.PHONY: all clean debug directories test-quick test-full
