from openenv.core.env_server.http_server import create_app
from env.orchestrator_env import OrchestratorEnv
import uvicorn

def env_factory(**kwargs):
    return OrchestratorEnv()

app = create_app(
    env_factory, 
    env_name="agentic-orchestrator"
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)