/*
 * client_corpus.c —— 语料回放客户端（实验方案 §5.2）。
 *
 * 逐步回放 corpus_active.h（由 Makefile 从 experiment/corpus/out/ 复制到 $(BUILD_DIR)）中的
 * corpus_steps[]，每步通过 PPC 发给门闩。客户端不知道类别与真值；它对 B/B+/M 完全相同。
 *
 * 分片（可选，防止客户端 PD 内存不足）：-DCORPUS_SHARD_K=k -DCORPUS_SHARD_N=K，
 * 只回放"用例序号 mod K == k"的用例。每片一份日志，分析时合并。
 *
 * 非临床 · 仅仿真 · 无写使能 · 交付 != 达成。
 */
#include <stdint.h>
#include <microkit.h>
#include "proto_fields.h"
#include "corpus_active.h"

#ifndef CORPUS_SHARD_N
#define CORPUS_SHARD_N 1u
#endif
#ifndef CORPUS_SHARD_K
#define CORPUS_SHARD_K 0u
#endif

static void put_dec(uint32_t n)
{
    char tmp[11], buf[12];
    unsigned j = 0, i = 0;
    do {
        tmp[j++] = (char)('0' + (n % 10u));
        n /= 10u;
    } while (n && j < sizeof(tmp));
    while (j > 0) {
        buf[i++] = tmp[--j];
    }
    buf[i] = 0;
    microkit_dbg_puts(buf);
}

static const char *rep_name(seL4_Word lab)
{
    switch (lab) {
    case REP_ALLOW_SIM: return "ALLOW_SIM";
    case REP_ALLOW: return "ALLOW";
    case REP_DENY: return "DENY";
    case REP_OK: return "OK";
    case REP_COSIGN_ON: return "COSIGN_ON";
    case REP_COSIGN_OFF: return "COSIGN_OFF";
    case REP_EVIDENCE_TIP: return "EVIDENCE_TIP";
    default: return "OTHER";
    }
}

static seL4_Word send_step(const corpus_step_t *s)
{
    microkit_msginfo rep;
    switch (s->op) {
    case STEP_OP_RESET:
        rep = microkit_ppcall(GATE_CH, microkit_msginfo_new(REQ_HARNESS_RESET, 0));
        break;
    case STEP_OP_CLOCK:
        microkit_mr_set(MR_CLOCK_NOW, s->now);
        rep = microkit_ppcall(GATE_CH, microkit_msginfo_new(REQ_HARNESS_CLOCK_SET, 1));
        break;
    case STEP_OP_GRANT:
    case STEP_OP_REVOKE:
        microkit_mr_set(MR_ENT_ID, s->ent_id);
        microkit_mr_set(MR_ENT_VER, s->ent_ver);
        rep = microkit_ppcall(GATE_CH, microkit_msginfo_new(
                  s->op == STEP_OP_GRANT ? REQ_HUMAN_COSIGN_GRANT : REQ_HUMAN_COSIGN_REVOKE, MR_COUNT));
        break;
    default: /* STEP_OP_EVAL */
        microkit_mr_set(MR_CASE_ID, s->case_id);
        microkit_mr_set(MR_STEP_KIND, s->kind);
        microkit_mr_set(MR_ACTION, s->action);
        microkit_mr_set(MR_ROLE, s->role);
        microkit_mr_set(MR_ORIGIN_ROLE, s->origin);
        microkit_mr_set(MR_ENT_ID, s->ent_id);
        microkit_mr_set(MR_ENT_VER, s->ent_ver);
        microkit_mr_set(MR_ZONE, s->zone);
        microkit_mr_set(MR_SIM_LEVEL, s->sim_level);
        microkit_mr_set(MR_NONCE, s->nonce);
        microkit_mr_set(MR_U_DECL, s->u_decl);
        rep = microkit_ppcall(GATE_CH, microkit_msginfo_new(REQ_CORPUS_EVAL, MR_COUNT));
        break;
    }
    return microkit_msginfo_get_label(rep);
}

void init(void)
{
    uint32_t i, case_ord = 0, n_run = 0;
    int active = 0;

    microkit_dbg_puts("CLIENT|INFO|profile=corpus|corpus=" CORPUS_ID "|json_sha256=" CORPUS_JSON_SHA256 "|shard=");
    put_dec(CORPUS_SHARD_K);
    microkit_dbg_puts("/");
    put_dec(CORPUS_SHARD_N);
    microkit_dbg_puts("|steps=");
    put_dec(CORPUS_N_STEPS);
    microkit_dbg_puts("\n");

    for (i = 0; i < CORPUS_N_STEPS; i++) {
        const corpus_step_t *s = &corpus_steps[i];
        seL4_Word lab;
        if (s->op == STEP_OP_RESET) {
            active = ((case_ord % CORPUS_SHARD_N) == CORPUS_SHARD_K);
            case_ord++;
            if (active) {
                n_run++;
            }
        }
        if (!active) {
            continue;
        }
        lab = send_step(s);
#ifdef CLIENT_VERBOSE
        if (s->op == STEP_OP_EVAL) {
            microkit_dbg_puts("CLIENT|REQ|case=");
            put_dec(s->case_id);
            microkit_dbg_puts("|step=");
            put_dec(i);
            microkit_dbg_puts("\n");
        }
#endif
        if (s->op == STEP_OP_EVAL && s->kind == STEP_KIND_TARGET) {
            microkit_dbg_puts("CLIENT|REP|case=");
            put_dec(s->case_id);
            microkit_dbg_puts("|label=");
            microkit_dbg_puts(rep_name(lab));
            microkit_dbg_puts("\n");
        }
    }

    (void)microkit_ppcall(GATE_CH, microkit_msginfo_new(REQ_EVIDENCE_TIP, 0));
    (void)microkit_ppcall(GATE_CH, microkit_msginfo_new(REQ_CORPUS_DONE, 0));
    microkit_dbg_puts("CLIENT|INFO|CORPUS_DONE|n=");
    put_dec(n_run);
    microkit_dbg_puts("\n");
}

void notified(microkit_channel ch)
{
    (void)ch;
}
