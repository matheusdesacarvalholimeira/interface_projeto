# esse arquivo será responsável pelos endpoints referentes às predições adicionadas via post

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/predict")

class Ocorrencia(BaseModel):
    data_ocorrencia: str
    latitude: float
    longitude: float
    bairro: str
    extra_content: dict

@router.post("/")
async def fazerPredicao(Ocorrencia: Ocorrencia):
    
    pass

    return