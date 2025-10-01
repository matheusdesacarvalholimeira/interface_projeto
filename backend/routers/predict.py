# esse arquivo será responsável pelos endpoints referentes às predições adicionadas via post

from fastapi import APIRouter
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
import uvicorn

try:
    imputer = joblib.load("models/imputer_idade.pkl")
    rf_model = joblib.load("models/modelo_rf.pkl")
    le_bairro = joblib.load("models/encoder_bairro.pkl")
    le_crime = joblib.load("models/encoder_crime.pkl")
except Exception as e:
    print(f"Erro ao carregar modelos: {e}")

router = APIRouter(prefix="/predict")

class Ocorrencia(BaseModel):
    data_ocorrencia: str
    latitude: float
    longitude: float
    bairro: str
    is_event: int
    idade_suspeito: int = 30

@router.post("/")
async def fazerPredicao(ocorrencia: Ocorrencia):
    
    data_dt = datetime.strptime(ocorrencia.data_ocorrencia, "%Y-%m-%d")

    entrada = {
        "ano": data_dt.year,
        "mes": data_dt.month,
        "dia_da_semana": data_dt.weekday(),
        "is_event": ocorrencia.is_event,
        "bairro": ocorrencia.bairro,
        "latitude": ocorrencia.latitude,
        "longitude": ocorrencia.longitude,
        "idade_suspeito": ocorrencia.idade_suspeito
    }

    entrada_df = pd.DataFrame([entrada])

    entrada_df["bairro"] = le_bairro.transform(entrada_df["bairro"].astype(str))
    entrada_df["idade_suspeito"] = imputer.transform(entrada_df[["idade_suspeito"]])

    probs = rf_model.predict_proba(entrada_df)[0]
    classes = le_crime.inverse_transform(np.arange(len(probs)))

    resultados = [{"tipo_crime": crime, "prob":float(prob)} for crime, prob in zip(classes, probs)]
    resultados = sorted(resultados, key=lambda x: x["prob"], reverse=True)
    
    return {"predictions": resultados}