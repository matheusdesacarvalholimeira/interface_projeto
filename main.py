import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import pydeck as pdk
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import joblib
from math import radians, cos, sin, asin, sqrt
import requests
import os


load_dotenv()

# -----------------------
# Processamento dos eventos
# -----------------------
eventos = [
    {"nome": "Carnaval", "data": "20-02-2024"},
    {"nome": "Recife Junino (Sítio Trindade)", "data": "11-06-2024 a 30-06-2024"},
    {"nome": "Festival de Quadrilhas Juninas do Nordeste", "data": "22-06-2024"},
    {"nome": "Festa de Nossa Senhora do Carmo", "data": "06-07-2024 a 16-07-2024"},
    {"nome": "Samba Recife", "data": "28-09-2024 a 29-09-2024"},
    {"nome": "Phase Festival (música eletrônica)", "data": "09-11-2024"},
    {"nome": "Réveillon (Orla da Praia do Pina)", "data": "29-12-2024 a 31-12-2024"}
]

def processar_eventos(eventos, margem=5):
    eventos_processados = []
    for ev in eventos:
        if " a " in ev["data"]:
            inicio_str, fim_str = ev["data"].split(" a ")
            inicio = datetime.strptime(inicio_str, "%d-%m-%Y").date()
            fim = datetime.strptime(fim_str, "%d-%m-%Y").date()
        else:
            data = datetime.strptime(ev["data"], "%d-%m-%Y").date()
            inicio, fim = data, data
        inicio -= timedelta(days=margem)
        fim += timedelta(days=margem)
        eventos_processados.append({"nome": ev["nome"], "inicio": inicio, "fim": fim})
    return eventos_processados

# -----------------------
# Carregando dados
# -----------------------
df = pd.read_csv("dataset_ocorrencias_delegacia_5(in).csv", parse_dates=["data_ocorrencia"])
df2 = pd.read_csv("dataset_ocorrencias_delegacia_prioridade.csv")

# -----------------------
# Marcar eventos especiais
# -----------------------
eventos_proc = processar_eventos(eventos, margem=5)
df["evento_especial"] = "Normal"

for idx, row in df.iterrows():
    data = row["data_ocorrencia"].date()
    for ev in eventos_proc:
        if ev["inicio"] <= data <= ev["fim"]:
            df.loc[idx, "evento_especial"] = ev["nome"]
            break

df["ano_mes"] = df["data_ocorrencia"].dt.to_period("M").astype(str)

# -----------------------
# Configuração da Aplicação
# -----------------------
st.set_page_config(page_title="Sistema de Suporte à Investigação Criminal", layout="wide", initial_sidebar_state="expanded")

# Tema personalizado (opcional, para melhorar visual)
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { background-color: #4CAF50; color: white; }
    .stSelectbox { background-color: white; }
    </style>
""", unsafe_allow_html=True)

# Sidebar para navegação
# Removida a página "Ocorrências Priorizadas" pois será integrada ao Clustering
pagina = st.sidebar.selectbox(
    "Navegação",
    ["Home", "Dashboard", "Mapa de Calor", "Análise Mensal", "Previsão de Crimes", "Agrupamento e Priorização"]
)

# -----------------------
# Página Home: Sobre o Projeto
# -----------------------
if pagina == "Home":
    st.title("Bem-vindo ao Sistema de Suporte à Investigação Criminal")
    
    st.markdown("""
    ### Problema
    O estado de Pernambuco enfrenta altos índices de criminalidade, sendo o líder em taxa de homicídios no Brasil em 2024, com aproximadamente 37.8 homicídios por 100.000 habitantes, resultando em mais de 3.300 homicídios registrados. No contexto nacional, o Brasil registrou cerca de 18.21 homicídios por 100.000 habitantes, mas regiões como o Nordeste, incluindo Pernambuco, apresentam taxas significativamente mais altas. Problemas específicos incluem:
    - Aumento de crimes violentos como latrocínios, feminicídios e roubos.
    - Dificuldade na alocação eficiente de recursos policiais por delegacias e bairros.
    - Necessidade de identificação de padrões criminais para prevenção e investigação mais ágeis.
    
    Estatísticas reais (fontes: Statista, Wikipedia, InSight Crime):
    - Pernambuco: 37.8 homicídios/100k habitantes (2024).
    - Brasil: Quase 45.000 assassinatos totais em 2024, incluindo homicídios e feminicídios.
    - Foco em violência organizada e impactos climáticos que influenciam padrões criminais.
    
    **Perguntas-chave:**
    - Onde e quando há maior risco de ocorrências criminais?
    - Quais padrões distinguem roubos de furtos ou outros crimes?
    - Como correlacionar ocorrências por similaridade (modus operandi, local, tempo)?
    
    ### Nossa Solução
    Desenvolvemos um protótipo funcional (PoC) baseado em Machine Learning para classificar e prever padrões criminais, correlacionar ocorrências e gerar insights visuais. Público-alvo: Equipes de investigação da Polícia Civil de Pernambuco (PC-PE) e setores de inteligência.
    
    **Foco em Aprendizagem Supervisionada:**
    - MVP que resolve classificação (ex.: tipo de crime) e previsão (ex.: probabilidade em janelas de tempo por região).
    - Inclui data storytelling, pipeline de pré-processamento, avaliação quantitativa e justificativa de modelos.
    
    ### Metodologia
    Aplicamos uma abordagem estruturada, priorizando a metodologia sobre a qualidade intrínseca dos dados:
    1. **Definição do Problema:** Baseado em estatísticas reais do mundo (não apenas dados internos) para defender a problemática.
    2. **História de Dados (Data Storytelling):** Contexto, perguntas-chave, visões exploratórias (distribuições, séries temporais, mapas de calor).
    3. **Pipeline de Dados:** Limpeza, balanceamento (SMOTE/undersampling), encoding, split temporal (evitando vazamento).
    4. **Modelagem:** Baseline (DummyClassifier) + Modelos (Regressão Logística, Random Forest, XGBoost). Usamos técnica de cotovelo para clusters ideais (ex.: 2 clusters).
    5. **Métricas:** Precision, Recall, F1, ROC-AUC, Matriz de Confusão, F1@k para hotspots.
    6. **Interpretação:** Importância de features (SHAP), análise de erros.
    7. **Justificativa:** Escolha baseada em desempenho, interpretabilidade e custo.
    8. **Visualizações:** Dashboards interativos com mapas, gráficos e tabelas.
    
    **Requisitos Não Funcionais:**
    - Conformidade com LGPD: Anonimização de dados (sem PII).
    - Reprodutibilidade: requirements.txt, seeds fixas, README com instruções.
    - Organização do Repositório: /data, /notebooks, /src, /reports.
    
    Esta aplicação é deployada no Streamlit Cloud para atualizações automáticas via repositório GitHub.
    """)

# -----------------------
# Página Dashboard
# -----------------------
elif pagina == "Dashboard":
    st.title("📊 Dashboard Interativo de Ocorrências Criminais")
    
    # Filtro por período
    min_date = df["data_ocorrencia"].min()
    max_date = df["data_ocorrencia"].max()
    
    data_range = st.slider(
        "Selecione o período:",
        min_value=min_date.to_pydatetime(),
        max_value=max_date.to_pydatetime(),
        value=(min_date.to_pydatetime(), max_date.to_pydatetime())
    )
    
    df_filtrado = df[(df["data_ocorrencia"] >= data_range[0]) & (df["data_ocorrencia"] <= data_range[1])]
    
    col1, col2 = st.columns(2)
    
    # Top 10 bairros
    bairros = df_filtrado['bairro'].value_counts().head(10).reset_index()
    bairros.columns = ["bairro", "quantidade"]
    fig_bairros = px.bar(
        bairros,
        x="bairro",
        y="quantidade",
        title="Top 10 Bairros com Mais Ocorrências",
        labels={"bairro": "Bairro", "quantidade": "Quantidade"},
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    col1.plotly_chart(fig_bairros, use_container_width=True)
    
    # Ocorrências por evento especial
    contagem_evento = df_filtrado["evento_especial"].value_counts().reset_index()
    contagem_evento.columns = ["evento", "quantidade"]
    fig_eventos = px.bar(
        contagem_evento,
        x="evento",
        y="quantidade",
        title="Ocorrências por Evento Especial (±5 dias)",
        labels={"evento": "Evento", "quantidade": "Quantidade"},
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    col2.plotly_chart(fig_eventos, use_container_width=True)
    
    # Evolução mensal
    ocorrencias_mes = df_filtrado.groupby("ano_mes").size().reset_index(name="quantidade")
    fig_tempo = px.line(
        ocorrencias_mes,
        x="ano_mes",
        y="quantidade",
        markers=True,
        title="Evolução de Ocorrências por Mês",
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    st.plotly_chart(fig_tempo, use_container_width=True)
    
    # Tabela interativa
    st.subheader("📑 Dados Filtrados")
    st.dataframe(df_filtrado, use_container_width=True)

# -----------------------
# Página Mapa de Calor
# -----------------------
elif pagina == "Mapa de Calor":
    st.title("🌍 Mapa de Calor das Ocorrências")
    
    # Filtro por período (reutilizando)
    min_date = df["data_ocorrencia"].min()
    max_date = df["data_ocorrencia"].max()
    data_range = st.slider(
        "Selecione o período:",
        min_value=min_date.to_pydatetime(),
        max_value=max_date.to_pydatetime(),
        value=(min_date.to_pydatetime(), max_date.to_pydatetime())
    )
    df_filtrado = df[(df["data_ocorrencia"] >= data_range[0]) & (df["data_ocorrencia"] <= data_range[1])]
    
    # Lista de bairros com opção "Todos"
    bairros_disponiveis = ["Todos"] + sorted(df_filtrado["bairro"].dropna().unique().tolist())
    bairro_selecionado = st.selectbox("Selecione o bairro:", bairros_disponiveis)
    
    # Filtra o dataframe pelo bairro selecionado
    if bairro_selecionado != "Todos":
        df_heat = df_filtrado[df_filtrado["bairro"] == bairro_selecionado].copy()
    else:
        df_heat = df_filtrado.copy()
    
    if len(df_heat) == 0:
        st.warning("Não há ocorrências para o bairro selecionado.")
    else:
        # Calcula a frequência de cada tipo de crime no bairro
        freq_crimes = df_heat["tipo_crime"].value_counts()
        
        # Normaliza a frequência para criar o peso do heatmap (0 a 1)
        df_heat["peso"] = df_heat["tipo_crime"].map(lambda x: freq_crimes[x])
        df_heat["peso"] = df_heat["peso"] / df_heat["peso"].max()
        
        # Ajusta radiusPixels dinamicamente para não extrapolar o bairro
        raio = max(10, min(40, len(df_heat)))  # mínimo 10, máximo 40
    
        heatmap_layer = pdk.Layer(
            "HeatmapLayer",
            data=df_heat,
            get_position="[longitude, latitude]",
            get_weight="peso",
            radiusPixels=raio,
            intensity=1,
            threshold=0.01,
            get_color="[255 * peso, 0, 0, 160]"  # vermelho mais intenso para crimes mais comuns
        )
    
        # Scatter de pontos mantendo como antes
        scatter_layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_heat,
            get_position="[longitude, latitude]",
            get_color="[200, 30, 0, 160]",
            get_radius=40,
        )
    
        # Centraliza o mapa no bairro selecionado
        view_state = pdk.ViewState(
            latitude=df_heat["latitude"].mean(),
            longitude=df_heat["longitude"].mean(),
            zoom=11,
            pitch=40,
        )
    
        deck = pdk.Deck(
            layers=[heatmap_layer, scatter_layer],
            initial_view_state=view_state,
            tooltip={"text": "Bairro: {bairro}\nCrime: {tipo_crime}\nData: {data_ocorrencia}"}
        )
    
        st.pydeck_chart(deck)

# -----------------------
# Página Análise Mensal
# -----------------------
elif pagina == "Análise Mensal":
    st.title("📈 Análise de Crimes por Mês")
    
    # Lista de meses
    meses = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    mes_selecionado = st.selectbox("Selecione o mês:", meses)
    num_mes = meses.index(mes_selecionado) + 1  # Janeiro = 1
    
    # Filtra df para o mês selecionado (todos os anos)
    df_mes = df[df["data_ocorrencia"].dt.month == num_mes].copy()
    df_mes["dia"] = df_mes["data_ocorrencia"].dt.day
    
    # Conta ocorrências por dia e tipo de crime
    df_agg = df_mes.groupby(["dia", "tipo_crime"]).size().reset_index(name="quantidade")
    
    # Ordena os crimes do mais comum para o menos comum dentro do mês
    top_crimes = df_mes["tipo_crime"].value_counts().index.tolist()
    df_agg["tipo_crime"] = pd.Categorical(df_agg["tipo_crime"], categories=top_crimes, ordered=True)
    
    # Cria gráfico de linhas
    fig_crimes = px.line(
        df_agg,
        x="dia",
        y="quantidade",
        color="tipo_crime",
        title=f"Crimes mais comuns em {mes_selecionado} (todos os anos)",
        labels={"dia": "Dia do mês", "quantidade": "Ocorrências", "tipo_crime": "Tipo de crime"},
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    
    st.plotly_chart(fig_crimes, use_container_width=True)

# -----------------------
# Página Previsão de Crimes
# -----------------------
elif pagina == "Previsão de Crimes":
    st.title("🕵️ Previsão de Crime Mais Provável")

    API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/predict")
    
    # Filtro por período (reutilizando para consistência)
    min_date = df["data_ocorrencia"].min()
    max_date = df["data_ocorrencia"].max()
    data_range = st.slider(
        "Selecione o período histórico para base da previsão:",
        min_value=min_date.to_pydatetime(),
        max_value=max_date.to_pydatetime(),
        value=(min_date.to_pydatetime(), max_date.to_pydatetime())
    )
    df_filtrado = df[(df["data_ocorrencia"] >= data_range[0]) & (df["data_ocorrencia"] <= data_range[1])]
    
    with st.form(key="prever_crime_form"):
        col1, col2 = st.columns(2)
        
        data_input = col1.date_input("Data da Previsão")
        bairro_input = col1.selectbox("Bairro", [""] + sorted(df_filtrado["bairro"].dropna().unique().tolist()))
        evento_input = col2.selectbox("Evento", ["Normal"] + sorted(set(df_filtrado["evento_especial"].dropna())))
        
        submit_button = st.form_submit_button(label="Prever Crimes")
    
    if submit_button:
        if not bairro_input or not data_input:
            st.warning("⚠️ Preencha todos os campos para prever o crime.")
        else:
            st.info("ℹ️ O modelo preditivo atual **não utiliza mais latitude e longitude** para a previsão.")
            
            payload = {
                "data_ocorrencia": data_input.strftime("%Y-%m-%d"),
                "bairro": bairro_input,
                "is_event": 0 if evento_input == "Normal" else 1,
            }

            api_disponivel = False

            with st.spinner('Consultando o modelo de previsão...'):
                try:
                    response = requests.post(API_URL, json=payload, timeout=10)

                    if response.status_code == 200:
                        predictions = response.json().get("predictions")
                        st.subheader("🤖 Previsão do Modelo Preditivo")
                        
                        if predictions:
                            crime_mais_provavel = predictions[0]["tipo_crime"]
                            probabilidade = predictions[0]["prob"]
                            st.success(f"**Crime mais provável: {crime_mais_provavel.upper()}**")
                            st.metric(label="Confiança do Modelo", value=f"{probabilidade:.2%}")
                            api_disponivel = True
                    else:
                        st.error(f"Erro na API de previsão: {response.status_code}")
                        st.caption(response.text)

                except requests.exceptions.RequestException:
                    st.warning("Erro: A API de previsão não está respondendo.")
            
            st.markdown("---")
            
            st.subheader("📈 Análise do Histórico Local")

            # 1. Tenta histórico exato da data + bairro + evento
            df_filtro = df_filtrado[
                (df_filtrado["bairro"] == bairro_input) &
                (df_filtrado["evento_especial"] == evento_input) &
                (df_filtrado["data_ocorrencia"].dt.date == data_input)
            ].copy()
    
            # 2. Se vazio, histórico do mesmo evento no bairro
            if len(df_filtro) == 0 and evento_input != "Normal":
                df_filtro = df_filtrado[
                    (df_filtrado["bairro"] == bairro_input) &
                    (df_filtrado["evento_especial"] == evento_input)
                ].copy()
    
            # 3. Se ainda vazio, histórico do mesmo bairro (qualquer evento)
            if len(df_filtro) == 0:
                df_filtro = df_filtrado[
                    (df_filtrado["bairro"] == bairro_input)
                ].copy()
    
            # 4. Se ainda vazio, histórico geral (qualquer bairro/evento)
            if len(df_filtro) == 0:
                df_filtro = df_filtrado.copy()
    
            if len(df_filtro) == 0:
                st.info("❌ Não há ocorrências históricas suficientes para prever o crime nesse bairro/evento.")
            else:
                # Calcula crime mais comum
                crime_mais_comum = df_filtro["tipo_crime"].value_counts().idxmax()
                st.success(f"Crime mais provável: **{crime_mais_comum}**")
                st.info(f"Baseado em {len(df_filtro)} ocorrência(s) histórica(s) usadas para previsão.")

                
# -----------------------
# Página Agrupamento e Priorização (Clustering + Prioridade)
# -----------------------
elif pagina == "Agrupamento e Priorização":
    st.title("🔍 Análise de Agrupamento e Priorização de Ocorrências")
    
    # Configuração do classificador de prioridade (copiado do script do colega)
    DEFAULT_CONFIG = {
        "crime_weight_map": {
            "homicídio": 100,
            "homicidio": 100,
            "homicide": 100,
            "estupro": 95,
            "sequestro": 90,
            "roubo": 70,
            "furto": 40,
            "fraude": 30,
            "arrombamento": 50,
            "outro": 20
        },
        "keyword_crime_weight_map": {
            "homicídio": 100,
            "homicidio": 100,
            "assassinato": 100,
            "estupro": 95,
            "sequestro": 90
        },
        "weapon_weight_map": {
            "arma de fogo": 40,
            "arma de fogo (outra)": 40,
            "faca": 25,
            "objeto contundente": 20,
            "nenhum": 0,
            "sem": 0
        },
        "modus_keyword_bonus": {
            "estupro": 10,
            "coletivo": 3,
            "golpe": 5,
            "fraude": 5,
            "invas\u00e3o": 5,
            "arrombamento": 5,
            "sequestro": 10
        },
        "victim_weight": 10,
        "suspect_weight": 5,
        "thresholds": {
            "muito_alta": 120,
            "alta": 80,
            "media": 40
        }
    }

    def clean_text(x):
        if pd.isna(x):
            return ""
        return str(x).lower()

    def get_crime_weight(tipo_crime, descricao, cfg):
        tipo = clean_text(tipo_crime).strip()
        crime_map = cfg["crime_weight_map"]
        base = None
        if tipo in crime_map:
            base = crime_map[tipo]
        else:
            for k, v in crime_map.items():
                if k in tipo and k != "outro":
                    base = v
                    break
        if base is None:
            base = cfg["crime_weight_map"].get("outro", 20)

        desc = clean_text(descricao)
        max_kw = 0
        for kw, w in cfg["keyword_crime_weight_map"].items():
            if kw in desc:
                max_kw = max(max_kw, w)
        return max(base, max_kw)

    def get_weapon_weight(arma, cfg):
        a = clean_text(arma).strip()
        wm = cfg["weapon_weight_map"]
        for k, v in wm.items():
            if k in a:
                return v
        return 0

    def modus_bonus(descricao, cfg):
        desc = clean_text(descricao)
        bonus = 0
        for k, v in cfg["modus_keyword_bonus"].items():
            if k in desc:
                bonus += v
        return bonus


    def safe_int(x):
        try:
            if pd.isna(x):
                return 0
            return int(float(re.sub(r"[^0-9.-]", "", str(x))))
        except Exception:
            return 0

    def score_row(row, cfg):
        tipo = row.get("tipo_crime", "")
        descricao = row.get("descricao_modus_operandi", "")
        arma = row.get("arma_utilizada", "")

        crime_w = get_crime_weight(tipo, descricao, cfg)
        weapon_w = get_weapon_weight(arma, cfg)
        victims = safe_int(row.get("quantidade_vitimas", 0))
        suspects = safe_int(row.get("quantidade_suspeitos", 0))

        s = 0
        s += crime_w
        s += weapon_w
        s += victims * cfg["victim_weight"]
        s += suspects * cfg["suspect_weight"]
        s += modus_bonus(descricao, cfg)

        if weapon_w == 0 and victims >= 3 and suspects >= 2:
            s += 5

        if s < 0:
            s = 0
        return s

    def score_to_label(score, cfg):
        t = cfg["thresholds"]
        if score >= t["muito_alta"]:
            return "Muito Alta"
        if score >= t["alta"]:
            return "Alta"
        if score >= t["media"]:
            return "Média"
        return "Baixa"

    # Carregamento dos modelos de clustering
    try:
        kmeans = joblib.load("models/modelo_kmeans.pkl")
        preprocessor = joblib.load("models/preprocessador.pkl")
        cluster_insights = joblib.load("models/cluster_insights.pkl")
        modelo_carregado = True
    except Exception as e:
        st.error(f"Erro ao carregar os modelos: {e}")
        modelo_carregado = False

    if modelo_carregado:
        st.subheader("Insira os dados da nova ocorrência:")

        with st.form("form_cluster"):
            col1, col2 = st.columns(2)

            descricao = col1.text_area("Descrição do modus operandi", "")
            bairro = col1.selectbox("Bairro", sorted(df["bairro"].dropna().unique().tolist()))
            tipo_crime = col1.selectbox("Tipo de crime", sorted(df["tipo_crime"].dropna().unique().tolist()))
            arma = col2.selectbox("Arma utilizada", sorted(df["arma_utilizada"].dropna().unique().tolist()))
            sexo_suspeito = col2.selectbox("Sexo do suspeito", ["Masculino", "Feminino", "Não informado"])
            idade_suspeito = col2.number_input("Idade do suspeito", min_value=10, max_value=90, value=25)
            qtd_vitimas = col1.number_input("Quantidade de vítimas", min_value=0, value=1)
            qtd_suspeitos = col1.number_input("Quantidade de suspeitos", min_value=1, value=1)
            data_input = col1.date_input("Data da ocorrência", value=pd.Timestamp.now().date())
            hora_input = col2.time_input("Hora da ocorrência", value=pd.Timestamp.now().time())
            
            submit_cluster = st.form_submit_button("Classificar Ocorrência")

        if submit_cluster:
            data_ocorrencia_input = pd.to_datetime(f"{data_input} {hora_input}")
            nova_ocorrencia = pd.DataFrame([{
                "descricao_modus_operandi": descricao,
                "bairro": bairro,
                "tipo_crime": tipo_crime,
                "arma_utilizada": arma,
                "sexo_suspeito": sexo_suspeito,
                "quantidade_vitimas": qtd_vitimas,
                "quantidade_suspeitos": qtd_suspeitos,
                "idade_suspeito": idade_suspeito,
                "data_ocorrencia": data_ocorrencia_input
            }])

            # -----------------------
            # Processamento para Clustering
            # -----------------------
            # Extrai colunas temporais (ano, mês, dia, hora)
            nova_ocorrencia["ano"] = nova_ocorrencia["data_ocorrencia"].dt.year
            nova_ocorrencia["mes"] = nova_ocorrencia["data_ocorrencia"].dt.month
            nova_ocorrencia["dia"] = nova_ocorrencia["data_ocorrencia"].dt.day
            nova_ocorrencia["hora"] = nova_ocorrencia["data_ocorrencia"].dt.hour

            # Remove a coluna original de data
            nova_ocorrencia_cluster = nova_ocorrencia.drop(columns=["data_ocorrencia"])

            try:
                # Aplica o mesmo pré-processamento do treino
                X_proc = preprocessor.transform(nova_ocorrencia_cluster)

                # Prediz o cluster
                cluster_pred = int(kmeans.predict(X_proc)[0])

                # Exibe o resultado do clustering
                st.success(f"A ocorrência pertence ao **Cluster {cluster_pred}**")

                # Exibe insights do cluster, se disponíveis
                if cluster_insights and cluster_pred in cluster_insights:
                    info = cluster_insights[cluster_pred]
                    st.markdown(f"""
                    ### Características do Cluster {cluster_pred}
                    - **Crimes predominantes:** {', '.join(info['tipos_crime'])}
                    - **Bairros mais frequentes:** {', '.join(info['bairros'])}
                    - **Faixa etária média dos suspeitos:** {info['idade_media']} anos
                    - **Sexo predominante:** {info['sexo_predominante']}
                    - **Armas mais usadas:** {', '.join(info['armas'])}
                    """)
                    
                    st.info(info["descricao_textual"])

            except Exception as e:
                st.error(f"Erro ao processar a ocorrência para clustering: {e}")

            # -----------------------
            # Processamento para Priorização
            # -----------------------
            # Calcula score e prioridade usando as funções do classificador
            cfg = DEFAULT_CONFIG
            row = nova_ocorrencia.iloc[0]
            score = score_row(row, cfg)
            prioridade = score_to_label(score, cfg)

            # Mapeamento de cores para cada prioridade
            cor_prioridade = {
                "Muito Alta": "background-color: #FF4C4C; color: white",
                "Alta": "background-color: #FF8C42; color: white",
                "Média": "background-color: #FFD166; color: black",
                "Baixa": "background-color: #06D6A0; color: black"
            }

            cor = cor_prioridade.get(prioridade, "")

            # Exibe em formato de cartão estilizado
            st.subheader("🔎 Detalhes e Prioridade da Ocorrência")
            st.markdown(
                f"""
                <div style="padding:16px; border-radius:10px; {cor}">
                    <p><b>Data:</b> {row["data_ocorrencia"]}</p>
                    <p><b>Bairro:</b> {row.get("bairro", "")}</p>
                    <p><b>Tipo de crime:</b> {row.get("tipo_crime", "")}</p>
                    <p><b>Vítimas:</b> {row.get("quantidade_vitimas", "")}</p>
                    <p><b>Suspeitos:</b> {row.get("quantidade_suspeitos", "")}</p>
                    <p><b>Sexo suspeito:</b> {row.get("sexo_suspeito", "")}</p>
                    <p><b>Idade suspeito:</b> {row.get("idade_suspeito", "")}</p>
                    <p><b>Score prioridade:</b> {score}</p>
                    <p><b>Prioridade:</b> {prioridade}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    else:
        st.warning("⚠️ Modelos de agrupamento não foram carregados corretamente.")
