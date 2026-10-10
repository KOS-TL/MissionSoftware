/*
 * 实验扩展协议：按字段判决的门闩（实验方案 §2.2）。
 *
 * 非临床 · 仅仿真 · 无写使能路径 · 交付 != 达成。
 * 本头文件不修改、只扩展原 mission_proto.h；原有 full/cosign_only/false_only 剖面不受影响。
 * 所有"区""强度"字段均为无物理含义的仿真字段。
 */
#pragma once
#include <stdint.h>
#include "../mission_proto.h"

/* ---- 报文标签（label） ---- */
#define REQ_CORPUS_EVAL        30u  /* 被评分的目标请求或前置请求 */
#define REQ_HARNESS_RESET      31u  /* 用例间复位共签绑定/nonce 表/逻辑时钟；证据链不复位 */
#define REQ_HARNESS_CLOCK_SET  32u  /* 设置门闩逻辑时钟（测试专用报文；写入证据/审计） */
#define REQ_CORPUS_DONE        33u  /* 语料结束 */
/* 共签沿用 REQ_HUMAN_COSIGN_GRANT/REVOKE/QUERY（20/21/22）；
 * 实验剖面中 GRANT/REVOKE 额外携带 MR_ENT_ID/MR_ENT_VER，即共签绑定到某一版托付。
 * REVOKE 携带 (0,0) 表示撤销全部绑定。 */

#define REP_ALLOW              16u  /* B/B+ 的放行（功能性"成功"）；M 仍用 REP_ALLOW_SIM(10) */
/* 两者都以 REP_DENY(11) 表示拒绝；测试控制报文返回 REP_OK(12) */

/* ---- 消息寄存器布局（microkit_mr_set / microkit_mr_get） ---- */
enum {
    MR_CASE_ID = 0,   /* 用例编号；仅用于日志关联，门闩不得据此判决 */
    MR_STEP_KIND,     /* 0 = target（评分），1 = setup（不评分） */
    MR_ACTION,        /* 1=ENABLE_SIM, 2=RECOMMEND, 3=QUERY_STATUS, 4=CLAIM_ACHIEVE */
    MR_ROLE,          /* 1=OPERATOR, 2=ADVISOR */
    MR_ORIGIN_ROLE,   /* 来源角色（玩具级标注；真实来源签名属 U） */
    MR_ENT_ID,        /* 托付编号 */
    MR_ENT_VER,       /* 托付版本 */
    MR_ZONE,          /* 目标区 0..15 */
    MR_SIM_LEVEL,     /* 仿真强度 0..1000（无物理含义） */
    MR_NONCE,         /* 非零 */
    MR_U_DECL,        /* 未覆盖项 U 的位掩码；0 = 声称"无未覆盖" */
    MR_COUNT
};
/* REQ_HARNESS_CLOCK_SET 只用 MR 0（逻辑时刻）。 */
#define MR_CLOCK_NOW 0

#define ACT_ENABLE_SIM     1u
#define ACT_RECOMMEND      2u
#define ACT_QUERY_STATUS   3u
#define ACT_CLAIM_ACHIEVE  4u
#define ROLE_OPERATOR      1u
#define ROLE_ADVISOR       2u

#define STEP_KIND_TARGET   0u
#define STEP_KIND_SETUP    1u

#define ZONE_MAX           15u
#define SIM_LEVEL_MAX      1000u
#define U_MASK_VALID       0xffu
#define ENT_VER_MIN        1u

/* ---- 门闩持有的托付记录（由 gen/entrustments_gen.h 实例化） ---- */
typedef struct {
    uint16_t id, ver;
    uint32_t t_start, t_end;      /* 逻辑时间，闭区间 [t_start, t_end] */
    uint16_t allowed_zones;       /* 位掩码 */
    uint16_t forbidden_zones;     /* 位掩码，优先于 allowed */
    uint16_t sim_level_max;       /* 托付上限（<= 设备范围 1000） */
    uint8_t  allowed_actions;     /* 位掩码：bit(action) */
    uint8_t  superseded;          /* 1 = 已被更高版本取代 */
} entrustment_t;

/* ---- 客户端回放的语料步骤（由 corpus/out/corpus_<seed>.h 实例化） ---- */
#define STEP_OP_RESET   1u
#define STEP_OP_CLOCK   2u
#define STEP_OP_GRANT   3u
#define STEP_OP_REVOKE  4u
#define STEP_OP_EVAL    5u

typedef struct {
    uint32_t case_id;
    uint8_t  op;        /* STEP_OP_* */
    uint8_t  kind;      /* STEP_KIND_* */
    uint8_t  action;    /* 允许越界值（用于 M1 格式错用例） */
    uint8_t  role;
    uint8_t  origin;
    uint16_t ent_id;
    uint16_t ent_ver;
    uint16_t zone;
    uint16_t sim_level;
    uint32_t nonce;
    uint32_t u_decl;
    uint32_t now;       /* 仅 STEP_OP_CLOCK 使用 */
} corpus_step_t;
