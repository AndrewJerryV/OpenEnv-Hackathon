import asyncio
import os
from typing import List, Optional
from openai import OpenAI
from env.orchestrator_env import OrchestratorEnv, Action

# ENV VARIABLES (STRICT)
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

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

def get_action():
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": "Decide next action"}],
            max_tokens=50
        )
        return response.choices[0].message.content.strip()
    except:
        return "search_logs database"

async def main():
    env = OrchestratorEnv()

    rewards: List[float] = []
    steps = 0

    log_start("agentic_orchestrator", "custom_env", MODEL_NAME)

    try:
        state = env.reset()

        for step in range(1, MAX_STEPS + 1):
            action_str = get_action()

            action = Action.parse(action_str)

            result = env.step(action)

            reward = result["reward"]
            done = result["done"]
            error = result.get("error")

            rewards.append(reward)
            steps = step

            log_step(step, action_str, reward, done, error)

            if done:
                break

        score = min(sum(rewards) / 50, 1.0)
        success = score > 0.3

    finally:
        env.close()
        log_end(success, steps, score, rewards)

if __name__ == "__main__":
    asyncio.run(main())