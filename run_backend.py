#!/usr/bin/env python3
"""
Script para executar o backend do Sistema de Previsão de Crimes
"""

import uvicorn
import os
import sys

# Adicionar o diretório backend ao path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    print("🚀 Iniciando Sistema de Previsão de Crimes - Backend API")
    print("📍 URL: http://localhost:8000")
    print("📚 Documentação: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health/")
    print("-" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
