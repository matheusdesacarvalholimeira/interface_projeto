# 🚔 Sistema de Previsão de Crimes - Interface Projeto

Este é o backend API do Sistema de Previsão de Crimes, desenvolvido com FastAPI para fornecer endpoints de predição e análise de crimes.

## 📋 Funcionalidades

### 🔮 Predição de Crimes
- Endpoint `/predict/` para previsão do tipo de crime mais provável
- Integração com modelos de Machine Learning (Random Forest)
- Suporte a características temporais e geográficas
- Contexto de eventos especiais

### 🏥 Health Checks
- Endpoint `/health/` para verificar status da API
- Endpoint `/health/models` para verificar disponibilidade dos modelos ML

### 📊 Documentação Automática
- Swagger UI disponível em `/docs`
- ReDoc disponível em `/redoc`

## 🚀 Como Executar

### Pré-requisitos
- Python 3.8 ou superior
- Modelos ML treinados na pasta `models/`

### Instalação

1. **Instalar dependências:**
```bash
pip install -r requirements.txt
```

2. **Executar o backend:**
```bash
python run_backend.py
```

3. **Acessar a API:**
```
http://localhost:8000
```

4. **Documentação interativa:**
```
http://localhost:8000/docs
```

## 📁 Estrutura do Projeto

```
interface_projeto/
├── backend/
│   ├── main.py              # Aplicação FastAPI principal
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py        # Endpoints de health check
│   │   └── predict.py       # Endpoints de predição
├── models/                  # Modelos ML treinados
│   ├── modelo_rf.pkl
│   ├── modelo_kmeans.pkl
│   ├── preprocessador.pkl
│   ├── encoder_bairro.pkl
│   ├── encoder_crime.pkl
│   ├── imputer_idade.pkl
│   └── cluster_insights.pkl
├── run_backend.py           # Script de inicialização
├── requirements.txt         # Dependências
└── README.md               # Este arquivo
```

## 🔧 API Endpoints

### Predição de Crimes

**POST** `/predict/`

Faz predição do tipo de crime mais provável baseado nas características fornecidas.

**Request Body:**
```json
{
  "data_ocorrencia": "2024-02-15",
  "latitude": -7.11532,
  "longitude": -34.861,
  "bairro": "Centro",
  "extra_context": {
    "is_event": 1
  }
}
```

**Response:**
```json
{
  "predictions": [
    {
      "tipo_crime": "furto",
      "prob": 0.45
    },
    {
      "tipo_crime": "roubo", 
      "prob": 0.30
    }
  ],
  "metadata": {
    "timestamp": "2024-02-15T10:30:00",
    "model_used": "RandomForest",
    "features_used": ["latitude", "longitude", "bairro", "ano", "mes", "dia", "hora", "dia_semana", "is_weekend", "is_event"],
    "total_predictions": 2
  }
}
```

### Health Check

**GET** `/health/`

Verifica se a API está funcionando.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-02-15T10:30:00",
  "service": "Sistema de Previsão de Crimes API",
  "version": "1.0.0"
}
```

**GET** `/health/models`

Verifica se os modelos ML estão disponíveis.

**Response:**
```json
{
  "models_available": true,
  "models_status": {
    "modelo_rf.pkl": true,
    "modelo_kmeans.pkl": true,
    "preprocessador.pkl": true,
    "encoder_bairro.pkl": true,
    "encoder_crime.pkl": true,
    "imputer_idade.pkl": true,
    "cluster_insights.pkl": true
  },
  "models_path": "../models"
}
```

## 🤖 Modelos de Machine Learning

O sistema utiliza os seguintes modelos ML:

- **Random Forest** (`modelo_rf.pkl`): Modelo principal para predição de tipos de crime
- **K-Means** (`modelo_kmeans.pkl`): Agrupamento de ocorrências similares
- **Preprocessador** (`preprocessador.pkl`): Pipeline de pré-processamento dos dados
- **Encoders**: Codificação de variáveis categóricas (bairro, tipo de crime)
- **Imputer** (`imputer_idade.pkl`): Tratamento de valores faltantes na idade

## 🔍 Características Utilizadas

O modelo utiliza as seguintes características para predição:

- **Geográficas**: latitude, longitude, bairro
- **Temporais**: ano, mês, dia, hora, dia da semana
- **Contextuais**: fim de semana, eventos especiais
- **Demográficas**: idade do suspeito (quando disponível)

## 🔧 Configuração

### CORS
A API está configurada para aceitar requisições do frontend Streamlit em:
- `http://localhost:8501`
- `http://127.0.0.1:8501`

### Porta
Por padrão, a API roda na porta `8000`. Para alterar, modifique o arquivo `run_backend.py`.

## 🚨 Troubleshooting

### Erro ao Carregar Modelos
- Verifique se todos os arquivos `.pkl` estão na pasta `models/`
- Confirme se os modelos foram treinados corretamente
- Verifique as permissões de leitura dos arquivos

### Erro de CORS
- Certifique-se de que o frontend está rodando nas URLs permitidas
- Verifique se não há firewall bloqueando as requisições

### Erro de Dependências
- Execute `pip install -r requirements.txt` novamente
- Verifique se está usando Python 3.8+
- Considere usar um ambiente virtual

## 📝 Logs

A aplicação gera logs detalhados sobre:
- Carregamento de modelos
- Requisições de predição
- Erros e exceções
- Performance da API

## 👥 Equipe

**Responsável:** Equipe de Interface

## 📄 Licença

Este projeto é parte do Sistema de Previsão de Crimes desenvolvido para a Delegacia 5.0.
