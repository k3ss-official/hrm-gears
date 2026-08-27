# Phase 1 algorithm — I → T → E on the exploded matrix

Frozen: 2026-08-27. Snapshot file: `config/matrix.exploded.v1.yaml`.
H is a nested supervisor. It does not invent winners. It applies this function.

## Objects

Let a model \(m\) carry:

| symbol | field |
| --- | --- |
| \(v(m)\) | vendor |
| \(\ell(m)\) | lane \(\in L\) |
| \(a(m)\) | ability floor \(\in \{1,2,3,4\}\) |
| \(p(m)\) | unit cost inside the chosen lane (lower = cheaper) |
| \(c(m)\) | vendor claim score \(\in [0,1]\) |
| \(b(m)\) | frozen bench composite \(\in [0,1]\) |
| \(o(m)\) | community offset \(\in [-1,+1]\) |
| \(r(m)\) | reality score (defined below) |
| \(K(m)\) | capability flags: tools, vision |

Lane order \(L\), cheapest-first for Phase 1:

$$
L = (\texttt{subscription},\; \texttt{api\_free},\; \texttt{api\_paid\_non\_frontier},\; \texttt{api\_paid\_frontier})
$$

Index \(\lambda(\ell) \in \{0,1,2,3\}\).

## Reality

Vendor benches are claims. Community chatter offsets them. Frozen, not live.

$$
r(m) = \mathrm{clip}_{[0,1]}\big( \alpha\, b(m) + (1-\alpha)\, c(m) + \beta\, o(m) \big)
$$

Phase 1 constants (locked in the YAML header):

$$
\alpha = 0.55,\quad \beta = 0.25
$$

Example: bench 0.80, claim 0.95, offset \(-0.4\) (overhyped) → \(r = 0.7675\), not 0.95.

## Need (tags → floor)

$$
N(t) = \max(d, u, s, x, \delta)
$$

Maps: depth/tools/stakes/context → \{1,2,3\}. Domain bumps: vision/multimodal/medical \(=3\), planning_law/legal \(=2\).

$$
R_{\min}(t) = \{1\mapsto 0.35,\ 2\mapsto 0.50,\ 3\mapsto 0.65,\ 4\mapsto 0.78\}
$$

Hard flags: tools required if tool_use ≥ light. Vision required if domain contains vision/multimodal.

## I → T → E

**I — identify** eligible set \(E\) on menu \(A\):

$$
E_0 = \{ m \in A : a(m) \ge N(t),\ r(m) \ge R_{\min}(t),\ K(m)\ \mathrm{covers}\ t \}
$$

If empty, drop the reality floor once (keep ability + flags). If still empty: no pick, conf 0.

**T — then** cheapest lane that still has an eligible model, then cheapest model in that lane by unit cost, then higher reality, then YAML order.

**E — else** if confidence \(< \tau=0.62\), climb **one** lane only.

$$
\mathrm{conf} = \mathrm{clip}(0.50 + 0.40(r(m^\star)-R_{\min}) + 0.10\cdot\mathbf{1}[|M_\ell|\ge 2])
$$

## What H imitates

Three heads: lane, vendor, model. Loss = sum of CEs. Under-tier (\(a(m)<N\)) is a hard fail.

Chooser: `scripts/routing_data/policy_nested.py`.
