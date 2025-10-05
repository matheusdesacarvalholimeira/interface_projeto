import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import pydeck as pdk
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import joblib


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
# Use seu CSV real (com latitude e longitude)
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
# STREAMLIT DASHBOARD
# -----------------------
st.set_page_config(page_title="Dashboard de Ocorrências", layout="wide")

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

# -----------------------
# Gráficos
# -----------------------
col1, col2 = st.columns(2)

# Top 10 bairros
bairros = df_filtrado['bairro'].value_counts().head(10).reset_index()
bairros.columns = ["bairro", "quantidade"]
fig_bairros = px.bar(
    bairros,
    x="bairro",
    y="quantidade",
    title="Top 10 Bairros com Mais Ocorrências",
    labels={"bairro": "Bairro", "quantidade": "Quantidade"}
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
    labels={"evento": "Evento", "quantidade": "Quantidade"}
)
col2.plotly_chart(fig_eventos, use_container_width=True)

# Evolução mensal
ocorrencias_mes = df_filtrado.groupby("ano_mes").size().reset_index(name="quantidade")
fig_tempo = px.line(
    ocorrencias_mes,
    x="ano_mes",
    y="quantidade",
    markers=True,
    title="Evolução de Ocorrências por Mês"
)
st.plotly_chart(fig_tempo, use_container_width=True)

# -----------------------
# Tabela interativa
# -----------------------
st.subheader("📑 Dados filtrados")
st.dataframe(df_filtrado)

# -----------------------
# Mapa de calor (heatmap)
# -----------------------
# st.subheader("🌍 Mapa de Calor das Ocorrências")

# if "latitude" in df_filtrado.columns and "longitude" in df_filtrado.columns:
#     heatmap_layer = pdk.Layer(
#         "HeatmapLayer",
#         data=df_filtrado,
#         get_position="[longitude, latitude]",
#         get_weight=1,
#         radiusPixels=40,
#         intensity=1,
#         threshold=0.01,
#     )

#     scatter_layer = pdk.Layer(
#         "ScatterplotLayer",
#         data=df_filtrado,
#         get_position="[longitude, latitude]",
#         get_color="[200, 30, 0, 160]",
#         get_radius=40,
#     )

#     view_state = pdk.ViewState(
#         latitude=df_filtrado["latitude"].mean(),
#         longitude=df_filtrado["longitude"].mean(),
#         zoom=11,
#         pitch=40,
#     )

#     deck = pdk.Deck(
#         layers=[heatmap_layer, scatter_layer],
#         initial_view_state=view_state,
#         tooltip={"text": "Bairro: {bairro}\\nCrime: {tipo_crime}\\nData: {data_ocorrencia}"}
#     )

#     st.pydeck_chart(deck)
# else:
#     st.warning("⚠️ Seu dataset não contém latitude/longitude para gerar o mapa.")

# -----------------------
# Mapa de calor (heatmap) filtrável por bairro
# -----------------------
st.subheader("🌍 Mapa de Calor das Ocorrências por Bairro")

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

#============================================================

# -----------------------
# Gráfico: Crimes por mês
# -----------------------
st.subheader("📈 Crimes mais comuns por mês")

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
    labels={"dia": "Dia do mês", "quantidade": "Ocorrências", "tipo_crime": "Tipo de crime"}
)

st.plotly_chart(fig_crimes, use_container_width=True)

#============================================================

# -----------------------
# Formulário: Previsão de Crimes (inclusive datas futuras)
# -----------------------
st.subheader("🕵️ Prever Crime Mais Provável")

with st.form(key="prever_crime_form"):
    col1, col2 = st.columns(2)
    
    data_input = col1.date_input("Data")
    bairro_input = col1.selectbox("Bairro", [""] + sorted(df_filtrado["bairro"].dropna().unique().tolist()))
    
    latitude_input = col2.number_input("Latitude", value=0.0, format="%.6f")
    longitude_input = col2.number_input("Longitude", value=0.0, format="%.6f")
    
    evento_input = col1.selectbox("Evento", ["Normal"] + sorted(set(df_filtrado["evento_especial"].dropna())))
    
    submit_button = st.form_submit_button(label="Prever crimes")

if submit_button:
    if not bairro_input or latitude_input == 0.0 or longitude_input == 0.0 or not data_input:
        st.warning("⚠️ Preencha todos os campos para prever o crime.")
    else:
        from math import radians, cos, sin, asin, sqrt
        # Função Haversine para distância
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371000  # metros
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            return R * c

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

        # Se houver latitude/longitude, filtra ocorrências próximas (1 km)
        if len(df_filtro) > 0 and "latitude" in df_filtro.columns and "longitude" in df_filtro.columns:
            df_filtro["distancia"] = df_filtro.apply(
                lambda row: haversine(latitude_input, longitude_input, row["latitude"], row["longitude"]),
                axis=1
            )
            df_filtro = df_filtro[df_filtro["distancia"] <= 1000]  # 1 km

            # Se nenhum registro próximo, mantém todos do filtro anterior
            if len(df_filtro) == 0:
                df_filtro = df_filtrado[
                    (df_filtrado["bairro"] == bairro_input)
                ].copy()

        if len(df_filtro) == 0:
            st.info("❌ Não há ocorrências históricas suficientes para prever o crime nesse bairro/evento.")
        else:
            # Calcula crime mais comum
            crime_mais_comum = df_filtro["tipo_crime"].value_counts().idxmax()
            st.success(f"Crime mais provável: **{crime_mais_comum}**")
            st.info(f"Baseado em {len(df_filtro)} ocorrência(s) histórica(s) usadas para previsão.")

#============================================================

st.header("Análise de Agrupamento (Cluster de Ocorrências)")

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

        submit_cluster = st.form_submit_button("🔍 Classificar ocorrência")

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
            "data_ocorrencia": pd.to_datetime(data_ocorrencia_input)
        }])

        # Extrai colunas temporais (ano, mês, dia, hora)
        nova_ocorrencia["ano"] = nova_ocorrencia["data_ocorrencia"].dt.year
        nova_ocorrencia["mes"] = nova_ocorrencia["data_ocorrencia"].dt.month
        nova_ocorrencia["dia"] = nova_ocorrencia["data_ocorrencia"].dt.day
        nova_ocorrencia["hora"] = nova_ocorrencia["data_ocorrencia"].dt.hour

        # Remove a coluna original de data
        nova_ocorrencia = nova_ocorrencia.drop(columns=["data_ocorrencia"])

        try:
            # Aplica o mesmo pré-processamento do treino
            X_proc = preprocessor.transform(nova_ocorrencia)

            # Prediz o cluster
            cluster_pred = int(kmeans.predict(X_proc)[0])

            # Exibe o resultado
            st.success(f"🏷️ A ocorrência pertence ao **Cluster {cluster_pred}**")

            # Exibe insights do cluster, se disponíveis
            if cluster_insights and cluster_pred in cluster_insights:
                info = cluster_insights[cluster_pred]
                st.markdown(f"""
                ### 🔎 Características do Cluster {cluster_pred}
                - **Crimes predominantes:** {', '.join(info['tipos_crime'])}
                - **Bairros mais frequentes:** {', '.join(info['bairros'])}
                - **Faixa etária média dos suspeitos:** {info['idade_media']} anos
                - **Sexo predominante:** {info['sexo_predominante']}
                - **Armas mais usadas:** {', '.join(info['armas'])}
                """)
                
                st.info(info["descricao_textual"])

        except Exception as e:
            st.error(f"Erro ao processar a ocorrência: {e}")

else:
    st.warning("⚠️ Modelos de agrupamento não foram carregados corretamente.")




st.subheader("📑 Ocorrências com Prioridade")

# Mapeamento de cores para cada prioridade
cor_prioridade = {
    "Muito Alta": "background-color: #FF4C4C; color: white",
    "Alta": "background-color: #FF8C42; color: white",
    "Média": "background-color: #FFD166; color: black",
    "Baixa": "background-color: #06D6A0; color: black"
}

# Colunas desejadas
colunas_exibir = [
    "id_ocorrencia", "data_ocorrencia", "bairro", "tipo_crime",
    "quantidade_vitimas", "quantidade_suspeitos", "sexo_suspeito",
    "idade_suspeito", "orgao_responsavel", "status_investigacao",
    "score_prioridade", "prioridade"
]

# Protege caso algumas colunas não existam
colunas_existentes = [c for c in colunas_exibir if c in df2.columns]
if len(colunas_existentes) == 0:
    st.warning("Nenhuma das colunas esperadas está presente no DataFrame (verifique 'df2').")
    st.stop()

df_tabela = df2[colunas_existentes]

# --- Construir opções da AgGrid ---
gb = GridOptionsBuilder.from_dataframe(df_tabela)

# Configure seleção: 'single' permite selecionar uma linha; use_checkbox=False permite selecionar clicando na linha
gb.configure_selection("single", use_checkbox=False)

grid_options = gb.build()

# Garantir que row click selecione (compatibilidade com versões)
# (algumas versões do build colocam as options em 'gridOptions' — tentamos definir em ambos)
if isinstance(grid_options, dict):
    grid_options.setdefault("gridOptions", {})
    grid_options["gridOptions"]["rowSelection"] = "single"
    grid_options["gridOptions"]["suppressRowClickSelection"] = False
    # Também colocar no top-level se necessário
    grid_options["rowSelection"] = "single"
    grid_options["suppressRowClickSelection"] = False

# Renderiza tabela interativa
grid_response = AgGrid(
    df_tabela,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    enable_enterprise_modules=False,
    theme="streamlit",
    fit_columns_on_grid_load=True,
    height=400,  # força altura para garantir que a tabela seja visível
    allow_unsafe_jscode=True
)

# Pega linha selecionada
selected = grid_response["selected_rows"]

# Se for DataFrame, converte para lista de dicts
if hasattr(selected, "to_dict"):
    selected = selected.to_dict(orient="records")

# Verifica se tem seleção
if isinstance(selected, list) and len(selected) > 0:
    st.subheader("🔎 Detalhes da ocorrência selecionada")

    dados = selected[0]  # primeira linha selecionada
    prioridade = dados.get("prioridade", "Baixa")
    cor = cor_prioridade.get(prioridade, "")

    # Exibe em formato de cartão estilizado
    st.markdown(
        f"""
        <div style="padding:16px; border-radius:10px; {cor}">
            <h4>Ocorrência #{dados.get("id_ocorrencia", "")}</h4>
            <p><b>Data:</b> {dados.get("data_ocorrencia", "")}</p>
            <p><b>Bairro:</b> {dados.get("bairro", "")}</p>
            <p><b>Tipo de crime:</b> {dados.get("tipo_crime", "")}</p>
            <p><b>Vítimas:</b> {dados.get("quantidade_vitimas", "")}</p>
            <p><b>Suspeitos:</b> {dados.get("quantidade_suspeitos", "")}</p>
            <p><b>Sexo suspeito:</b> {dados.get("sexo_suspeito", "")}</p>
            <p><b>Idade suspeito:</b> {dados.get("idade_suspeito", "")}</p>
            <p><b>Órgão responsável:</b> {dados.get("orgao_responsavel", "")}</p>
            <p><b>Status investigação:</b> {dados.get("status_investigacao", "")}</p>
            <p><b>Score prioridade:</b> {dados.get("score_prioridade", "")}</p>
            <p><b>Prioridade:</b> {dados.get("prioridade", "")}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.info("👉 Selecione uma ocorrência na tabela para ver os detalhes abaixo.")