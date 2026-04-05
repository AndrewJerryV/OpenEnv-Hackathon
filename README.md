---
title: OpenEnv Hackathon
emoji: 👀
colorFrom: indigo
colorTo: green
sdk: docker
pinned: false
license: mit
short_description: Stateful RL environment for multi-tool AI agents
---

# Agentic Orchestrator Environment

A dynamic, multi-path RL environment for evaluating agent reasoning under uncertainty.

## 🚀 Overview

This simulates real-world incident workflows utilizing logs, CRM platforms, Slack notifications, and terminal commands. Agents must reason through evolving multi-step tasks across a stateful, dynamic pipeline. It is intentionally designed to rigorously test authentic agentic behavior rather than scripted procedural execution.

## 🔥 Key Features

- Stateful environment with evolving system logs
- Multi-path resolution strategies (non-linear workflows)
- Realistic tool usage (logs, CRM, commands, Slack)
- Controlled stochasticity via noise injection
- Partial observability and fuzzy feedback
- Reward shaping for correctness, efficiency, and reasoning
- Strict causal dependencies between actions

## 🧠 What Makes This Different

Traditional environments can be brute-forced or solved with strict LLM templates. This project prevents deterministic execution patterns and requires adaptive reasoning from contextual observations. It successfully supports multiple valid resolution paths while introducing localized uncertainty via noise increments and partial signal matching. By enforcing robust causal consistency across actions, illogical deviation is punished.

The environment is designed to penalize scripted behavior and reward true reasoning.

## ⚙️ Environment Design

The simulation evaluates agent interactions against a continuous state matrix, which includes:
- **logs** (dynamic feedback pipelines)
- **action_history** 
- **observations**
- **flags** (`root_found`, `mitigated`, `notified`)
- **noise_level**

Agents must maneuver through scenarios using strict tool mechanics:
- `search_logs`
- `update_crm`
- `run_command`
- `send_slack`
- `finish_task`

## 🎯 Task Flow (Example)

No single template resolves a crisis. A viable architectural branch might resemble:

1. `search_logs payment`
2. `run_command restart_service`
3. `send_slack devops`
4. `finish_task`

(Multiple valid alternative paths typically exist per scenario.)

## 🏆 Reward System

Scores are normalized dynamically against the scenario's optimal efficiency ceiling:

- **+10** → task completion
- **+5** → correct step
- **+3** → efficient solution
- **-1** → step cost
- **-2** → redundant
- **-5** → invalid sequence
- **-10** → incorrect completion

## 🌐 Live Demo

You can explore the live environment validated on Hugging Face Spaces here:
[https://huggingface.co/spaces/andrewjerryv/OpenEnv-Hackathon](https://huggingface.co/spaces/andrewjerryv/OpenEnv-Hackathon)

## 🛠️ Tech Stack

- Python
- FastAPI
- OpenEnv
- Hugging Face Inference API

## 📌 Summary

This environment provides a realistic benchmark for evaluating agentic AI systems operating under uncertainty, dynamic state transitions, and multi-step reasoning constraints.
