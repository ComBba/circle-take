from fastapi import FastAPI
from .schemas import EpisodeBrief, EpisodeState

app = FastAPI(title="Circle Take API", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok", "service": "circle-take"}

@app.post("/api/episodes", response_model=EpisodeState)
def create_episode(brief: EpisodeBrief):
    """Create a golden-path episode shell.

    Implementation TODO:
    1. Build Actor/Style/Story Contracts with Qwen.
    2. Persist episode state.
    3. Return artifact pointers.
    """
    return EpisodeState(
        episode_id="ep01",
        state="DRAFT",
        title=brief.title or "The Last Alarm",
        artifacts={"brief": brief.model_dump()}
    )
