import streamlit as st
import pandas as pd
import os
import glob
import plotly.express as px
from datetime import datetime, timedelta
import subprocess
import tempfile
import base64
import pytz

st.set_page_config(layout="wide", page_title="Telecom Speed Monitor")

LOG_DIR = os.getenv('LOG_DIR', '/app/data/logs')
st.title("📡 Telecom Speed Monitor Dashboard")

# ------------------------------------------------------------
# 1. BRAZILIAN TELECOM PLANS DATASET
# ------------------------------------------------------------
PLANS = {
    "VIVO": [
        {"name": "VIVO TOTAL – PRO (500/250 Mbps)", "download": 500, "upload": 250},
        {"name": "VIVO TOTAL – MAX (300/150 Mbps)", "download": 300, "upload": 150},
        {"name": "VIVO TOTAL – SMART (100/50 Mbps)", "download": 100, "upload": 50},
        {"name": "VIVO FIBRA 700 Mbps", "download": 700, "upload": 350},
        {"name": "VIVO FIBRA 200 Mbps", "download": 200, "upload": 100},
    ],
    "Claro": [
        {"name": "Claro Fibra 500 Mbps", "download": 500, "upload": 250},
        {"name": "Claro Fibra 300 Mbps", "download": 300, "upload": 150},
        {"name": "Claro Fibra 120 Mbps", "download": 120, "upload": 60},
        {"name": "Claro Fibra 50 Mbps", "download": 50, "upload": 25},
    ],
    "TIM": [
        {"name": "TIM LIVE 500 Mbps", "download": 500, "upload": 250},
        {"name": "TIM LIVE 300 Mbps", "download": 300, "upload": 150},
        {"name": "TIM LIVE 100 Mbps", "download": 100, "upload": 50},
    ],
    "Oi": [
        {"name": "Oi Fibra 500 Mbps", "download": 500, "upload": 250},
        {"name": "Oi Fibra 300 Mbps", "download": 300, "upload": 150},
        {"name": "Oi Fibra 100 Mbps", "download": 100, "upload": 50},
    ],
    "Algar": [
        {"name": "Algar Fibra 500 Mbps", "download": 500, "upload": 250},
        {"name": "Algar Fibra 300 Mbps", "download": 300, "upload": 150},
    ],
}

DEFAULT_ISP = "VIVO"
DEFAULT_PLAN = "VIVO TOTAL – PRO (500/250 Mbps)"
DEFAULT_CLIENT = "Mauricio Faria Palma Nascimento"
DEFAULT_TZ = "America/Sao_Paulo"
DEFAULT_REFRESH = "1 minute"

# ------------------------------------------------------------
# 2. LOAD DATA
# ------------------------------------------------------------
@st.cache_data(ttl=300)
def load_data():
    all_files = glob.glob(os.path.join(LOG_DIR, '*_speed_logs.csv'))
    dfs = []
    for f in all_files:
        tool = os.path.basename(f).replace('_speed_logs.csv', '')
        try:
            df = pd.read_csv(f)
        except pd.errors.ParserError:
            df = pd.read_csv(f, on_bad_lines='skip')
        if df.empty:
            continue
        df['Tool'] = tool
        if 'Timestamp' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        elif 'timestamp' in df.columns:
            df.rename(columns={'timestamp': 'Timestamp'}, inplace=True)
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        else:
            mtime = os.path.getmtime(f)
            df['Timestamp'] = pd.to_datetime(mtime, unit='s', utc=True)
        if 'Server Lat' not in df.columns:
            df['Server Lat'] = 0.0
        if 'Server Lon' not in df.columns:
            df['Server Lon'] = 0.0
        dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)

df = load_data()
if df.empty:
    st.warning("No data found. Waiting for collector to start.")
    st.stop()

# ------------------------------------------------------------
# 3. TIMEZONE SELECTOR (default America/Sao_Paulo)
# ------------------------------------------------------------
st.sidebar.header("🌐 Timezone Settings")
timezone_str = st.sidebar.selectbox(
    "Select Timezone",
    ["UTC", "America/Sao_Paulo", "America/New_York", "Europe/London", "Asia/Tokyo"],
    index=1
)
try:
    user_tz = pytz.timezone(timezone_str)
except Exception:
    user_tz = pytz.UTC
    timezone_str = "UTC"

# ------------------------------------------------------------
# 4. FILTERS (with date range display and UTC filtering)
# ------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("🔍 Filters")
tools = st.sidebar.multiselect("Tools", df['Tool'].unique(), default=df['Tool'].unique())

min_date = df['Timestamp'].min().date()
max_date = df['Timestamp'].max().date()
st.sidebar.write(f"Data range: {min_date} to {max_date}")

start_date = st.sidebar.date_input("Start", min_date, min_value=min_date, max_value=max_date, key="start_date")
end_date = st.sidebar.date_input("End", max_date, min_value=min_date, max_value=max_date, key="end_date")

mask = (df['Tool'].isin(tools)) & (df['Timestamp'].dt.date >= start_date) & (df['Timestamp'].dt.date <= end_date)
filtered = df[mask].copy()

if not filtered.empty:
    filtered['Timestamp_local'] = filtered['Timestamp'].dt.tz_convert(user_tz)
else:
    st.warning("No data with selected filters.")
    st.stop()

# ------------------------------------------------------------
# 5. AUTO REFRESH (default 1 minute)
# ------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("🔄 Auto Refresh")
refresh_interval = st.sidebar.selectbox(
    "Refresh interval",
    ["Off", "1 minute", "5 minutes", "10 minutes"],
    index=1
)
auto_refresh = refresh_interval != "Off"
if auto_refresh:
    interval_map = {"1 minute": 60, "5 minutes": 300, "10 minutes": 600}
    seconds = interval_map[refresh_interval]
    st.components.v1.html(
        f'<meta http-equiv="refresh" content="{seconds}">',
        height=0
    )

if st.sidebar.button("Refresh Now"):
    st.rerun()

# ------------------------------------------------------------
# 6. QUICK METRICS
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
# 7. TABS (using width='stretch')
# ------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Time Series", "📊 Boxplot", "📉 Scatter",
    "📅 Throttling", "🗺️ Server Map", "📋 Raw Data"
])

with tab1:
    # Download Evolution
    fig1 = px.line(filtered, x='Timestamp_local', y='Download', color='Tool',
                   title='Download Evolution (bps)')
    fig1.update_xaxes(
        tickformat="%H:%M\n%m/%d",
        dtick=300000,
        rangeslider=dict(visible=True, thickness=0.05),
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1h", step="hour", stepmode="backward"),
                dict(count=6, label="6h", step="hour", stepmode="backward"),
                dict(count=1, label="1d", step="day", stepmode="backward"),
                dict(count=7, label="7d", step="day", stepmode="backward"),
                dict(step="all", label="All")
            ])
        )
    )
    # Mostrar últimos 20 registros inicialmente
    if len(filtered) > 20:
        last_20_time = filtered['Timestamp_local'].iloc[-20]
        fig1.update_xaxes(range=[last_20_time, filtered['Timestamp_local'].max()])
    st.plotly_chart(fig1, width='stretch')
    
    # Upload Evolution
    fig2 = px.line(filtered, x='Timestamp_local', y='Upload', color='Tool',
                   title='Upload Evolution (bps)')
    fig2.update_xaxes(
        tickformat="%H:%M\n%m/%d",
        dtick=300000,
        rangeslider=dict(visible=True, thickness=0.05),
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1h", step="hour", stepmode="backward"),
                dict(count=6, label="6h", step="hour", stepmode="backward"),
                dict(count=1, label="1d", step="day", stepmode="backward"),
                dict(count=7, label="7d", step="day", stepmode="backward"),
                dict(step="all", label="All")
            ])
        )
    )
    if len(filtered) > 20:
        last_20_time = filtered['Timestamp_local'].iloc[-20]
        fig2.update_xaxes(range=[last_20_time, filtered['Timestamp_local'].max()])
    st.plotly_chart(fig2, width='stretch')

with tab2:
    fig3 = px.box(filtered, x='Tool', y='Download', color='Tool',
                  title='Download Distribution by Tool')
    st.plotly_chart(fig3, width='stretch')
    
    fig4 = px.box(filtered, x='Tool', y='Ping', color='Tool',
                  title='Ping Distribution by Tool')
    st.plotly_chart(fig4, width='stretch')

with tab3:
    fig5 = px.scatter(filtered, x='Ping', y='Download', color='Tool',
                      hover_data=['Timestamp_local', 'Server Name'],
                      title='Ping vs Download (bps)')
    st.plotly_chart(fig5, width='stretch')

with tab4:
    filtered['DayOfWeek'] = filtered['Timestamp_local'].dt.day_name()
    filtered['IsWeekend'] = filtered['DayOfWeek'].isin(['Saturday', 'Sunday'])
    aggr = filtered.groupby(['Tool', 'IsWeekend'])['Download'].mean().reset_index()
    aggr['Period'] = aggr['IsWeekend'].map({True: 'Weekend', False: 'Weekday'})
    aggr['Download_Mbps'] = aggr['Download'] / 1e6
    
    fig6 = px.bar(aggr, x='Tool', y='Download_Mbps', color='Period', barmode='group',
                  title='Avg Download (Mbps): Weekday vs Weekend (Throttling Detection)')
    st.plotly_chart(fig6, width='stretch')

with tab5:
    st.subheader("🌍 Server Locations")
    server_locations = filtered[filtered['Server Lat'] != 0].drop_duplicates(
        subset=['Server ID', 'Server Name', 'Server Lat', 'Server Lon']
    )
    if not server_locations.empty:
        fig_map = px.scatter_mapbox(
            server_locations,
            lat='Server Lat',
            lon='Server Lon',
            color='Tool',
            hover_name='Server Name',
            hover_data=['Sponsor', 'Distance'],
            title='Servers Used for Tests',
            mapbox_style='open-street-map',
            zoom=4,
            height=500
        )
        fig_map.update_layout(mapbox_style="open-street-map")
        st.plotly_chart(fig_map, width='stretch')
    else:
        st.info("No server location data available. Only speedtest-cli and librespeed provide this.")

with tab6:
    st.dataframe(filtered[['Timestamp_local', 'Tool', 'Server Name', 'Ping', 'Download', 'Upload']].head(100))

# ------------------------------------------------------------
# 8. EXPORT FOR PDF REPORT
# ------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("📄 Generate PDF Report")

with st.sidebar.form("pdf_report_form"):
    st.markdown("### Personal Information")
    client_name = st.text_input("Client Name", DEFAULT_CLIENT, key="client_name")
    
    isp_list = list(PLANS.keys())
    isp_name = st.selectbox("ISP Name", isp_list, index=isp_list.index(DEFAULT_ISP), key="isp_name")
    
    plans = PLANS[isp_name]
    plan_names = [p['name'] for p in plans]
    default_plan_index = plan_names.index(DEFAULT_PLAN) if DEFAULT_PLAN in plan_names else 0
    plan_name = st.selectbox("Plan Name", plan_names, index=default_plan_index, key="plan_name")
    
    attorney_name = st.text_input("Attorney Name (optional)", "", key="attorney_name")
    address = st.text_area("Address (CEP, City, State)", "Guaxupé, MG, Brazil", key="address")
    
    st.markdown("### Select Data Period")
    export_days = st.slider("Last N days", 1, 30, 7, key="export_days")
    
    tool_options = list(df['Tool'].unique()) + ["All Tools"]
    export_tool = st.selectbox("Tool to export", tool_options, index=len(tool_options)-1, key="export_tool")
    
    uploaded_file = st.file_uploader("Upload Bill (PDF, optional)", type=['pdf'], key="bill_upload")
    
    submitted = st.form_submit_button("Generate PDF Report")
    
    if submitted:
        with st.spinner("Generating report..."):
            threshold = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=export_days)
            
            if export_tool == "All Tools":
                export_df = df[df['Timestamp'] >= threshold].copy()
            else:
                export_df = df[(df['Tool'] == export_tool) & (df['Timestamp'] >= threshold)].copy()
            
            if export_df.empty:
                st.error("No data for the selected period and tool.")
                st.stop()
            
            for col in ['Server ID', 'Sponsor', 'Server Name', 'Distance', 'Ping', 'Download', 'Upload', 'Share', 'IP Address']:
                if col not in export_df.columns:
                    export_df[col] = ''
            
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp_csv:
                export_df.to_csv(tmp_csv.name, index=False)
                csv_path = tmp_csv.name
            
            bill_path = None
            if uploaded_file is not None:
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
                    tmp_pdf.write(uploaded_file.read())
                    bill_path = tmp_pdf.name
            
            start_str = export_df['Timestamp'].min().strftime('%Y%m%d')
            end_str = export_df['Timestamp'].max().strftime('%Y%m%d')
            safe_client = client_name.replace(' ', '_')
            safe_isp = isp_name.replace(' ', '_')
            filename = f"{datetime.now().strftime('%Y%m%d')}_{safe_isp}_{safe_client}_{start_str}-{end_str}.pdf"
            output_path = f"/app/data/logs/{filename}"
            
            cmd = [
                'python', '-u', '/app/scripts/generate_pdf_report.py',
                '--csv', csv_path,
                '--client', client_name,
                '--isp', isp_name,
                '--plan', plan_name,
                '--attorney', attorney_name,
                '--address', address,
                '--output', output_path
            ]
            if bill_path:
                cmd.extend(['--bill', bill_path])
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    with open(output_path, 'rb') as f:
                        pdf_bytes = f.read()
                    b64 = base64.b64encode(pdf_bytes).decode()
                    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Download PDF Report</a>'
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