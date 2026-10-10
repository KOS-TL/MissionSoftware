/* DEMO_PROFILE=cosign_only — focus on human co-sign channel. */
#include <microkit.h>
#include "mission_proto.h"

static void call(const char *name, seL4_Word req)
{
    microkit_msginfo rep;
    seL4_Word lab;
    microkit_dbg_puts("CLIENT|REQ|");
    microkit_dbg_puts(name);
    microkit_dbg_puts("\n");
    rep = microkit_ppcall(GATE_CH, microkit_msginfo_new(req, 0));
    lab = microkit_msginfo_get_label(rep);
    if (lab == REP_ALLOW_SIM) microkit_dbg_puts("CLIENT|REP|ALLOW_SIM\n");
    else if (lab == REP_DENY) microkit_dbg_puts("CLIENT|REP|DENY\n");
    else if (lab == REP_OK) microkit_dbg_puts("CLIENT|REP|OK\n");
    else if (lab == REP_COSIGN_ON) microkit_dbg_puts("CLIENT|REP|COSIGN_ON\n");
    else if (lab == REP_COSIGN_OFF) microkit_dbg_puts("CLIENT|REP|COSIGN_OFF\n");
    else if (lab == REP_EVIDENCE_TIP) microkit_dbg_puts("CLIENT|REP|EVIDENCE_TIP\n");
    else microkit_dbg_puts("CLIENT|REP|OTHER\n");
}

void init(void)
{
    microkit_dbg_puts("CLIENT|INFO|profile=cosign_only\n");
    call("query", REQ_HUMAN_COSIGN_QUERY);
    call("legal_no_cosign", REQ_LEGAL_ENABLE);
    call("grant", REQ_HUMAN_COSIGN_GRANT);
    call("legal_with_cosign", REQ_LEGAL_ENABLE);
    call("revoke", REQ_HUMAN_COSIGN_REVOKE);
    call("legal_after_revoke", REQ_LEGAL_ENABLE);
    call("evidence_tip", REQ_EVIDENCE_TIP);
    microkit_dbg_puts("CLIENT|INFO|MISSION_SHELL_DEMO_DONE\n");
}

void notified(microkit_channel ch) { (void)ch; }
