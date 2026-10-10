/* Mission PPC protocol (demo only; non-clinical). */
#pragma once

#define GATE_CH 0

#define REQ_LEGAL_ENABLE        1u
#define REQ_EXPIRED_TRUST       2u
#define REQ_FORBIDDEN_ZONE      3u
#define REQ_ADVISOR_ENABLE      4u
#define REQ_EMPTY_U_ACHIEVE     5u

#define REQ_HUMAN_COSIGN_GRANT  20u
#define REQ_HUMAN_COSIGN_REVOKE 21u
#define REQ_HUMAN_COSIGN_QUERY  22u
#define REQ_EVIDENCE_TIP        23u  /* return/print chain tip */

#define REP_ALLOW_SIM           10u
#define REP_DENY                11u
#define REP_OK                  12u
#define REP_COSIGN_ON           13u
#define REP_COSIGN_OFF          14u
#define REP_EVIDENCE_TIP        15u
