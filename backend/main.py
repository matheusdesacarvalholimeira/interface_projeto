from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import health, predict

app = FastAPI(
    title="Sistema de Previsão de Crimes - API",
    description="API para previsão e análise de crimes",
    version="1.0.0"
)

# Configurar CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],  # Streamlit frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir os roteadores
app.include_router(health.router, tags=["health"])
app.include_router(predict.router, tags=["predict"])

@app.get("/")
async def root():
    return {"message": "Sistema de Previsão de Crimes API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)