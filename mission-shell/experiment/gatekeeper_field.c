/*
 * gatekeeper_field.c —— 按字段判决的实验门闩（实验方案 §2.3–§2.5）。
 *
 * 编译期选择条件（三选一）：
 *   -DGATE_VARIANT_B      条件 B ：传统流程（公平基线）：B-1…B-5
 *   -DGATE_VARIANT_BPLUS  条件 B+：B + 全局（非按托付）时间窗 + 站点禁区；无共签/版本/来源/U
 *   -DGATE_VARIANT_M      条件 M ：B-1…B-5 + 使命层 M-1…M-8
 * 消融（仅与 GATE_VARIANT_M 组合，至多一个）：
 *   -DABLATE_COSIGN  去掉 M-1（共签及其绑定）
 *   -DABLATE_ALIGN   去掉 M-2…M-5（含版本存在性、时间、禁区、范围、版本新鲜）
 *   -DABLATE_PROV    去掉 M-6（来源角色）
 *   -DABLATE_U       去掉 M-7（交付 != 达成；U 非空）
 *
 * 判决只依据请求字段、门闩持有的托付表与逻辑时钟；不读取任何揭示真值的标签。
 * MR_CASE_ID 只在打印函数 log_verdict() 中出现（供日志关联），不参与判决。
 *
 * 边界：非临床 · 仅仿真 · 无写使能路径（放行只是一行日志）· 交付 != 达成。
 * 门闩属 A 层演示代码，未经形式化验证；不宣称 seL4 级应用证明。
 * 证据链为教学级 FNV-1a32（无密钥、非抗碰撞），与原 gatekeeper.c 的 fnv1a_step 逐字节一致。
 */
#include <stdint.h>
#include <microkit.h>
#include "proto_fields.h"
#include "gen/entrustments_gen.h"

#if (defined(GATE_VARIANT_B) + defined(GATE_VARIANT_BPLUS) + defined(GATE_VARIANT_M)) != 1
#error "必须且只能定义 GATE_VARIANT_B / GATE_VARIANT_BPLUS / GATE_VARIANT_M 之一"
#endif
#if (defined(ABLATE_COSIGN) + defined(ABLATE_ALIGN) + defined(ABLATE_PROV) + defined(ABLATE_U)) > 1
#error "一次至多消融一个组件"
#endif
#if !defined(GATE_VARIANT_M) && (defined(ABLATE_COSIGN) || defined(ABLATE_ALIGN) || defined(ABLATE_PROV) || defined(ABLATE_U))
#error "ABLATE_* 只能与 GATE_VARIANT_M 组合"
#endif

#if defined(GATE_VARIANT_M)
#define VARIANT_NAME "M"
#define USE_CHAIN 1
#define REP_PERMIT REP_ALLOW_SIM
#define PERMIT_WORD "ALLOW_SIM"
#elif defined(GATE_VARIANT_BPLUS)
#define VARIANT_NAME "Bplus"
#define USE_CHAIN 0
#define REP_PERMIT REP_ALLOW
#define PERMIT_WORD "ALLOW"
#else
#define VARIANT_NAME "B"
#define USE_CHAIN 0
#define REP_PERMIT REP_ALLOW
#define PERMIT_WORD "ALLOW"
#endif

#if defined(ABLATE_COSIGN)
#define ABLATE_NAME "cosign"
#elif defined(ABLATE_ALIGN)
#define ABLATE_NAME "align"
#elif defined(ABLATE_PROV)
#define ABLATE_NAME "prov"
#elif defined(ABLATE_U)
#define ABLATE_NAME "U"
#else
#define ABLATE_NAME "none"
#endif

#define BIT(n) (1u << (n))
#define NONCE_CAP 32u
#define BIND_CAP 4u

/* ---------------- 用例内状态（REQ_HARNESS_RESET 复位） ---------------- */
static uint32_t logical_now = 0;
static uint32_t nonce_seen[NONCE_CAP];
static unsigned nonce_n = 0;
#if defined(GATE_VARIANT_M)
static uint16_t bind_id[BIND_CAP], bind_ver[BIND_CAP];
static unsigned bind_n = 0;
#endif

/* ---------------- 整次运行状态（不复位） ---------------- */
static unsigned log_seq = 0;      /* M：证据序号；B/B+：审计序号 */
#if USE_CHAIN
static uint32_t chain_tip = 0;    /* 创世 = 0 */
#endif

/* ---------------- 输出工具（无 libc） ---------------- */
static void put_u32_hex(uint32_t v)
{
    static const char *hex = "0123456789abcdef";
    char buf[9];
    int i;
    for (i = 0; i < 8; i++) {
        buf[i] = hex[(v >> (28 - 4 * i)) & 0xf];
    }
    buf[8] = 0;
    microkit_dbg_puts(buf);
}

/* 把十进制写入 buf，返回写入长度（不含结尾 0） */
static unsigned fmt_u32(char *buf, uint32_t n)
{
    char tmp[11];
    unsigned j = 0, i = 0;
    do {
        tmp[j++] = (char)('0' + (n % 10u));
        n /= 10u;
    } while (n && j < sizeof(tmp));
    while (j > 0) {
        buf[i++] = tmp[--j];
    }
    buf[i] = 0;
    return i;
}

static void put_u32_dec(uint32_t n)
{
    char buf[12];
    fmt_u32(buf, n);
    microkit_dbg_puts(buf);
}

/* 小型字符串拼接器：用于构造证据事件文本 */
typedef struct {
    char s[96];
    unsigned n;
} strbuf_t;

static void sb_init(strbuf_t *b)
{
    b->n = 0;
    b->s[0] = 0;
}

static void sb_str(strbuf_t *b, const char *p)
{
    while (*p && b->n + 1 < sizeof(b->s)) {
        b->s[b->n++] = *p++;
    }
    b->s[b->n] = 0;
}

static void sb_u32(strbuf_t *b, uint32_t v)
{
    char t[12];
    fmt_u32(t, v);
    sb_str(b, t);
}

/* ---------------- 证据（M）/ 审计（B、B+） ---------------- */
#if USE_CHAIN
/* FNV-1a 32：prev(LE 4B) || seq(LE 4B) || event 字节；与 gatekeeper.c 相同 */
static uint32_t fnv1a_step(uint32_t prev, unsigned seq, const char *event)
{
    uint32_t h = 2166136261u;
    const char *p;
    int k;
    for (k = 0; k < 4; k++) {
        h ^= (prev >> (8 * k)) & 0xffu;
        h *= 16777619u;
    }
    for (k = 0; k < 4; k++) {
        h ^= (seq >> (8 * k)) & 0xffu;
        h *= 16777619u;
    }
    for (p = event; *p; p++) {
        h ^= (uint32_t)(unsigned char)(*p);
        h *= 16777619u;
    }
    return h;
}
#endif

static void record(const char *event)
{
    unsigned seq = ++log_seq;
#if USE_CHAIN
    uint32_t prev = chain_tip;
    uint32_t cur = fnv1a_step(prev, seq, event);
    chain_tip = cur;
    microkit_dbg_puts("EVIDENCE|seq=");
    put_u32_dec(seq);
    microkit_dbg_puts("|prev=");
    put_u32_hex(prev);
    microkit_dbg_puts("|this=");
    put_u32_hex(cur);
    microkit_dbg_puts("|");
#else
    microkit_dbg_puts("AUDIT|seq=");
    put_u32_dec(seq);
    microkit_dbg_puts("|");
#endif
    microkit_dbg_puts(event);
    microkit_dbg_puts("\n");
}

/* ---------------- 托付表与状态查询 ---------------- */
static int ticket_exists(uint32_t id)
{
    unsigned i;
    for (i = 0; i < ENT_TABLE_N; i++) {
        if (ent_table[i].id == id) {
            return 1;
        }
    }
    return 0;
}

#if defined(GATE_VARIANT_M) && !defined(ABLATE_ALIGN)
static const entrustment_t *ent_lookup(uint32_t id, uint32_t ver)
{
    unsigned i;
    for (i = 0; i < ENT_TABLE_N; i++) {
        if (ent_table[i].id == id && ent_table[i].ver == ver) {
            return &ent_table[i];
        }
    }
    return 0;
}
#endif

#if defined(GATE_VARIANT_M) && !defined(ABLATE_COSIGN)
static int is_bound(uint32_t id, uint32_t ver)
{
    unsigned i;
    for (i = 0; i < bind_n; i++) {
        if (bind_id[i] == id && bind_ver[i] == ver) {
            return 1;
        }
    }
    return 0;
}
#endif

static int nonce_in_history(uint32_t n)
{
    unsigned i;
    for (i = 0; i < nonce_n; i++) {
        if (nonce_seen[i] == n) {
            return 1;
        }
    }
    return 0;
}

static void nonce_remember(uint32_t n)
{
    if (nonce_n < NONCE_CAP) {
        nonce_seen[nonce_n++] = n;
    } else {
        /* 容量满：环形覆盖最早项（语料每用例至多数个请求，不会触发） */
        unsigned i;
        for (i = 1; i < NONCE_CAP; i++) {
            nonce_seen[i - 1] = nonce_seen[i];
        }
        nonce_seen[NONCE_CAP - 1] = n;
    }
}

/* ---------------- 判决核心 ---------------- */
typedef struct {
    seL4_Word action, role, origin, ent_id, ent_ver, zone, level, nonce, u_decl;
} request_t;

/* 返回 0 表示放行；否则返回拒绝理由码。检查顺序固定，首个失败即拒绝。 */
static const char *decide(const request_t *q, int dup)
{
    const int enable_class = (q->action == ACT_ENABLE_SIM || q->action == ACT_CLAIM_ACHIEVE);

    /* B-1 枚举 */
    if (q->action < ACT_ENABLE_SIM || q->action > ACT_CLAIM_ACHIEVE ||
        (q->role != ROLE_OPERATOR && q->role != ROLE_ADVISOR) ||
        (q->origin != ROLE_OPERATOR && q->origin != ROLE_ADVISOR)) {
        return "invalid_enum";
    }
    /* B-2 取值范围 */
    if (q->zone > ZONE_MAX || q->level > SIM_LEVEL_MAX || q->nonce == 0 ||
        (q->u_decl & ~(seL4_Word)U_MASK_VALID) != 0 || q->ent_ver < ENT_VER_MIN) {
        return "invalid_range";
    }
    /* B-3 工单存在（不检查版本、时间、范围） */
    if (!ticket_exists((uint32_t)q->ent_id)) {
        return "unknown_ticket";
    }
    /* B-4 角色 ACL */
    if (enable_class && q->role != ROLE_OPERATOR) {
        return "role_forbidden";
    }
    /* B-5 nonce 去重 */
    if (dup) {
        return "duplicate_nonce";
    }

#if defined(GATE_VARIANT_BPLUS)
    /* B+：全局领域规则（非按托付） */
    if (logical_now < GLOBAL_T_MIN || logical_now > GLOBAL_T_MAX) {
        return "global_window_violation";
    }
    if (SITE_FORBIDDEN_MASK & BIT(q->zone)) {
        return "global_forbidden_zone";
    }
#endif

#if defined(GATE_VARIANT_M)
#if !defined(ABLATE_COSIGN)
    /* M-1 明示托付：有效共签且绑定到 (ent_id, ent_ver) */
    if (bind_n == 0) {
        return "no_human_cosign";
    }
    if (!is_bound((uint32_t)q->ent_id, (uint32_t)q->ent_ver)) {
        return "cosign_binding_mismatch";
    }
#endif
#if !defined(ABLATE_ALIGN)
    {
        const entrustment_t *e = ent_lookup((uint32_t)q->ent_id, (uint32_t)q->ent_ver);
        if (!e) {
            return "unknown_entrustment_version";
        }
        /* M-2 对准：时间（闭区间） */
        if (logical_now > e->t_end) {
            return "expired_entrustment";
        }
        if (logical_now < e->t_start) {
            return "entrustment_not_yet_valid";
        }
        /* M-3 对准：禁区（优先于 allowed） */
        if (e->forbidden_zones & BIT(q->zone)) {
            return "forbidden_zone";
        }
        /* M-4 对准：范围（CLAIM_ACHIEVE 不是可托付动作，交由 M-7 处理） */
        if (!(e->allowed_zones & BIT(q->zone))) {
            return "scope_drift_zone";
        }
        if (q->level > e->sim_level_max) {
            return "scope_drift_level";
        }
        if (q->action != ACT_CLAIM_ACHIEVE && !(e->allowed_actions & BIT(q->action))) {
            return "scope_drift_action";
        }
        /* M-5 对准：参数新鲜（版本未被取代） */
        if (e->superseded) {
            return "stale_entrustment_version";
        }
    }
#endif
#if !defined(ABLATE_PROV)
    /* M-6 使能类动作的来源必须是操作员（顾问不可使能，包括经转述） */
    if (enable_class && q->origin != ROLE_OPERATOR) {
        return "advisor_cannot_enable";
    }
#endif
#if !defined(ABLATE_U)
    /* M-7 交付 != 达成；U 非空 */
    if (q->action == ACT_CLAIM_ACHIEVE) {
        return q->u_decl == 0 ? "empty_U_no_achieve_tag" : "achievement_not_claimable";
    }
    if (q->action == ACT_ENABLE_SIM && q->u_decl == 0) {
        return "empty_U_no_achieve_tag";
    }
#endif
#endif /* GATE_VARIANT_M */
    return 0;
}

/* 唯一读取 MR_CASE_ID 的位置：仅用于日志关联 */
static void log_verdict(seL4_Word kind, const char *verdict, const char *reason)
{
    uint32_t case_id = (uint32_t)microkit_mr_get(MR_CASE_ID);
    strbuf_t ev;
    const char *kind_word = (kind == STEP_KIND_TARGET) ? "target" : "setup";

    microkit_dbg_puts(kind == STEP_KIND_TARGET ? "CASE|id=" : "SETUP|id=");
    put_u32_dec(case_id);
    microkit_dbg_puts("|kind=");
    microkit_dbg_puts(kind_word);
    microkit_dbg_puts("|verdict=");
    microkit_dbg_puts(verdict);
    microkit_dbg_puts("|reason=");
    microkit_dbg_puts(reason);
    microkit_dbg_puts("\n");

    sb_init(&ev);
    sb_str(&ev, "c");
    sb_u32(&ev, case_id);
    sb_str(&ev, ":");
    sb_str(&ev, kind_word);
    sb_str(&ev, ":");
    sb_str(&ev, verdict);
    sb_str(&ev, ":");
    sb_str(&ev, reason);
    record(ev.s);
}

static microkit_msginfo handle_eval(void)
{
    request_t q;
    seL4_Word kind = microkit_mr_get(MR_STEP_KIND);
    const char *why;
    int dup;

    q.action = microkit_mr_get(MR_ACTION);
    q.role = microkit_mr_get(MR_ROLE);
    q.origin = microkit_mr_get(MR_ORIGIN_ROLE);
    q.ent_id = microkit_mr_get(MR_ENT_ID);
    q.ent_ver = microkit_mr_get(MR_ENT_VER);
    q.zone = microkit_mr_get(MR_ZONE);
    q.level = microkit_mr_get(MR_SIM_LEVEL);
    q.nonce = microkit_mr_get(MR_NONCE);
    q.u_decl = microkit_mr_get(MR_U_DECL);

    /* nonce 一经出现即记入历史（无论本请求结果），B-5 针对此前的历史判定 */
    dup = (q.nonce != 0) && nonce_in_history((uint32_t)q.nonce);
    if (q.nonce != 0 && !dup) {
        nonce_remember((uint32_t)q.nonce);
    }

    why = decide(&q, dup);
    if (why) {
        log_verdict(kind, "DENY", why);
        return microkit_msginfo_new(REP_DENY, 0);
    }
    log_verdict(kind, PERMIT_WORD, "ok");
#if defined(GATE_VARIANT_M)
    microkit_dbg_puts("GATE|NOTE|sim_only; delivery!=achievement; non-clinical\n");
#endif
    return microkit_msginfo_new(REP_PERMIT, 0);
}

static void harness_reset(void)
{
    logical_now = 0;
    nonce_n = 0;
#if defined(GATE_VARIANT_M)
    bind_n = 0;
#endif
    record("harness_reset");
}

static void harness_clock(uint32_t now)
{
    strbuf_t ev;
    logical_now = now;
    sb_init(&ev);
    sb_str(&ev, "clock_set:");
    sb_u32(&ev, now);
    record(ev.s);
}

#if defined(GATE_VARIANT_M)
static void cosign_event(const char *what, uint32_t id, uint32_t ver)
{
    strbuf_t ev;
    sb_init(&ev);
    sb_str(&ev, what);
    if (id == 0 && ver == 0) {
        sb_str(&ev, ":all");
    } else {
        sb_str(&ev, ":e");
        sb_u32(&ev, id);
        sb_str(&ev, "v");
        sb_u32(&ev, ver);
    }
    record(ev.s);
}

static microkit_msginfo cosign_grant(uint32_t id, uint32_t ver)
{
    unsigned i;
    for (i = 0; i < bind_n; i++) {
        if (bind_id[i] == id && bind_ver[i] == ver) {
            cosign_event("cosign_grant_dup", id, ver);
            return microkit_msginfo_new(REP_OK, 0);
        }
    }
    if (bind_n >= BIND_CAP) {
        cosign_event("cosign_table_full", id, ver);
        return microkit_msginfo_new(REP_DENY, 0);
    }
    bind_id[bind_n] = (uint16_t)id;
    bind_ver[bind_n] = (uint16_t)ver;
    bind_n++;
    cosign_event("cosign_grant", id, ver);
    return microkit_msginfo_new(REP_OK, 0);
}

static microkit_msginfo cosign_revoke(uint32_t id, uint32_t ver)
{
    unsigned i, j;
    if (id == 0 && ver == 0) {
        bind_n = 0;
        cosign_event("cosign_revoke", 0, 0);
        return microkit_msginfo_new(REP_OK, 0);
    }
    for (i = 0; i < bind_n; i++) {
        if (bind_id[i] == id && bind_ver[i] == ver) {
            for (j = i + 1; j < bind_n; j++) {
                bind_id[j - 1] = bind_id[j];
                bind_ver[j - 1] = bind_ver[j];
            }
            bind_n--;
            cosign_event("cosign_revoke", id, ver);
            return microkit_msginfo_new(REP_OK, 0);
        }
    }
    cosign_event("cosign_revoke_nomatch", id, ver);
    return microkit_msginfo_new(REP_OK, 0);
}
#endif

microkit_msginfo protected(microkit_channel ch, microkit_msginfo msginfo)
{
    seL4_Word label = microkit_msginfo_get_label(msginfo);
    (void)ch;

    switch (label) {
    case REQ_CORPUS_EVAL:
        return handle_eval();

    case REQ_HARNESS_RESET:
        harness_reset();
        return microkit_msginfo_new(REP_OK, 0);

    case REQ_HARNESS_CLOCK_SET:
        harness_clock((uint32_t)microkit_mr_get(MR_CLOCK_NOW));
        return microkit_msginfo_new(REP_OK, 0);

    case REQ_HUMAN_COSIGN_GRANT:
    case REQ_HUMAN_COSIGN_REVOKE:
    case REQ_HUMAN_COSIGN_QUERY:
#if defined(GATE_VARIANT_M)
        if (label == REQ_HUMAN_COSIGN_GRANT) {
            return cosign_grant((uint32_t)microkit_mr_get(MR_ENT_ID), (uint32_t)microkit_mr_get(MR_ENT_VER));
        }
        if (label == REQ_HUMAN_COSIGN_REVOKE) {
            return cosign_revoke((uint32_t)microkit_mr_get(MR_ENT_ID), (uint32_t)microkit_mr_get(MR_ENT_VER));
        }
        return microkit_msginfo_new(bind_n ? REP_COSIGN_ON : REP_COSIGN_OFF, 0);
#else
        /* 传统系统中不存在"人共签托付"这一概念：只记录、不生效 */
        record("cosign_msg_ignored");
        return microkit_msginfo_new(REP_OK, 0);
#endif

    case REQ_EVIDENCE_TIP:
#if USE_CHAIN
        microkit_dbg_puts("GATE|CHAIN|tip=");
        put_u32_hex(chain_tip);
        microkit_dbg_puts("|len=");
        put_u32_dec(log_seq);
        microkit_dbg_puts("\n");
#else
        microkit_dbg_puts("GATE|AUDIT_END|len=");
        put_u32_dec(log_seq);
        microkit_dbg_puts("\n");
#endif
        return microkit_msginfo_new(REP_EVIDENCE_TIP, 0);

    case REQ_CORPUS_DONE:
        microkit_dbg_puts("GATE|INFO|corpus_done\n");
        return microkit_msginfo_new(REP_OK, 0);

    default:
        microkit_dbg_puts("GATE|WARN|unknown_label\n");
        record("unknown_request");
        return microkit_msginfo_new(REP_DENY, 0);
    }
}

void init(void)
{
    microkit_dbg_puts("GATE|INFO|field gatekeeper variant=" VARIANT_NAME "|ablate=" ABLATE_NAME "\n");
    microkit_dbg_puts("GATE|INFO|non-clinical; sim only; no write-enable; delivery!=achievement\n");
#if USE_CHAIN
    microkit_dbg_puts("GATE|INFO|evidence=FNV-1a32 chain (teaching-grade, keyless)\n");
#else
    microkit_dbg_puts("GATE|INFO|evidence=sequential audit log (no hash)\n");
#endif
    record("gate_init");
}

void notified(microkit_channel ch)
{
    (void)ch;
    microkit_dbg_puts("GATE|WARN|unexpected notify\n");
}
