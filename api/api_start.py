import asyncio
import uuid
from fastapi import FastAPI, HTTPException
from shared.broker import publish_task
from shared.state_builder import build_state
from shared.create_graph import app

fastapi_app = FastAPI(title="Food Analyzer API", version="1.0")

# Временное хранилище (заменить на Redis)
results_store = {}

@fastapi_app.post("/analyze")
async def analyze(request: dict):
    request_id = str(uuid.uuid4())
    task = {
        "request_id": request_id,
        "type": request.get("type", "text"),
        "content": request.get("content"),
        "image_base64": request.get("image_base64"),
    }
    await publish_task(task)
    return {"request_id": request_id, "status": "queued"}

@fastapi_app.get("/result/{request_id}")
async def get_result(request_id: str):
    result = results_store.get(request_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found or still processing")
    return {"request_id": request_id, "result": result}

@fastapi_app.post("/analyze_sync")
async def analyze_sync(request: dict):
    initial_state = build_state(request)
    final_state = await app.ainvoke(initial_state)
    answer = final_state.get("messages", [])[-1].content if final_state.get("messages") else ""
    return {"result": answer}

# Запуск через uvicorn (точка входа для Docker)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)
