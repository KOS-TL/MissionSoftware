/*
 * Gatekeeper PD: mission shell + minimal evidence hash chain (FNV-1a 32-bit).
 * Not cryptographic strength; demo of tamper-evident sequencing only.
 * K=cited; A=unverified; ALLOW_SIM != achievement; non-clinical.
 */
#include <stdint.h>
#include <microkit.h>
#include "mission_proto.h"

static unsigned evidence_seq = 0;
static int human_cosign_ok = 0;
static uint32_t chain_tip = 0; /* running hash; genesis = 0 */

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

static void put_u32_dec(unsigned n)
{
    char buf[16];
    int i = 0;
    if (n == 0) {
        microkit_dbg_puts("0");
        return;
    }
    {
        char tmp[16];
        int j = 0;
        while (n && j < 15) {
            tmp[j++] = (char)('0' + (n % 10));
            n /= 10;
        }
        while (j > 0) {
            buf[i++] = tmp[--j];
        }
    }
    buf[i] = 0;
    microkit_dbg_puts(buf);
}

/* FNV-1a 32-bit over prev tip + seq + event string */
static uint32_t fnv1a_step(uint32_t prev, unsigned seq, const char *event)
{
    uint32_t h = 2166136261u;
    const char *p;
    int k;
    /* mix previous tip bytes */
    for (k = 0; k < 4; k++) {
        h ^= (prev >> (8 * k)) & 0xffu;
        h *= 16777619u;
    }
    /* mix seq little-endian */
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

static void evidence_append(const char *event)
{
    uint32_t prev = chain_tip;
    unsigned seq = ++evidence_seq;
    uint32_t cur = fnv1a_step(prev, seq, event);
    chain_tip = cur;

    microkit_dbg_puts("EVIDENCE|seq=");
    put_u32_dec(seq);
    microkit_dbg_puts("|prev=");
    put_u32_hex(prev);
    microkit_dbg_puts("|this=");
    put_u32_hex(cur);
    microkit_dbg_puts("|");
    microkit_dbg_puts(event);
    microkit_dbg_puts("\n");
}

static microkit_msginfo deny(const char *why)
{
    microkit_dbg_puts("GATE|DENY|");
    microkit_dbg_puts(why);
    microkit_dbg_puts("\n");
    evidence_append(why);
    return microkit_msginfo_new(REP_DENY, 0);
}

static microkit_msginfo allow_sim(const char *why)
{
    microkit_dbg_puts("GATE|ALLOW_SIM|");
    microkit_dbg_puts(why);
    microkit_dbg_puts("\n");
    microkit_dbg_puts("GATE|NOTE|sim_only; delivery!=achievement; non-clinical\n");
    evidence_append(why);
    return microkit_msginfo_new(REP_ALLOW_SIM, 0);
}

microkit_msginfo protected(microkit_channel ch, microkit_msginfo msginfo)
{
    seL4_Word label;
    (void)ch;
    label = microkit_msginfo_get_label(msginfo);

    switch (label) {
    case REQ_HUMAN_COSIGN_GRANT:
        human_cosign_ok = 1;
        microkit_dbg_puts("GATE|COSIGN|GRANT (demo stand-in)\n");
        evidence_append("cosign_grant");
        return microkit_msginfo_new(REP_OK, 0);

    case REQ_HUMAN_COSIGN_REVOKE:
        human_cosign_ok = 0;
        microkit_dbg_puts("GATE|COSIGN|REVOKE\n");
        evidence_append("cosign_revoke");
        return microkit_msginfo_new(REP_OK, 0);

    case REQ_HUMAN_COSIGN_QUERY:
        if (human_cosign_ok) {
            microkit_dbg_puts("GATE|COSIGN|STATE=ON\n");
            return microkit_msginfo_new(REP_COSIGN_ON, 0);
        }
        microkit_dbg_puts("GATE|COSIGN|STATE=OFF\n");
        return microkit_msginfo_new(REP_COSIGN_OFF, 0);

    case REQ_EVIDENCE_TIP:
        microkit_dbg_puts("GATE|CHAIN|tip=");
        put_u32_hex(chain_tip);
        microkit_dbg_puts("|len=");
        put_u32_dec(evidence_seq);
        microkit_dbg_puts("\n");
        return microkit_msginfo_new(REP_EVIDENCE_TIP, 0);

    default:
        break;
    }

    if (!human_cosign_ok) {
        return deny("no_human_cosign");
    }

    switch (label) {
    case REQ_LEGAL_ENABLE:
        return allow_sim("legal_path_sim");
    case REQ_EXPIRED_TRUST:
        return deny("expired_entrustment");
    case REQ_FORBIDDEN_ZONE:
        return deny("forbidden_zone");
    case REQ_ADVISOR_ENABLE:
        return deny("advisor_cannot_enable");
    case REQ_EMPTY_U_ACHIEVE:
        return deny("empty_U_no_achieve_tag");
    default:
        return deny("unknown_request");
    }
}

void init(void)
{
    microkit_dbg_puts("GATE|INFO|mission shell init (cosign OFF; hash chain on)\n");
    microkit_dbg_puts("GATE|INFO|K=cited; A=demo; M=discipline; chain=FNV-1a32 demo\n");
    evidence_append("gate_init");
}

void notified(microkit_channel ch)
{
    (void)ch;
    microkit_dbg_puts("GATE|WARN|unexpected notify\n");
}
