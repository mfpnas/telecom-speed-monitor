import streamlit as st
import pandas as pd
import plotly.express as px
import pytz
from dashboard.data_loader import load_data
from dashboard.filters import apply_time_filters
from dashboard.report_generator import generate_report

# Configuração inicial
st.set_page_config(layout="wide", page_title="Telecom Speed Monitor")
LOG_DIR = "/app/data/logs"
st.title("📡 Telecom Speed Monitor Dashboard")

# PLANOS (mantido)
PLANS = {
    "VIVO": [{"name": "VIVO TOTAL – PRO (500/250 Mbps)", "download": 500, "upload": 250}, ...],
    ...
}
DEFAULT_ISP = "VIVO"
DEFAULT_PLAN = "VIVO TOTAL – PRO (500/250 Mbps)"
DEFAULT_CLIENT = "Mauricio Faria Palma Nascimento"

# Carregar dados
df = load_data(LOG_DIR)
if df.empty:
    st.warning("No data found. Waiting for collector to start.")
    st.stop()

# Sidebar com timezone, filtros, etc.
st.sidebar.header("🌐 Timezone Settings")
timezone_str = st.sidebar.selectbox("Select Timezone", ["UTC", "America/Sao_Paulo", ...], index=1)
user_tz = pytz.timezone(timezone_str)

st.sidebar.markdown("---")
st.sidebar.header("🔍 Filters")
tools = st.sidebar.multiselect("Tools", df['Tool'].unique(), default=df['Tool'].unique())
min_date = df['Timestamp'].min().date()
max_date = df['Timestamp'].max().date()
start_date = st.sidebar.date_input("Start", min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("End", max_date, min_value=min_date, max_value=max_date)

period_options = ["Últimas 6 horas", "Últimas 12 horas", "Últimas 24 horas", "Últimos 3 dias", "Últimos 7 dias", "Completo"]
selected_period = st.selectbox("📅 Período de exibição", period_options, index=0)

# Aplicar filtros
filtered = apply_time_filters(df, tools, start_date, end_date, selected_period)
if filtered.empty:
    st.warning("No data with selected filters.")
    st.stop()

filtered['Timestamp_local'] = filtered['Timestamp'].dt.tz_convert(user_tz)

# Métricas
col_metrics = st.columns(4)
with col_metrics[0]:
    st.metric("Total Tests", len(filtered))
with col_metrics[1]:
    st.metric("Avg Download", f"{filtered['Download'].mean()/1e6:.3f} Mbps")
with col_metrics[2]:
    st.metric("Avg Upload", f"{filtered['Upload'].mean()/1e6:.3f} Mbps")
with col_metrics[3]:
    st.metric("Avg Ping", f"{filtered['Ping'].mean():.1f} ms")

# Tabs (mesmo código original, apenas usando filtered)
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([...])
with tab1:
    fig1 = px.line(filtered, x='Timestamp_local', y='Download', color='Tool', title='Download Evolution (bps)')
    st.plotly_chart(fig1, width='stretch')
    # ... (demais gráficos)

# Seção de exportação
st.sidebar.markdown("---")
st.sidebar.subheader("📄 Generate PDF Report")
isp_list = list(PLANS.keys())
isp_name = st.sidebar.selectbox("ISP Name", isp_list, index=isp_list.index(DEFAULT_ISP))
plans = PLANS[isp_name]
plan_names = [p['name'] for p in plans]
plan_name = st.sidebar.selectbox("Plan Name", plan_names, index=0)

with st.sidebar.form("pdf_report_form"):
    client_name = st.text_input("Client Name", DEFAULT_CLIENT)
    attorney_name = st.text_input("Attorney Name (optional)")
    address = st.text_area("Address", "Guaxupé, MG, Brazil")
    export_days = st.slider("Last N days", 1, 45, 7)
    tool_options = list(df['Tool'].unique()) + ["All Tools"]
    export_tool = st.selectbox("Tool to export", tool_options, index=len(tool_options)-1)
    uploaded_file = st.file_uploader("Upload Bill (PDF, optional)", type=['pdf'])
    submitted = st.form_submit_button("Generate PDF Report")

    if submitted:
        href = generate_report(df, client_name, isp_name, plan_name, attorney_name,
                               address, export_days, export_tool, uploaded_file)
        if href:
            st.sidebar.markdown(href, unsafe_allow_html=True)
            st.sidebar.success("PDF generated successfully!")