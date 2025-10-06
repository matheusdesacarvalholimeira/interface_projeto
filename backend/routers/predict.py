from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
import os
from typing import List, Dict, Optional

router = APIRouter(prefix="/predict", tags=["predict"])

class Ocorrencia(BaseModel):
    data_ocorrencia: str
    latitude: float
    longitude: float
    bairro: str
    extra_context: Optional[Dict] = {}

class PredictionResult(BaseModel):
    tipo_crime: str
    prob: float

class PredictionResponse(BaseModel):
    predictions: List[PredictionResult]
    metadata: Dict

# Carregar modelos globalmente (cache)
_models_loaded = False
_rf_model = None
_encoders = {}
_preprocessor = None

def load_models():
    """Carrega os modelos ML necessários"""
    global _models_loaded, _rf_model, _encoders, _preprocessor
    
    if _models_loaded:
        return
    
    models_path = "../models"
    
    try:
        # Carregar modelo Random Forest
        _rf_model = joblib.load(os.path.join(models_path, "modelo_rf.pkl"))
        
        # Carregar encoders
        _encoders['bairro'] = joblib.load(os.path.join(models_path, "encoder_bairro.pkl"))
        _encoders['crime'] = joblib.load(os.path.join(models_path, "encoder_crime.pkl"))
        
        # Carregar preprocessador
        _preprocessor = joblib.load(os.path.join(models_path, "preprocessador.pkl"))
        
        _models_loaded = True
        print("✅ Modelos carregados com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao carregar modelos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao carregar modelos: {str(e)}")

@router.post("/", response_model=PredictionResponse)
async def fazer_predicao(ocorrencia: Ocorrencia):
    """Faz predição do tipo de crime mais provável"""
    
    # Carregar modelos se necessário
    if not _models_loaded:
        load_models()
    
    try:
        # Processar data
        data_ocorrencia = pd.to_datetime(ocorrencia.data_ocorrencia)
        
        # Extrair características temporais
        features = {
            'latitude': ocorrencia.latitude,
            'longitude': ocorrencia.longitude,
            'bairro': ocorrencia.bairro,
            'ano': data_ocorrencia.year,
            'mes': data_ocorrencia.month,
            'dia': data_ocorrencia.day,
            'hora': data_ocorrencia.hour,
            'dia_semana': data_ocorrencia.dayofweek,
            'is_weekend': 1 if data_ocorrencia.dayofweek >= 5 else 0
        }
        
        # Adicionar contexto extra (eventos especiais)
        if ocorrencia.extra_context:
            features.update(ocorrencia.extra_context)
        
        # Criar DataFrame
        df = pd.DataFrame([features])
        
        # Aplicar pré-processamento
        X_processed = _preprocessor.transform(df)
        
        # Fazer predição
        probabilities = _rf_model.predict_proba(X_processed)[0]
        classes = _rf_model.classes_
        
        # Criar lista de predições ordenada por probabilidade
        predictions = []
        for i, (class_name, prob) in enumerate(zip(classes, probabilities)):
            predictions.append(PredictionResult(
                tipo_crime=class_name,
                prob=float(prob)
            ))
        
        # Ordenar por probabilidade (maior primeiro)
        predictions.sort(key=lambda x: x.prob, reverse=True)
        
        # Metadata
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "model_used": "RandomForest",
            "features_used": list(features.keys()),
            "total_predictions": len(predictions)
        }
        
        return PredictionResponse(
            predictions=predictions,
            metadata=metadata
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na predição: {str(e)}")

@router.get("/info")
async def prediction_info():
    """Retorna informações sobre o endpoint de predição"""
    return {
        "endpoint": "/predict",
        "method": "POST",
        "description": "Faz predição do tipo de crime mais provável",
        "required_fields": [
            "data_ocorrencia",
            "latitude", 
            "longitude",
            "bairro"
        ],
        "optional_fields": [
            "extra_context"
        ],
        "models_loaded": _models_loaded
    }