/*
 * 主机模拟用 microkit.h 桩（hostsim）。
 * 【主机模拟、非 QEMU 实测】只用于在没有交叉编译器/QEMU 的机器上快速验证门闩判决逻辑与日志格式；
 * 不模拟 seL4 内核、能力、保护域隔离或 IPC 语义细节。结果不得表述为 QEMU/seL4 实测。
 */
#pragma once
#include <stdint.h>

typedef uint64_t seL4_Word;
typedef uint8_t seL4_Uint8;
typedef uint16_t seL4_Uint16;
typedef int seL4_Bool;
typedef unsigned int microkit_channel;
typedef struct {
    seL4_Word label;
    seL4_Word count;
} seL4_MessageInfo_t;
typedef seL4_MessageInfo_t microkit_msginfo;

extern seL4_Word hostsim_mr[128];

void microkit_dbg_puts(const char *s);
microkit_msginfo microkit_ppcall(microkit_channel ch, microkit_msginfo msginfo);

static inline microkit_msginfo microkit_msginfo_new(seL4_Word label, seL4_Uint16 count)
{
    microkit_msginfo m;
    m.label = label;
    m.count = count;
    return m;
}
static inline seL4_Word microkit_msginfo_get_label(microkit_msginfo m) { return m.label; }
static inline void microkit_mr_set(seL4_Uint8 mr, seL4_Word v) { hostsim_mr[mr] = v; }
static inline seL4_Word microkit_mr_get(seL4_Uint8 mr) { return hostsim_mr[mr]; }
