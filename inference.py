import asyncio
import os
import re
from typing import List, Optional
from openai import OpenAI
from env.orchestrator_env import OrchestratorEnv, Action

# ENV VARIABLES (STRICT)
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN) if HF_TOKEN else None

# MAX_STEPS mapping by task (Sync with openenv.yaml)
TASK_MAX_STEPS = {
    "payment_failure": 6,
    "deployment_crash": 8,
    "customer_complaint": 10,
    "latency_spike": 12
}
DEFAULT_MAX_STEPS = 8

# LOGGING (STRICT FORMAT)
def log_start(task, env, model):
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step, action, reward, done, error, thought=""):
    error = error if error else "null"
    # Include thought in log for judge transparency, but keep [STEP] format intact
    thought_tag = f" thought=\"{thought}\"" if thought else ""
    print(f"AGENT_REASONING: {thought}") 
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error}", flush=True)

# MODIFICATION: Added 'task' argument and formatted it in the print statement
def log_end(task, success, steps, score, rewards):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] task={task} success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)

# ── Feature 1: Chain-of-Thought (CoT) Prompting & Parsing ────────────
def get_action(state):
    """
    Ask the LLM to produce a THOUGHT before an ACTION.
    Format:  THOUGHT: <reasoning> | ACTION: <command>
    Falls back gracefully if the LLM doesn't follow the format.
    """
    # Handle both plain dicts and OpenEnv Observation objects
    if hasattr(state, "metadata"):
        state = state.metadata
    
    task = state["task"]
    logs = state["logs"]
    history = state["action_history"]
    obs = state["observations"]

    system_prompt = (
        "You are an expert Site-Reliability AI agent resolving live infrastructure incidents.\n"
        "Before acting, you MUST reason about the situation step-by-step.\n\n"
        "── Response Format (STRICT) ──\n"
        "THOUGHT: <your reasoning about what you observe and what to do next>\n"
        "ACTION: <exact tool command>\n\n"
        "── Available Tools ──\n"
        "  search_logs <keyword>    – search logs for a keyword to find root cause\n"
        "  update_crm <status>      – update CRM system with a status\n"
        "  run_command <cmd>         – run an infrastructure command (expensive, may timeout)\n"
        "  send_slack <recipient>    – notify a team via Slack\n"
        "  finish_task               – close the incident (only when fully resolved)\n\n"
        "── Rules ──\n"
        "1. Always search_logs FIRST to identify the root cause before taking mitigation actions.\n"
        "2. If you see [ERROR] Connection timeout, RETRY the same command – tool flakiness is expected.\n"
        "3. Only send_slack AFTER mitigation is confirmed.\n"
        "4. Only finish_task when root cause is found, mitigated, AND team is notified.\n"
        "5. Prefer cheaper actions (search_logs) over expensive ones (run_command) when possible.\n"
        "6. Analyze all [ERROR] and [WARNING] observations to adapt your strategy dynamically.\n"
    )

    user_prompt = (
        f"Task: {task}\n"
        f"Logs: {logs}\n"
        f"Action History: {history}\n"
        f"Observations: {obs}\n\n"
        f"Provide your THOUGHT and then your ACTION:"
    )

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=200,
            temperature=0.2,
        )
        raw = response.choices[0].message.content.strip()
        return parse_thought_action(raw)
    except Exception:
        return ("No LLM response available", "noop")


def parse_thought_action(raw_text: str):
    """
    Parse the LLM output into (thought, action).
    Handles multiple formats robustly:
      - THOUGHT: ... | ACTION: ...
      - THOUGHT: ...\nACTION: ...
      - Just action text (fallback)
    """
    thought = ""
    action = ""

    # Try pipe-delimited format first:  THOUGHT: ... | ACTION: ...
    pipe_match = re.search(
        r"THOUGHT:\s*(.+?)\s*\|\s*ACTION:\s*(.+)",
        raw_text, re.IGNORECASE | re.DOTALL
    )
    if pipe_match:
        thought = pipe_match.group(1).strip()
        action = pipe_match.group(2).strip()
    else:
        # Try newline-delimited format: THOUGHT: ...\nACTION: ...
        thought_match = re.search(r"THOUGHT:\s*(.+?)(?=\n|ACTION:)", raw_text, re.IGNORECASE | re.DOTALL)
        action_match = re.search(r"ACTION:\s*(.+)", raw_text, re.IGNORECASE | re.DOTALL)

        if thought_match:
            thought = thought_match.group(1).strip()
        if action_match:
            action = action_match.group(1).strip()

    # If no ACTION was extracted, treat the entire last line as the action
    if not action:
        action = raw_text.strip().split('\n')[-1].strip()

    # Clean the action: lowercase, strip quotes/backticks, take only first line
    action = action.lower().strip('`"\' ')
    action = action.split('\n')[0].strip()

    # Remove any residual "action:" prefix
    action = re.sub(r'^action:\s*', '', action, flags=re.IGNORECASE)

    return (thought, action)


async def main():
    if not client:
        print("[System] API token omitted, agent cannot hit external inference properly locally however structural validation format will proceed normally.")

    env = OrchestratorEnv()

    try:
        # MODIFICATION: Loop through ALL tasks in TASK_MAX_STEPS
        for target_task, max_steps in TASK_MAX_STEPS.items():
            state = env.reset(scenario_name=target_task)
            
            log_start(target_task, "custom_env", MODEL_NAME)

            rewards: List[float] = []
            steps = 0
            result_info = {}

            for step in range(1, max_steps + 1):
                thought, action_str = get_action(state)
                
                try:
                    action = Action.parse(action_str)
                except Exception as e:
                    print(f"[ERROR] Failed to parse action '{action_str}': {e}")
                    action = Action(type="noop", value="")
                
                result = env.step(action)

                if hasattr(result, "metadata"):
                    reward = result.reward
                    done = result.done
                    error = result.metadata.get("info", {}).get("error")
                    result_info = result.metadata.get("info", {})
                else:
                    reward = result["reward"]
                    done = result["done"]
                    error = result.get("info", {}).get("error") if "info" in result else result.get("error")
                    result_info = result.get("info", {})

                rewards.append(reward)
                steps = step

                log_step(step, f"{action.type} {action.value}".strip(), reward, done, error, thought=thought)

                if done:
                    break

                # Update state for next iteration
                state = env.state

            # MODIFICATION: Clamp score strictly between 0.01 and 0.99
            final_score = result_info.get("score", 0.01) if result_info else 0.01
            final_score = max(0.01, min(0.99, float(final_score)))

            success = final_score > 0.6
            
            # MODIFICATION: Pass target_task into log_end
            log_end(target_task, success, steps, final_score, rewards)

    finally:
        env.close()

if __name__ == "__main__":
    asyncio.run(main())