ifeq ($(strip $(BUILD_DIR)),)
$(error BUILD_DIR must be specified)
endif
ifeq ($(strip $(MICROKIT_SDK)),)
$(error MICROKIT_SDK must be specified)
endif
ifeq ($(strip $(MICROKIT_BOARD)),)
$(error MICROKIT_BOARD must be specified)
endif
ifeq ($(strip $(MICROKIT_CONFIG)),)
$(error MICROKIT_CONFIG must be specified)
endif

DEMO_PROFILE ?= full
ifeq ($(DEMO_PROFILE),full)
  CLIENT_SRC := scenarios/client_full.c
else ifeq ($(DEMO_PROFILE),cosign_only)
  CLIENT_SRC := scenarios/client_cosign_only.c
else ifeq ($(DEMO_PROFILE),false_only)
  CLIENT_SRC := scenarios/client_false_only.c
else ifeq ($(DEMO_PROFILE),baseline_corpus)
  CLIENT_SRC := experiment/client_corpus.c
  GATE_VARIANT := B
else ifeq ($(DEMO_PROFILE),mission_corpus)
  CLIENT_SRC := experiment/client_corpus.c
  GATE_VARIANT := M
else ifeq ($(DEMO_PROFILE),baselineplus_corpus)
  CLIENT_SRC := experiment/client_corpus.c
  GATE_VARIANT := BPLUS
else
$(error Unknown DEMO_PROFILE=$(DEMO_PROFILE); use full|cosign_only|false_only|baseline_corpus|mission_corpus|baselineplus_corpus)
endif

# ---- 实验分支（按字段判决的门闩；见 experiment/README.md）----
# 原 full/cosign_only/false_only 剖面：GATE_SRC=gatekeeper.c，GATE_DEFS/CLIENT_DEFS 为空，
# 编译命令与依赖语义与改动前一致（回归门禁：full 仍得 GATE|CHAIN|tip=80488a97|len=10）。
GATE_SRC := gatekeeper.c
GATE_DEFS :=
GATE_DEPS :=
CLIENT_DEFS :=
CLIENT_DEPS :=
ABLATE ?=
ifneq ($(strip $(GATE_VARIANT)),)
  CORPUS_SET ?= seed
  CORPUS_SEED ?= 20261007
  ifeq ($(CORPUS_SET),seed)
    CORPUS_H := experiment/corpus/out/corpus_$(CORPUS_SEED).h
  else ifeq ($(CORPUS_SET),holdout_draft)
    CORPUS_H := experiment/corpus/out/holdout_draft.h
  else
    $(error Unknown CORPUS_SET=$(CORPUS_SET); use seed|holdout_draft)
  endif
  GATE_SRC := experiment/gatekeeper_field.c
  GATE_DEFS := -DGATE_VARIANT_$(GATE_VARIANT) -fno-tree-loop-distribute-patterns
  GATE_DEPS := experiment/proto_fields.h experiment/gen/entrustments_gen.h
  CLIENT_DEFS := -I$(BUILD_DIR) -fno-tree-loop-distribute-patterns
  CLIENT_DEPS := experiment/proto_fields.h $(BUILD_DIR)/corpus_active.h
  ifneq ($(strip $(ABLATE)),)
    ifneq ($(GATE_VARIANT),M)
      $(error ABLATE=$(ABLATE) only valid with DEMO_PROFILE=mission_corpus)
    endif
    ifeq ($(ABLATE),cosign)
      GATE_DEFS += -DABLATE_COSIGN
    else ifeq ($(ABLATE),align)
      GATE_DEFS += -DABLATE_ALIGN
    else ifeq ($(ABLATE),prov)
      GATE_DEFS += -DABLATE_PROV
    else ifeq ($(ABLATE),U)
      GATE_DEFS += -DABLATE_U
    else
      $(error Unknown ABLATE=$(ABLATE); use cosign|align|prov|U)
    endif
  endif
  ifneq ($(strip $(CORPUS_SHARD)),)
    CLIENT_DEFS += -DCORPUS_SHARD_K=$(word 1,$(subst /, ,$(CORPUS_SHARD)))u -DCORPUS_SHARD_N=$(word 2,$(subst /, ,$(CORPUS_SHARD)))u
  endif
else ifneq ($(strip $(ABLATE)),)
  $(error ABLATE=$(ABLATE) only valid with DEMO_PROFILE=mission_corpus)
endif

BOARD_DIR := $(MICROKIT_SDK)/board/$(MICROKIT_BOARD)/$(MICROKIT_CONFIG)
ARCH := $(shell grep 'CONFIG_SEL4_ARCH  ' $(BOARD_DIR)/include/kernel/gen_config.h | cut -d' ' -f4)

ifeq ($(ARCH),aarch64)
  TARGET_TRIPLE := aarch64-none-elf
  CFLAGS_ARCH := -mstrict-align
else ifeq ($(ARCH),riscv64)
  TARGET_TRIPLE := riscv64-unknown-elf
  CFLAGS_ARCH := -march=rv64imafdc_zicsr_zifencei -mabi=lp64d
else
$(error Unsupported ARCH $(ARCH))
endif

ifdef CROSS_PREFIX
  TARGET_TRIPLE := $(CROSS_PREFIX)
endif

ifeq ($(strip $(LLVM)),True)
  CC := clang -target $(TARGET_TRIPLE)
  LD := ld.lld
else
  CC := $(TARGET_TRIPLE)-gcc
  LD := $(TARGET_TRIPLE)-ld
endif

MICROKIT_TOOL ?= $(MICROKIT_SDK)/bin/microkit

CFLAGS := -nostdlib -ffreestanding -g -O2 -Wall -Wno-unused-function -Werror -I$(BOARD_DIR)/include -I. $(CFLAGS_ARCH)
LDFLAGS := -L$(BOARD_DIR)/lib
LIBS := -lmicrokit -Tmicrokit.ld

IMAGE_FILE = $(BUILD_DIR)/loader.img
REPORT_FILE = $(BUILD_DIR)/report.txt

all: $(IMAGE_FILE)

$(BUILD_DIR)/gatekeeper.o: $(GATE_SRC) Makefile mission_proto.h $(GATE_DEPS)
	$(CC) -c $(CFLAGS) $(GATE_DEFS) $(GATE_SRC) -o $@

$(BUILD_DIR)/client.o: $(CLIENT_SRC) Makefile mission_proto.h $(CLIENT_DEPS)
	$(CC) -c $(CFLAGS) $(CLIENT_DEFS) $(CLIENT_SRC) -o $@

# 实验剖面：把选定语料头复制为 $(BUILD_DIR)/corpus_active.h（源码树不被构建改写）
$(BUILD_DIR)/corpus_active.h: $(CORPUS_H)
	cp $(CORPUS_H) $@

$(BUILD_DIR)/gatekeeper.elf: $(BUILD_DIR)/gatekeeper.o
	$(LD) $(LDFLAGS) $^ $(LIBS) -o $@

$(BUILD_DIR)/client.elf: $(BUILD_DIR)/client.o
	$(LD) $(LDFLAGS) $^ $(LIBS) -o $@

$(IMAGE_FILE) $(REPORT_FILE): $(BUILD_DIR)/gatekeeper.elf $(BUILD_DIR)/client.elf mission.system
	$(MICROKIT_TOOL) mission.system --search-path $(BUILD_DIR) --board $(MICROKIT_BOARD) --config $(MICROKIT_CONFIG) -o $(IMAGE_FILE) -r $(REPORT_FILE)
