from fastapi import APIRouter
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np
from datetime import date, timedelta
from typing import Optional
import uvicorn

router = APIRouter(prefix="/insight")

@router.get("/")
async def get_insights(data_inicio: Optional[date] = date.today() - timedelta(days=30), data_fim: Optional[date] = date.today()):
    
    try:
        df = pd.read_csv("dataset_ocorrencias_delegacia.csv")
        df["data_ocorrencia"] = pd.to_datetime(df["data_ocorrencia"], errors='coerce')
        df.dropna(subset=['data_ocorrencia'], inplace=True)
    except FileNotFoundError:
        return {"error": "Dataset principal não encontrado."}
    
    df_filtrado = df.copy()

    df_filtrado = df_filtrado[df_filtrado['data_ocorrencia'].dt.date >= data_inicio]
    df_filtrado = df_filtrado[df_filtrado['data_ocorrencia'].dt.date <= data_fim]

    if df_filtrado.empty:
        return {"message": f"Nenhuma ocorrência encontrada para o período selecionado ({data_inicio} - {data_fim})"}
    
    top_crimes = df_filtrado['tipo_crime'].value_counts().head(10).to_dict()



    return {"top_crimes":top_crimes}

