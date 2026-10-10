/*
 * hostsim.c —— 主机模拟驱动：把 gatekeeper_field.c 与 client_corpus.c 链接进同一个主机进程，
 * microkit_ppcall 直接调用门闩的 protected()。输出与 QEMU 串口相同格式的行。
 * 【主机模拟、非 QEMU 实测】
 */
#include <stdio.h>
#include "microkit.h"

seL4_Word hostsim_mr[128];

void gk_init(void);
microkit_msginfo gk_protected(microkit_channel ch, microkit_msginfo msginfo);
void client_init(void);

void microkit_dbg_puts(const char *s) { fputs(s, stdout); }

microkit_msginfo microkit_ppcall(microkit_channel ch, microkit_msginfo msginfo)
{
    return gk_protected(ch, msginfo);
}

int main(void)
{
    gk_init();      /* Microkit 中被动 PD（门闩，优先级更高）先完成 init */
    client_init();
    return 0;
}
