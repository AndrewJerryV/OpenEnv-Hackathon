import asyncio
import os
from typing import List, Optional
from openai import OpenAI
from env.orchestrator_env import OrchestratorEnv, Action

# ENV VARIABLES (STRICT)
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN) if HF_TOKEN else None

MAX_STEPS = 6

# LOGGING (STRICT FORMAT)
def log_start(task, env, model):
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step, action, reward, done, error):
    error = error if error else "null"
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error}", flush=True)

def log_end(success, steps, score, rewards):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)

def get_action(state):
    task = state["task"]
    logs = state["logs"]
    history = state["action_history"]
    obs = state["observations"]
    
    system_prompt = (
        "You are an AI resolving live infrastructure incidents dynamically.\n"
        "Output ONLY the exact action string. No natural language.\n"
        "Tools: 'search_logs <keyword>', 'update_crm <status>', 'run_command <cmd>', 'send_slack <message>', 'finish_task'.\n\n"
        "Deduce root causes, apply mitigations, and notify teams in a logical sequential order.\n"
        "Analyze [ERROR] or [WARNING] observations to adapt your strategy dynamically."
    )
    
    user_prompt = f"Task: {task}\nLogs: {logs}\nAction History: {history}\nObservations: {obs}\nNext action:"
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=50
        )
        text = response.choices[0].message.content.strip().split('\n')[-1].lower()
        return text
    except:
        return "noop"

async def main():
    if not client:
        print("[System] API token omitted, agent cannot hit external inference properly locally however structural validation format will proceed normally.")

    env = OrchestratorEnv()

    rewards: List[float] = []
    steps = 0

    try:
        # UPDATED: Get the target task name from the validator environment
        # Default to payment_failure if not set (for local testing)
        target_task = os.getenv("TASK_NAME", "payment_failure")
        
        state = env.reset(scenario_name=target_task)
        
        # UPDATED: Log the dynamic task name so the grader recognizes it
        log_start(target_task, "custom_env", MODEL_NAME)

        for step in range(1, MAX_STEPS + 1):
            action_str = get_action(state)
            action = Action.parse(action_str)
            result = env.step(action)

            reward = result["reward"]
            done = result["done"]
            error = result.get("error")

            rewards.append(reward)
            steps = step

            log_step(step, f"{action.type} {action.value}".strip(), reward, done, error)

            if done:
                break

        # Use environment grader score
        score = result.get("score") if result.get("score") is not None else 0.0
        # Enforce strict (0,1) range to satisfy the validator
        score = min(max(score, 0.01), 0.99)
        success = score > 0.6

    finally:
        env.close()
        log_end(success, steps, score, rewards)

if __name__ == "__main__":
    asyncio.run(main())