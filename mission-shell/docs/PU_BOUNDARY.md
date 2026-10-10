# 保证边界（Microkit 使命外壳演示）

| 层级 | 内容 | 是否声称「已证明」 |
|------|------|-------------------|
| K | seL4 + Microkit | **仅引用** |
| A | gatekeeper/client | 演示；非形式化验证 |
| M | 托付/禁区/证据链/人共签 | 可观察；交付≠达成 |
| U | 真硬件、真签名、密码学强度、临床 | **非空未覆盖** |

## 证据哈希链（演示）

- 算法：FNV-1a 32-bit（**非**密码学哈希声明）
- 每条：`EVIDENCE|seq=…|prev=…|this=…|event`
- 查询：`REQ_EVIDENCE_TIP` → 打印 tip 与长度
- 用途：表明「顺序追加可复核」的教学语义，不作防密码学伪造保证

## 场景

`DEMO_PROFILE=full|cosign_only|false_only`
