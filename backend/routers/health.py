from fastapi import APIRouter
from datetime import datetime
import os

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check():
    """Endpoint para verificar se a API está funcionando"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Sistema de Previsão de Crimes API",
        "version": "1.0.0"
    }

@router.get("/models")
async def check_models():
    """Verifica se os modelos ML estão disponíveis"""
    models_path = "../models"
    required_models = [
        "modelo_rf.pkl",
        "modelo_kmeans.pkl", 
        "preprocessador.pkl",
        "encoder_bairro.pkl",
        "encoder_crime.pkl",
        "imputer_idade.pkl",
        "cluster_insights.pkl"
    ]
    
    models_status = {}
    all_available = True
    
    for model in required_models:
        model_path = os.path.join(models_path, model)
        exists = os.path.exists(model_path)
        models_status[model] = exists
        if not exists:
            all_available = False
    
    return {
        "models_available": all_available,
        "models_status": models_status,
        "models_path": models_path
    }