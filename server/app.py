from openenv.core.env_server.http_server import create_app
from env.orchestrator_env import OrchestratorEnv
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
import uvicorn
from fastapi.responses import HTMLResponse

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

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h2>Agentic Orchestrator Environment</h2>
    <p>Environment is running successfully. API is ready.</p>
    """

def main():
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()