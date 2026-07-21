
import io
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Castel Brain | Dashboard Comercial",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Castel Brain — Dashboard Comercial")
st.caption("Transforme relatórios em Excel em indicadores comerciais online.")

CAMPOS_PADRAO = {
    "Data": ["data", "periodo", "período", "dia", "mes", "mês"],
    "Empresa": ["empresa", "unidade", "operacao", "operação"],
    "Produto": ["produto", "empreendimento", "imovel", "imóvel"],
    "Imobiliaria": ["imobiliaria", "imobiliária", "agencia", "agência"],
    "Gerente": ["gerente", "gestor"],
    "Corretor": ["corretor", "consultor"],
    "Origem": ["origem", "canal", "fonte", "tipo de venda"],
    "Leads": ["leads", "lead"],
    "Visitas": ["visitas", "visita"],
    "Propostas": ["propostas", "proposta"],
    "Vendas": ["vendas", "venda"],
    "VGV": ["vgv", "valor", "valor de venda", "volume de vendas"]
}

def normalizar_texto(valor):
    return str(valor).strip().lower()

def sugerir_coluna(colunas, alternativas):
    mapa = {normalizar_texto(c): c for c in colunas}
    for alt in alternativas:
        if normalizar_texto(alt) in mapa:
            return mapa[normalizar_texto(alt)]
    for coluna in colunas:
        nome = normalizar_texto(coluna)
        if any(normalizar_texto(alt) in nome for alt in alternativas):
            return coluna
    return None

def ler_arquivo(arquivo):
    if arquivo.name.lower().endswith(".csv"):
        return pd.read_csv(arquivo, sep=None, engine="python")
    return pd.read_excel(arquivo)

def converter_numero(serie):
    if pd.api.types.is_numeric_dtype(serie):
        return pd.to_numeric(serie, errors="coerce").fillna(0)

    texto = serie.astype(str).str.strip()
    texto = texto.str.replace("R$", "", regex=False)
    texto = texto.str.replace(".", "", regex=False)
    texto = texto.str.replace(",", ".", regex=False)
    return pd.to_numeric(texto, errors="coerce").fillna(0)

arquivo = st.file_uploader(
    "Envie seu relatório",
    type=["xlsx", "xls", "csv"]
)

if not arquivo:
    st.info("Envie um arquivo Excel ou CSV para começar.")
    st.stop()

try:
    df_original = ler_arquivo(arquivo)
except Exception as erro:
    st.error(f"Não foi possível ler o arquivo: {erro}")
    st.stop()

if df_original.empty:
    st.warning("O arquivo está vazio.")
    st.stop()

df_original.columns = [str(c).strip() for c in df_original.columns]
colunas = df_original.columns.tolist()

st.sidebar.header("Mapeamento das colunas")
st.sidebar.caption("O sistema tenta identificar os campos automaticamente.")

mapeamento = {}

for campo, alternativas in CAMPOS_PADRAO.items():
    sugestao = sugerir_coluna(colunas, alternativas)
    opcoes = ["Não utilizar"] + colunas
    indice = opcoes.index(sugestao) if sugestao in opcoes else 0

    mapeamento[campo] = st.sidebar.selectbox(
        campo,
        opcoes,
        index=indice,
        key=f"campo_{campo}"
    )

renomear = {
    coluna: campo
    for campo, coluna in mapeamento.items()
    if coluna != "Não utilizar"
}

df = df_original.rename(columns=renomear).copy()

for campo in ["Leads", "Visitas", "Propostas", "Vendas", "VGV"]:
    if campo not in df.columns:
        df[campo] = 0
    df[campo] = converter_numero(df[campo])

if "Data" in df.columns:
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)

for campo in ["Empresa", "Produto", "Imobiliaria", "Gerente", "Corretor", "Origem"]:
    if campo not in df.columns:
        df[campo] = "Não informado"
    df[campo] = df[campo].fillna("Não informado").astype(str).str.strip()

st.sidebar.divider()
st.sidebar.header("Filtros")

df_filtrado = df.copy()

campos_filtro = ["Empresa", "Produto", "Imobiliaria", "Gerente", "Corretor", "Origem"]

for campo in campos_filtro:
    valores = sorted([v for v in df_filtrado[campo].dropna().unique().tolist() if str(v).strip()])
    selecionados = st.sidebar.multiselect(campo, valores)
    if selecionados:
        df_filtrado = df_filtrado[df_filtrado[campo].isin(selecionados)]

if "Data" in df_filtrado.columns and df_filtrado["Data"].notna().any():
    data_min = df_filtrado["Data"].min().date()
    data_max = df_filtrado["Data"].max().date()

    periodo = st.sidebar.date_input(
        "Período",
        value=(data_min, data_max),
        min_value=data_min,
        max_value=data_max
    )

    if isinstance(periodo, tuple) and len(periodo) == 2:
        inicio, fim = periodo
        df_filtrado = df_filtrado[
            (df_filtrado["Data"].dt.date >= inicio) &
            (df_filtrado["Data"].dt.date <= fim)
        ]

total_leads = df_filtrado["Leads"].sum()
total_visitas = df_filtrado["Visitas"].sum()
total_propostas = df_filtrado["Propostas"].sum()
total_vendas = df_filtrado["Vendas"].sum()
total_vgv = df_filtrado["VGV"].sum()

conversao_lead_venda = (total_vendas / total_leads * 100) if total_leads else 0
conversao_visita_venda = (total_vendas / total_visitas * 100) if total_visitas else 0
ticket_medio = (total_vgv / total_vendas) if total_vendas else 0

st.subheader("Visão executiva")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Leads", f"{total_leads:,.0f}".replace(",", "."))
c2.metric("Visitas", f"{total_visitas:,.0f}".replace(",", "."))
c3.metric("Vendas", f"{total_vendas:,.0f}".replace(",", "."))
c4.metric("VGV", f"R$ {total_vgv:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

c5, c6, c7 = st.columns(3)
c5.metric("Propostas", f"{total_propostas:,.0f}".replace(",", "."))
c6.metric("Conversão visita → venda", f"{conversao_visita_venda:.2f}%")
c7.metric("Ticket médio", f"R$ {ticket_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

st.caption(f"Conversão geral de lead para venda: {conversao_lead_venda:.2f}%")

st.divider()

aba1, aba2, aba3, aba4 = st.tabs([
    "Produtos",
    "Imobiliárias",
    "Corretores",
    "Dados"
])

with aba1:
    resumo_produto = (
        df_filtrado.groupby("Produto", as_index=False)
        .agg(
            Leads=("Leads", "sum"),
            Visitas=("Visitas", "sum"),
            Propostas=("Propostas", "sum"),
            Vendas=("Vendas", "sum"),
            VGV=("VGV", "sum")
        )
    )

    resumo_produto["Conversão (%)"] = (
        resumo_produto["Vendas"] / resumo_produto["Visitas"] * 100
    ).replace([float("inf")], 0).fillna(0)

    fig = px.bar(
        resumo_produto.sort_values("VGV", ascending=False),
        x="Produto",
        y="VGV",
        text_auto=".2s",
        title="VGV por produto"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(resumo_produto.sort_values("VGV", ascending=False), use_container_width=True)

with aba2:
    resumo_imobiliaria = (
        df_filtrado.groupby("Imobiliaria", as_index=False)
        .agg(
            Leads=("Leads", "sum"),
            Visitas=("Visitas", "sum"),
            Propostas=("Propostas", "sum"),
            Vendas=("Vendas", "sum"),
            VGV=("VGV", "sum")
        )
    )

    resumo_imobiliaria["Conversão (%)"] = (
        resumo_imobiliaria["Vendas"] / resumo_imobiliaria["Visitas"] * 100
    ).replace([float("inf")], 0).fillna(0)

    fig = px.bar(
        resumo_imobiliaria.sort_values("Vendas", ascending=False),
        x="Imobiliaria",
        y="Vendas",
        text="Vendas",
        title="Vendas por imobiliária"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(resumo_imobiliaria.sort_values("VGV", ascending=False), use_container_width=True)

with aba3:
    resumo_corretor = (
        df_filtrado.groupby(["Gerente", "Corretor"], as_index=False)
        .agg(
            Leads=("Leads", "sum"),
            Visitas=("Visitas", "sum"),
            Propostas=("Propostas", "sum"),
            Vendas=("Vendas", "sum"),
            VGV=("VGV", "sum")
        )
    )

    resumo_corretor["Conversão (%)"] = (
        resumo_corretor["Vendas"] / resumo_corretor["Visitas"] * 100
    ).replace([float("inf")], 0).fillna(0)

    fig = px.bar(
        resumo_corretor.sort_values("VGV", ascending=False).head(20),
        x="Corretor",
        y="VGV",
        text_auto=".2s",
        hover_data=["Gerente", "Vendas", "Visitas"],
        title="Ranking de corretores por VGV"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(resumo_corretor.sort_values("VGV", ascending=False), use_container_width=True)

with aba4:
    st.subheader("Base tratada")
    st.dataframe(df_filtrado, use_container_width=True)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_filtrado.to_excel(writer, index=False, sheet_name="Base Tratada")

    st.download_button(
        "Baixar base tratada em Excel",
        data=buffer.getvalue(),
        file_name="base_tratada_castel.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

