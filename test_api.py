#!/usr/bin/env python3
"""
Script de teste para verificar se a API está funcionando corretamente
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Testa o endpoint de health check"""
    print("🔍 Testando Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check OK: {data['status']}")
            return True
        else:
            print(f"❌ Health Check falhou: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro no Health Check: {e}")
        return False

def test_models_endpoint():
    """Testa o endpoint de verificação de modelos"""
    print("🤖 Testando verificação de modelos...")
    try:
        response = requests.get(f"{BASE_URL}/health/models")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Modelos disponíveis: {data['models_available']}")
            if not data['models_available']:
                print("⚠️  Alguns modelos não estão disponíveis:")
                for model, status in data['models_status'].items():
                    print(f"   {model}: {'✅' if status else '❌'}")
            return data['models_available']
        else:
            print(f"❌ Verificação de modelos falhou: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro na verificação de modelos: {e}")
        return False

def test_prediction_endpoint():
    """Testa o endpoint de predição"""
    print("🔮 Testando endpoint de predição...")
    
    # Dados de teste
    test_data = {
        "data_ocorrencia": "2024-02-15",
        "latitude": -7.11532,
        "longitude": -34.861,
        "bairro": "Centro",
        "extra_context": {"is_event": 1}
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/predict/",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Predição realizada com sucesso!")
            print(f"📊 Número de predições: {len(data['predictions'])}")
            
            # Mostrar as top 3 predições
            for i, pred in enumerate(data['predictions'][:3], 1):
                print(f"   {i}. {pred['tipo_crime']}: {pred['prob']:.2%}")
            
            return True
        else:
            print(f"❌ Predição falhou: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na predição: {e}")
        return False

def test_root_endpoint():
    """Testa o endpoint raiz"""
    print("🏠 Testando endpoint raiz...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API funcionando: {data['message']}")
            return True
        else:
            print(f"❌ Endpoint raiz falhou: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro no endpoint raiz: {e}")
        return False

def main():
    """Função principal de teste"""
    print("🚔 Teste da API - Sistema de Previsão de Crimes")
    print("=" * 50)
    
    # Aguardar um pouco para o servidor inicializar
    print("⏳ Aguardando servidor inicializar...")
    time.sleep(2)
    
    tests = [
        ("Root Endpoint", test_root_endpoint),
        ("Health Check", test_health_endpoint),
        ("Models Check", test_models_endpoint),
        ("Prediction", test_prediction_endpoint)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        result = test_func()
        results.append((test_name, result))
    
    # Resumo dos testes
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{len(results)} testes passaram")
    
    if passed == len(results):
        print("🎉 Todos os testes passaram! A API está funcionando corretamente.")
    else:
        print("⚠️  Alguns testes falharam. Verifique os logs acima.")

if __name__ == "__main__":
    main()
