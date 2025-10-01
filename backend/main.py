#aqui é o app principal onde todos os roteadores serão incluídos.

from fastapi import FastAPI
from backend.routers import predict, insights

app = FastAPI()

app.include_router(predict.router)
app.include_router(insights.router)

@app.get("/")
async def root():
    return {"mensagem": "API ON"}