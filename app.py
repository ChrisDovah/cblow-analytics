import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

# Configuração inicial da página web
st.set_page_config(
    page_title="CBLOW Analytics",
    page_icon="🏆",
    layout="wide",
)


@st.cache_resource
def conectar_banco():
    """Cria a conexão com o banco SQLite."""
    return sqlite3.connect("cblow.db", check_same_thread=False)


def carregar_dados_times(con):
    """Gera a tabela de classificação das equipes baseada nos jogos finalizados."""
    query = """
    SELECT 
        t.nome AS Time,
        t.tag AS Tag,
        COUNT(j.partida_id) AS 'Jogos Disputados',
        SUM(CASE WHEN j.vencedor_id = t.id THEN 1 ELSE 0 END) AS Vitórias,
        SUM(CASE WHEN j.vencedor_id != t.id AND j.vencedor_id IS NOT NULL THEN 1 ELSE 0 END) AS Derrotas
    FROM times t
    LEFT JOIN jogos j ON (j.vencedor_id = t.id OR (j.vencedor_id IS NOT NULL AND (
        SELECT 1 FROM partidas p WHERE p.id = j.partida_id AND (p.time1_id = t.id OR p.time2_id = t.id)
    )))
    GROUP BY t.id, t.nome, t.tag
    ORDER BY Vitórias DESC, Derrotas ASC
    """
    df = pd.read_sql_query(query, con)
    if not df.empty and df["Jogos Disputados"].sum() > 0:
        df["Win Rate (%)"] = (
            (df["Vitórias"] / df["Jogos Disputados"]) * 100
        ).round(1)
    else:
        df["Win Rate (%)"] = 0.0
    return df


def carregar_campeoes_populares(con):
    """Retorna os campeões mais escolhidos pelos jogadores."""
    query = """
    SELECT 
        campeao AS Campeão,
        COUNT(*) AS 'Vezes Pickado',
        SUM(kills) AS 'Kills Totais',
        SUM(deaths) AS 'Deaths Totais',
        SUM(assists) AS 'Assists Totais'
    FROM stats_jogo
    WHERE campeao IS NOT NULL AND campeao != ''
    GROUP BY campeao
    ORDER BY COUNT(*) DESC
    LIMIT 10
    """
    return pd.read_sql_query(query, con)


# --- INTERFACE PRINCIPAL DO STREAMLIT ---

st.title("🏆 CBLOW - Painel Geral do Campeonato")
st.markdown("Acompanhe o desempenho de equipes e jogadores no campeonato.")

# Conectar ao banco
con = conectar_banco()

# --- BLUCO DE MÉTRICAS RÁPIDAS (KPIs) ---
col1, col2, col3, col4 = st.columns(4)

total_times = pd.read_sql_query("SELECT COUNT(*) AS total FROM times", con)[
    "total"
][0]
total_jogadores = pd.read_sql_query(
    "SELECT COUNT(*) AS total FROM jogadores", con
)["total"][0]
total_partidas = pd.read_sql_query(
    "SELECT COUNT(*) AS total FROM partidas WHERE status = 'finalizada'", con
)["total"][0]
total_jogos = pd.read_sql_query("SELECT COUNT(*) AS total FROM jogos", con)[
    "total"
][0]

col1.metric("Equipes", total_times)
col2.metric("Jogadores", total_jogadores)
col3.metric("Séries Finalizadas", total_partidas)
col4.metric("Mapas/Jogos Totais", total_jogos)

st.divider()

# --- SEÇÃO 1: CLASSIFICAÇÃO DOS TIMES ---
st.subheader("📋 Tabela de Classificação das Equipes")

df_classificacao = carregar_dados_times(con)

if df_classificacao.empty or df_classificacao["Jogos Disputados"].sum() == 0:
    st.info("Ainda não há partidas finalizadas registradas no banco de dados.")
else:
    st.dataframe(
        df_classificacao,
        use_container_width=True,
        hide_index=True,
    )

st.divider()

# --- SEÇÃO 2: GRÁFICOS VISUAIS ---
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.subheader("📊 Campeões Mais Escolhidos (*Picks*)")
    df_champs = carregar_campeoes_populares(con)

    if not df_champs.empty:
        fig_champs = px.bar(
            df_champs,
            x="Campeão",
            y="Vezes Pickado",
            text="Vezes Pickado",
            color="Vezes Pickado",
            color_continuous_scale="Blues",
        )
        fig_champs.update_traces(
            textposition="outside", showlegend=False
        )
        fig_champs.update_layout(xaxis_title="", yaxis_title="Partidas")
        st.plotly_chart(fig_champs, use_container_width=True)
    else:
        st.info("Nenhuma estatística de campeões disponível ainda.")

with col_graf2:
    st.subheader("📈 Taxa de Vitória por Equipe (*Win Rate*)")
    if not df_classificacao.empty and df_classificacao["Jogos Disputados"].sum() > 0:
        fig_wr = px.bar(
            df_classificacao,
            x="Tag",
            y="Win Rate (%)",
            text="Win Rate (%)",
            color="Win Rate (%)",
            color_continuous_scale="Greens",
        )
        fig_wr.update_traces(textposition="outside", showlegend=False)
        fig_wr.update_layout(
            xaxis_title="Time", yaxis_title="Win Rate (%)", yaxis_range=[0, 100]
        )
        st.plotly_chart(fig_wr, use_container_width=True)
    else:
        st.info("Aguardando partidas concluídas para calcular o Win Rate.")