# Antigravity Metrics & Mathematical Formulations

## 1. Fix@k — Automated Remediation Confidence

Directly analogous to Codex's `pass@k` code-generation evaluation metric, `Fix@k` quantifies the probability that at least one of $k$ independent automated remediation attempts by a thruster successfully resolves a pipeline drag incident without human intervention.

$$Fix@k = 1 - \frac{\binom{n - c}{k}}{\binom{n}{k}}$$

Where:
- $n$: total sampled remediation attempts.
- $c$: number of successful remediations.
- $k$: retry budget considered per trial.

### Worked Example:
Given $n = 200$, $c = 150$:
$$Fix@1 = 1 - \frac{\binom{50}{1}}{\binom{200}{1}} = 1 - 0.25 = 0.75$$
$$Fix@3 = 1 - \frac{\binom{50}{3}}{\binom{200}{3}} = 1 - \frac{19600}{1313400} \approx 0.985$$

## 2. Drag Equation
$$D(w, t) = W_q(w, t) + W_s(w, t) \cdot P_{\text{fail}}(w, t)$$
- $W_q$: Average queue wait time (minutes)
- $W_s$: Average execution/service time (minutes)
- $P_{\text{fail}}$: Failure / retry probability

## 3. Normalized Drag Coefficient
$$C_d(w) = \frac{D(w, t)}{D_{\max}(field, t)}$$
Ranks wells from 0.0 to 1.0 within the evaluated field.

## 4. Escape Velocity Ratio (EVR)
$$EVR = \frac{v_{\text{current}}}{v_{\text{target}}}$$
- `SUB_ORBITAL`: $EVR < 0.85$
- `APPROACHING`: $0.85 \le EVR < 1.0$
- `ESCAPE`: $EVR \ge 1.0$ sustained $\ge 14$ days
- `DECAYING`: Trending down $\ge 10\%$ over 2 weeks

## 5. Orbit Stability Index (OSI)
$$OSI = 1 - \frac{\text{stddev}(v, 14d)}{\text{mean}(v, 14d)}$$
Clamped to $[0, 1]$. Measures delivery predictability.
