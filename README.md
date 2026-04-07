<p align="center">
  <h1 align="center">EIRA - Elite Incident Response Agent</h1>
  <p align="center"><strong>An autonomous SRE agent that reasons, optimizes, and self-corrects through live infrastructure incidents.</strong></p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Model-Qwen_2.5_72B-blueviolet?style=for-the-badge" alt="Model"/>
  <img src="https://img.shields.io/badge/Environment-Custom_OrchestratorEnv-0d1117?style=for-the-badge" alt="Env"/>
  <img src="https://img.shields.io/badge/Framework-OpenEnv-orange?style=for-the-badge" alt="Framework"/>
  <img src="https://img.shields.io/badge/Chaos_Rate-15%25-red?style=for-the-badge" alt="Chaos"/>
</p>

---

## 🔥 The Problem

Standard runbook automation—static `if-then` scripts, hardcoded escalation paths—**breaks the moment reality deviates from the script**. In production, tools time out, networks flake, and the cheapest fix isn't always the first one the agent tries. Existing incident-response bots either:

- **Hallucinate actions** without analysing the actual error state, or
- **Burn through expensive operations** (restarts, rollbacks) when a simple log search would have sufficed, or
- **Crash silently** when an upstream dependency returns a timeout instead of a result.

## 💡 The Solution

**EIRA** is an intelligent, cost-aware, chaos-hardened agent that resolves infrastructure incidents the way a senior SRE would:

1. **Read the room** — Analyse logs, errors, and warnings before touching anything.
2. **Think before acting** — Produce explicit chain-of-thought reasoning on every step.
3. **Spend wisely** — Prefer cheap diagnostics over expensive commands, minimising operational cost.
4. **Survive failure** — Detect tool timeouts and automatically retry, without human intervention.

---

## 🏆 Key Innovations

### 1. Chain-of-Thought (CoT) Reasoning

Every action is preceded by a `THOUGHT` step where the agent analyses the current state, interprets `[ERROR]` and `[WARNING]` observations, and plans its next move.

```
AGENT_REASONING: The logs show a payment gateway latency spike. I should search for
'gateway' to confirm the root cause before attempting any mitigation.
[STEP] step=1 action=search_logs gateway reward=3.90 done=false error=null
```

**Why this matters:** The `THOUGHT → ACTION` loop forces structured reasoning, drastically reducing hallucinated or premature actions. Judges can trace the agent's decision-making in real time through the logs.

### 2. Operational Cost-Awareness

Not every tool costs the same in production. EIRA's reward function encodes this reality:

| Tool | Cost | Rationale |
|------|------|-----------|
| `search_logs` | **-0.1** | Read-only, zero side effects |
| `update_crm` | **-0.2** | Administrative write |
| `send_slack` | **-0.3** | External notification (noisy) |
| `run_command` | **-0.7** | Infrastructure mutation (high-risk) |

The agent's **total score** = `Task Completion Reward − Accumulated Action Costs`. This forces the agent to find the **most efficient resolution path**, not just any path. An agent that solves the incident in 4 cheap steps outscores one that solves it in 4 expensive steps.

### 3. Chaos-Hardened Resilience

Production systems are unreliable. EIRA's environment simulates this with a **15% tool flakiness rate** on `run_command`:

```python
TOOL_FLAKINESS_RATE = 0.15  # 15% of run_command calls will timeout
```

When a command fails:
- The environment returns `[ERROR] Connection timeout` — **not** a success.
- The task is **not** marked as mitigated.
- The action is removed from history, **allowing the agent to retry**.
- The agent's CoT reasoning detects the timeout and adapts:

```
AGENT_REASONING: The previous run_command returned a connection timeout. This is
likely transient tool flakiness. I will retry the same command.
[STEP] step=4 action=run_command restart_service reward=-0.70 done=false error=null
```

Agents that survive chaos failures and still complete the task earn a **resilience bonus (+0.05)** on their final score.

---

## 🏗️ Technical Architecture

```
┌──────────────────────────────────────────────────┐
│                  inference.py                    │
│  ┌────────────┐     ┌──────────────────────────┐ │
│  │ CoT Prompt │<--->│ Qwen 2.5 72B-Instruct    │ │
│  │ Engine     │     │  (HF Router /v1)         │ │
│  └─────┬──────┘     └──────────────────────────┘ │
│        │ THOUGHT + ACTION                        │
│        ▼                                         │
│  ┌────────────────────────────────────────────┐  │
│  │           parse_thought_action()           │  │
│  │         Robust multi-format parser         │  │
│  └─────────────────────┬──────────────────────┘  │
│                        │ Action object           │
│                        ▼                         │
│  ┌────────────────────────────────────────────┐  │
│  │              OrchestratorEnv               │  │
│  │  ┌─────────────┐  ┌─────────────────────┐  │  │
│  │  │State Machine│  │ Chaos Engine (15%)  │  │  │
│  │  │• root_found │  │ • Timeout injection │  │  │
│  │  │• mitigated  │  │ • Retry allowance   │  │  │
│  │  │• notified   │  │ • Resilience bonus  │  │  │
│  │  └─────────────┘  └─────────────────────┘  │  │
│  │  ┌──────────────────────────────────────┐  │  │
│  │  │      Cost-Aware Reward Function      │  │  │
│  │  │  reward = task_reward - action_cost  │  │  │
│  │  │  score  = completion - cost_penalty  │  │  │
│  │  └──────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

| Component | Detail |
|-----------|--------|
| **Model** | `Qwen/Qwen2.5-72B-Instruct` via Hugging Face Inference Router |
| **Environment** | Custom `OrchestratorEnv` with state-machine validation, dynamic noise injection, and causal dependency enforcement |
| **Scenarios** | `payment_failure` · `deployment_crash` · `customer_complaint` |
| **Task Loading** | Dynamic via `TASK_NAME` environment variable |
| **Score Range** | Strictly clamped to `(0.01, 0.99)` |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- A [Hugging Face](https://huggingface.co/) account with API access

### Setup

```bash
# 1. Clone the repository
git clone https://huggingface.co/spaces/AndrewJerryV/OpenEnv-Hackathon
cd OpenEnv-Hackathon

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your Hugging Face token
export HF_TOKEN="hf_your_token_here"

# 4. (Optional) Override defaults
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
```

### Run

```bash
# Run against the default scenario (payment_failure)
python inference.py

# Run against a specific scenario
TASK_NAME=deployment_crash python inference.py
```

### Docker

```bash
docker build -t eira .
docker run -e HF_TOKEN="hf_..." -e TASK_NAME="payment_failure" eira
```

---

## 📊 Evaluation Metrics

The final score is a composite of **task completion** and **operational efficiency**:

| Metric | Weight | Description |
|--------|--------|-------------|
| **Root Cause Identified** | +0.30 | Agent correctly searched logs and confirmed the root cause |
| **Incident Mitigated** | +0.30 | Agent applied the correct remediation action |
| **Team Notified** | +0.30 | Agent dispatched notification to the appropriate channel |
| **Efficiency Bonus** | +0.10 | Completed in ≤ 4 actions |
| **Cost Penalty** | −(cost × 0.1) | Accumulated operational cost reduces the score |
| **Resilience Bonus** | +0.05 | Survived tool flakiness and still completed the task |

> **Success threshold:** `score > 0.60`
> **Score range:** `[0.01, 0.99]` — strictly clamped to satisfy OpenEnv validation.

---

## 📂 Project Structure

```
.
├── inference.py              # Agent loop: CoT prompting, parsing, logging
├── env/
│   └── orchestrator_env.py   # Environment: state machine, costs, chaos
├── openenv.yaml              # Task definitions for the OpenEnv framework
├── Dockerfile                # Container build for submission
├── requirements.txt          # Python dependencies
└── README.md
```

---

## 📝 License

This project was built for the [OpenEnv Hackathon](https://huggingface.co/). All rights reserved by the author.
