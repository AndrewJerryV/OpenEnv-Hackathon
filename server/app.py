from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

@app.post("/reset")
def reset():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h2>Agentic Orchestrator Environment</h2>
    <p>Use /reset endpoint to interact with environment.</p>
    """

def main():
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
