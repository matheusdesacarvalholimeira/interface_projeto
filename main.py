import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import pydeck as pdk
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

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
st.subheader("🌍 Mapa de Calor das Ocorrências")

if "latitude" in df_filtrado.columns and "longitude" in df_filtrado.columns:
    heatmap_layer = pdk.Layer(
        "HeatmapLayer",
        data=df_filtrado,
        get_position="[longitude, latitude]",
        get_weight=1,
        radiusPixels=40,
        intensity=1,
        threshold=0.01,
    )

    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_filtrado,
        get_position="[longitude, latitude]",
        get_color="[200, 30, 0, 160]",
        get_radius=40,
    )

    view_state = pdk.ViewState(
        latitude=df_filtrado["latitude"].mean(),
        longitude=df_filtrado["longitude"].mean(),
        zoom=11,
        pitch=40,
    )

    deck = pdk.Deck(
        layers=[heatmap_layer, scatter_layer],
        initial_view_state=view_state,
        tooltip={"text": "Bairro: {bairro}\\nCrime: {tipo_crime}\\nData: {data_ocorrencia}"}
    )

    st.pydeck_chart(deck)
else:
    st.warning("⚠️ Seu dataset não contém latitude/longitude para gerar o mapa.")
    
#============================================================

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