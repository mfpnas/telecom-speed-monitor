import streamlit as st
import pandas as pd
import os
import glob
import plotly.express as px
from datetime import datetime, timedelta
import subprocess
import tempfile
import base64
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Telecom Speed Monitor")

LOG_DIR = os.getenv('LOG_DIR', '/app/data/logs')
st.title("📡 Telecom Speed Monitor Dashboard")

# ------------------------------------------------------------
# 1. LOAD DATA
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
    st.warning("No data found. Waiting for collector to start.")
    st.stop()

# ------------------------------------------------------------
# 2. FILTERS
# ------------------------------------------------------------
st.sidebar.header("🔍 Filters")

# Aviso sobre librespeed (opcional)
st.sidebar.info("💡 If 'librespeed' shows unrealistic values, uncheck it below.")

tools_default = [t for t in df['Tool'].unique() if t != 'librespeed'] if 'librespeed' in df['Tool'].unique() else df['Tool'].unique()
tools = st.sidebar.multiselect("Tools", df['Tool'].unique(), default=tools_default)

min_date = df['Timestamp'].min().date()
max_date = df['Timestamp'].max().date()
start_date = st.sidebar.date_input("Start", min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("End", max_date, min_value=min_date, max_value=max_date)

mask = (df['Tool'].isin(tools)) & (df['Timestamp'].dt.date >= start_date) & (df['Timestamp'].dt.date <= end_date)
filtered = df[mask].copy()

if filtered.empty:
    st.warning("No data with selected filters.")
    st.stop()

# ------------------------------------------------------------
# 3. AUTO REFRESH
# ------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("🔄 Auto Refresh")

refresh_interval = st.sidebar.selectbox(
    "Refresh interval",
    ["Off", "1 minute", "5 minutes", "10 minutes"],
    index=0
)
auto_refresh = refresh_interval != "Off"
if auto_refresh:
    interval_map = {"1 minute": 60, "5 minutes": 300, "10 minutes": 600}
    seconds = interval_map[refresh_interval]
    meta = f'<meta http-equiv="refresh" content="{seconds}">'
    components.html(meta, height=0)

if st.sidebar.button("Refresh Now"):
    st.rerun()

# ------------------------------------------------------------
# 4. QUICK METRICS (com 3 casas decimais e unidade Mbps)
# ------------------------------------------------------------
st.subheader("📊 Summary")
col_metrics = st.columns(4)

avg_dl_mbps = filtered['Download'].mean() / 1e6
avg_ul_mbps = filtered['Upload'].mean() / 1e6
avg_ping = filtered['Ping'].mean()

with col_metrics[0]:
    st.metric("Total Tests", len(filtered))
with col_metrics[1]:
    st.metric("Avg Download", f"{avg_dl_mbps:.3f} Mbps")
with col_metrics[2]:
    st.metric("Avg Upload", f"{avg_ul_mbps:.3f} Mbps")
with col_metrics[3]:
    st.metric("Avg Ping", f"{avg_ping:.1f} ms")

# ------------------------------------------------------------
# 5. TABS
# ------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Time Series", "📊 Boxplot", "📉 Scatter", "📅 Throttling", "📋 Raw Data"])

with tab1:
    fig1 = px.line(filtered, x='Timestamp', y='Download', color='Tool',
                   title='Download Evolution (bps)')
    st.plotly_chart(fig1, use_container_width=True)
    
    fig2 = px.line(filtered, x='Timestamp', y='Upload', color='Tool',
                   title='Upload Evolution (bps)')
    st.plotly_chart(fig2, use_container_width=True)

with tab2:
    fig3 = px.box(filtered, x='Tool', y='Download', color='Tool',
                  title='Download Distribution by Tool')
    st.plotly_chart(fig3, use_container_width=True)
    
    fig4 = px.box(filtered, x='Tool', y='Ping', color='Tool',
                  title='Ping Distribution by Tool')
    st.plotly_chart(fig4, use_container_width=True)

with tab3:
    fig5 = px.scatter(filtered, x='Ping', y='Download', color='Tool',
                      hover_data=['Timestamp', 'Server Name'],
                      title='Ping vs Download (bps)')
    st.plotly_chart(fig5, use_container_width=True)

with tab4:
    filtered['DayOfWeek'] = filtered['Timestamp'].dt.day_name()
    filtered['IsWeekend'] = filtered['DayOfWeek'].isin(['Saturday', 'Sunday'])
    aggr = filtered.groupby(['Tool', 'IsWeekend'])['Download'].mean().reset_index()
    aggr['Period'] = aggr['IsWeekend'].map({True: 'Weekend', False: 'Weekday'})
    aggr['Download_Mbps'] = aggr['Download'] / 1e6  # Converter para Mbps
    
    fig6 = px.bar(aggr, x='Tool', y='Download_Mbps', color='Period', barmode='group',
                  title='Avg Download (Mbps): Weekday vs Weekend (Throttling Detection)')
    st.plotly_chart(fig6, use_container_width=True)

with tab5:
    st.dataframe(filtered[['Timestamp', 'Tool', 'Server Name', 'Ping', 'Download', 'Upload']].head(100))

# ------------------------------------------------------------
# 6. EXPORT FOR PDF REPORT
# ------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("📄 Generate PDF Report")

with st.sidebar.form("pdf_report_form"):
    st.markdown("### Personal Information")
    client_name = st.text_input("Client Name", "Mauricio Faria Palma Nascimento")
    isp_name = st.text_input("ISP Name", "VIVO")
    plan_name = st.text_input("Plan Name", "VIVO TOTAL – PRO (500/250 Mbps)")
    attorney_name = st.text_input("Attorney Name (optional)", "")
    address = st.text_area("Address (CEP, City, State)", "Guaxupé, MG, Brazil")
    
    st.markdown("### Select Data Period")
    export_days = st.slider("Last N days", 1, 30, 7)
    export_tool = st.selectbox("Tool to export", df['Tool'].unique())
    
    uploaded_file = st.file_uploader("Upload Bill (PDF, optional)", type=['pdf'])
    
    submitted = st.form_submit_button("Generate PDF Report")
    
    if submitted:
        with st.spinner("Generating report..."):
            threshold = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=export_days)
            mask_export = (df['Tool'] == export_tool) & (df['Timestamp'] >= threshold)
            export_df = df[mask_export].copy()
            if export_df.empty:
                st.error("No data for the selected period and tool.")
                st.stop()
            
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp_csv:
                export_df.to_csv(tmp_csv.name, index=False)
                csv_path = tmp_csv.name
            
            bill_path = None
            if uploaded_file is not None:
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
                    tmp_pdf.write(uploaded_file.read())
                    bill_path = tmp_pdf.name
            
            cmd = [
                'python', '-u', '/app/scripts/generate_pdf_report.py',
                '--csv', csv_path,
                '--client', client_name,
                '--isp', isp_name,
                '--plan', plan_name,
                '--attorney', attorney_name,
                '--address', address,
                '--output', '/tmp/report.pdf'
            ]
            if bill_path:
                cmd.extend(['--bill', bill_path])
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    with open('/tmp/report.pdf', 'rb') as f:
                        pdf_bytes = f.read()
                    b64 = base64.b64encode(pdf_bytes).decode()
                    href = f'<a href="data:application/pdf;base64,{b64}" download="report.pdf">Download PDF Report</a>'
                    st.sidebar.markdown(href, unsafe_allow_html=True)
                    st.sidebar.success("PDF generated successfully!")
                else:
                    st.sidebar.error(f"PDF generation failed: {result.stderr}")
            except Exception as e:
                st.sidebar.error(f"Error: {e}")
            finally:
                os.unlink(csv_path)
                if bill_path:
                    os.unlink(bill_path)