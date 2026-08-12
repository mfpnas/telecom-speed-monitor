import streamlit as st
import pandas as pd
import os
import glob
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Telemetry Monitor")

LOG_DIR = os.getenv('LOG_DIR', '/app/data/logs')
st.title("📡 Telecom Telemetry Dashboard")

# ------------------------------------------------------------
# 1. CARREGAR DADOS
# ------------------------------------------------------------
@st.cache_data(ttl=300)
def load_data():
    all_files = glob.glob(os.path.join(LOG_DIR, '*_speed_logs.csv'))
    dfs = []
    for f in all_files:
        tool = os.path.basename(f).replace('_speed_logs.csv', '')
        df = pd.read_csv(f)
        df['Tool'] = tool
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)

df = load_data()
if df.empty:
    st.warning("Nenhum dado encontrado. Aguarde a coleta.")
    st.stop()

# ------------------------------------------------------------
# 2. FILTROS
# ------------------------------------------------------------
st.sidebar.header("🔍 Filtros Avançados")

# Seleção de ferramentas
tools = st.sidebar.multiselect("Ferramentas", df['Tool'].unique(), default=df['Tool'].unique())

# Intervalo de datas
col1, col2 = st.sidebar.columns(2)
min_date = df['Timestamp'].min().date()
max_date = df['Timestamp'].max().date()
start_date = col1.date_input("Início", min_date, min_value=min_date, max_value=max_date)
end_date = col2.date_input("Fim", max_date, min_value=min_date, max_value=max_date)

# Filtragem
mask = (df['Tool'].isin(tools)) & (df['Timestamp'].dt.date >= start_date) & (df['Timestamp'].dt.date <= end_date)
filtered = df[mask].copy()

if filtered.empty:
    st.warning("Nenhum dado com os filtros selecionados.")
    st.stop()

# ------------------------------------------------------------
# 3. MÉTRICAS RÁPIDAS
# ------------------------------------------------------------
st.subheader("📊 Resumo Geral")
col_metrics = st.columns(4)
with col_metrics[0]:
    st.metric("Testes Totais", len(filtered))
with col_metrics[1]:
    st.metric("Download Médio (Mbps)", f"{filtered['Download'].mean()/1e6:.1f}")
with col_metrics[2]:
    st.metric("Upload Médio (Mbps)", f"{filtered['Upload'].mean()/1e6:.1f}")
with col_metrics[3]:
    st.metric("Ping Médio (ms)", f"{filtered['Ping'].mean():.1f}")

# ------------------------------------------------------------
# 4. GRÁFICOS INTERATIVOS
# ------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Evolução Temporal", "📊 Boxplot", "📉 Dispersão", "📅 Throttling", "📋 Tabela Bruta"])

with tab1:
    # Download
    fig1 = px.line(filtered, x='Timestamp', y='Download', color='Tool',
                   title='Evolução do Download (bps)')
    st.plotly_chart(fig1, use_container_width=True)
    
    # Upload
    fig2 = px.line(filtered, x='Timestamp', y='Upload', color='Tool',
                   title='Evolução do Upload (bps)')
    st.plotly_chart(fig2, use_container_width=True)

with tab2:
    fig3 = px.box(filtered, x='Tool', y='Download', color='Tool',
                  title='Distribuição de Download por Ferramenta')
    st.plotly_chart(fig3, use_container_width=True)
    
    fig4 = px.box(filtered, x='Tool', y='Ping', color='Tool',
                  title='Distribuição de Ping por Ferramenta')
    st.plotly_chart(fig4, use_container_width=True)

with tab3:
    fig5 = px.scatter(filtered, x='Ping', y='Download', color='Tool',
                      hover_data=['Timestamp', 'Server Name'],
                      title='Relação Ping vs Download')
    st.plotly_chart(fig5, use_container_width=True)

with tab4:
    # Throttling: comparação fim de semana vs dia útil
    filtered['DayOfWeek'] = filtered['Timestamp'].dt.day_name()
    filtered['IsWeekend'] = filtered['DayOfWeek'].isin(['Saturday', 'Sunday'])
    aggr = filtered.groupby(['Tool', 'IsWeekend'])['Download'].mean().reset_index()
    aggr['Period'] = aggr['IsWeekend'].map({True: 'Fim de Semana', False: 'Dia Útil'})
    
    fig6 = px.bar(aggr, x='Tool', y='Download', color='Period', barmode='group',
                  title='Download Médio: Dias Úteis vs Fins de Semana')
    st.plotly_chart(fig6, use_container_width=True)

with tab5:
    st.dataframe(filtered[['Timestamp', 'Tool', 'Server Name', 'Ping', 'Download', 'Upload']].head(100))

# ------------------------------------------------------------
# 5. EXPORTAÇÃO PARA O RELATÓRIO PDF
# ------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("📄 Exportar para Relatório")

# Selecionar período e ferramenta
export_tool = st.sidebar.selectbox("Ferramenta para exportar", df['Tool'].unique())
export_days = st.sidebar.slider("Últimos dias", 1, 30, 7)

if st.sidebar.button("Gerar CSV Padronizado"):
    mask_export = (df['Tool'] == export_tool) & (df['Timestamp'] >= datetime.now() - timedelta(days=export_days))
    export_df = df[mask_export].copy()
    
    # Mantém colunas exatas do relatório
    cols = ['Server ID', 'Sponsor', 'Server Name', 'Timestamp', 'Distance', 'Ping', 'Download', 'Upload', 'Share', 'IP Address']
    export_df = export_df[cols]
    
    # Substitui valores NaN/None
    export_df = export_df.fillna('')
    
    csv = export_df.to_csv(index=False)
    st.sideber.download_button(
        label="Baixar CSV",
        data=csv,
        file_name=f"{export_tool}_export_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )