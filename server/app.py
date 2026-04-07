from openenv.core.env_server.http_server import create_app
from env.orchestrator_env import OrchestratorEnv
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
import uvicorn

class Action(BaseModel):
    type: str
    value: str

def env_factory(**kwargs):
    return OrchestratorEnv()

app = create_app(
    env_factory, 
    env_name="agentic-orchestrator",
    action_cls=Action,
    observation_cls=dict
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)