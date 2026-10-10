/* 自动生成，请勿手改。来源：experiment/corpus/entrustments.json（SHA-256：1412203e37bd798dacb83d07deca7e6adf865cd191a1d851c2fc6ea19e2cf502） */
/* 托付表（门闩持有）；种子无关。非临床·仅仿真。 */
#pragma once
/* 使用前须先包含 proto_fields.h */

#define ENT_TABLE_N 11u
#define ENT_ID_MAX 8u
/* B+ 的全局领域规则（非按托付）：站点运行时间窗与站点禁区 */
#define GLOBAL_T_MIN 50u
#define GLOBAL_T_MAX 2000u
#define SITE_FORBIDDEN_MASK 0x8080u

static const entrustment_t ent_table[ENT_TABLE_N] = {
  {1u, 1u, 100u, 200u, 0x000eu, 0x8080u, 300u, 0x0eu, 0u},
  {2u, 1u, 150u, 400u, 0x0030u, 0x8080u, 500u, 0x04u, 0u},
  {3u, 1u, 100u, 300u, 0x004eu, 0x8180u, 300u, 0x0eu, 1u},
  {3u, 2u, 100u, 300u, 0x004eu, 0x8180u, 200u, 0x0eu, 0u},
  {4u, 1u, 500u, 900u, 0x0f00u, 0x9081u, 800u, 0x0eu, 0u},
  {5u, 1u, 50u, 1000u, 0x007fu, 0xe080u, 600u, 0x0au, 0u},
  {6u, 1u, 200u, 600u, 0x4600u, 0x8880u, 400u, 0x0eu, 1u},
  {6u, 2u, 200u, 600u, 0x4600u, 0x8880u, 350u, 0x0eu, 1u},
  {6u, 3u, 200u, 600u, 0x0600u, 0xc880u, 250u, 0x0eu, 0u},
  {7u, 1u, 1000u, 2000u, 0x7000u, 0x8088u, 900u, 0x0au, 0u},
  {8u, 1u, 50u, 150u, 0x0154u, 0x80a8u, 150u, 0x0eu, 0u},
};
