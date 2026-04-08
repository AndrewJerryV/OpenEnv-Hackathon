from openenv.core.env_server.http_server import create_app
from fastapi.responses import HTMLResponse
import uvicorn
from env.orchestrator_env import OrchestratorEnv, Action, Observation

def env_factory():
    return OrchestratorEnv()

app = create_app(
    env=env_factory, 
    env_name="agentic-orchestrator",
    action_cls=Action,
    observation_cls=Observation
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