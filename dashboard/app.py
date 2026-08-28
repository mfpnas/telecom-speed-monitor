"""Dashboard Streamlit para o Telecom Speed Monitor (Desktop & Mobile)."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pytz
from dashboard.data_loader import load_data
from dashboard.filters import apply_time_filters
from dashboard.report_generator import generate_report


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
LOG_DIR = "/app/data/logs"

# Configuração para otimização
MAX_POINTS_PER_TOOL = 500  # Limite de pontos por ferramenta para renderização

st.markdown("""
<style>
    @media only screen and (max-width: 600px) {
        .css-1d391kg { padding-top: 0.5rem !important; }
        .css-1v7tykx { padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
        .stPlotlyChart { margin-bottom: 10px !important; }
        .stTabs [data-baseweb="tab-list"] button { 
            font-size: 0.75rem !important; 
            padding: 0.3rem 0.5rem !important; 
        }
        .stMetric { font-size: 0.8rem !important; }
        .stMetric label { font-size: 0.8rem !important; }
        .stMetric div { font-size: 1.2rem !important; }
        .stSelectbox, .stMultiselect, .stSlider, .stTextInput, .stTextArea { font-size: 0.9rem !important; }
        .stDataFrame { font-size: 0.7rem !important; }
        .stDataFrame table { font-size: 0.7rem !important; }
        h1 { font-size: 1.5rem !important; }
        h2 { font-size: 1.2rem !important; }
        h3 { font-size: 1.0rem !important; }
        .css-1wvn5lz { width: 80% !important; }
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=60)
def downsample_data(df: pd.DataFrame, max_points: int = MAX_POINTS_PER_TOOL) -> pd.DataFrame:
    """Reduz a quantidade de pontos para renderização, preservando a tendência."""
    if len(df) <= max_points:
        return df
    
    # Agrupa por ferramenta e faz downsample mantendo a tendência
    sampled = []
    for tool in df['Tool'].unique():
        tool_df = df[df['Tool'] == tool]
        if len(tool_df) > max_points:
            # Seleciona pontos uniformemente distribuídos
            indices = np.linspace(0, len(tool_df)-1, max_points).astype(int)
            tool_df = tool_df.iloc[indices]
        sampled.append(tool_df)
    return pd.concat(sampled, ignore_index=True)


def main():
    st.set_page_config(
        layout="wide", 
        page_title="Telecom Speed Monitor",
        initial_sidebar_state="collapsed"
    )
    st.title("📡 Telecom Speed Monitor")

    # Carregar dados (apenas últimos 7 dias por padrão)
    df = load_data(LOG_DIR, max_days=7)
    if df.empty:
        st.warning("No data found. Please wait for the collector to start.")
        st.stop()

    # SIDEBAR: TIMEZONE
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

    # SIDEBAR: FILTERS
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filters")
    tools = st.sidebar.multiselect("Tools", df['Tool'].unique(), default=df['Tool'].unique())

    min_date = df['Timestamp'].min().date()
    max_date = df['Timestamp'].max().date()
    st.sidebar.write(f"Data range: {min_date} to {max_date}")

    start_date = st.sidebar.date_input("Start", min_date, min_value=min_date, max_value=max_date, key="start_date")
    end_date = st.sidebar.date_input("End", max_date, min_value=min_date, max_value=max_date, key="end_date")

    # PERÍODO
    st.markdown("---")
    period_options = [
        "Last 6 hours",
        "Last 12 hours",
        "Last 24 hours",
        "Last 3 days",
        "Last 7 days",
        "Complete"
    ]
    selected_period = st.selectbox(
        "📅 Display Period",
        period_options,
        index=0,
        help="Select the time range for data display"
    )

    # APLICAR FILTROS
    filtered = apply_time_filters(df, tools, start_date, end_date, selected_period)
    if filtered.empty:
        st.warning("No data with the selected filters.")
        st.stop()

    filtered['Timestamp_local'] = filtered['Timestamp'].dt.tz_convert(user_tz)

    # DOWNSAMPLE para melhorar performance
    filtered_display = downsample_data(filtered)

    # MÉTRICAS
    st.subheader("📊 Summary")
    col_metrics = st.columns(4)

    avg_dl_mbps = filtered['Download'].mean() / 1e6 if not filtered.empty else 0
    avg_ul_mbps = filtered['Upload'].mean() / 1e6 if not filtered.empty else 0
    avg_ping = filtered['Ping'].mean() if not filtered.empty else 0

    with col_metrics[0]:
        st.metric("Total Tests", len(filtered))
    with col_metrics[1]:
        st.metric("Avg Download", f"{avg_dl_mbps:.3f} Mbps")
    with col_metrics[2]:
        st.metric("Avg Upload", f"{avg_ul_mbps:.3f} Mbps")
    with col_metrics[3]:
        st.metric("Avg Ping", f"{avg_ping:.1f} ms")

    # TABS
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📈 Time Series", "📊 Boxplot", "📉 Scatter",
        "📅 Throttling", "🗺️ Server Map", "📋 Raw Data",
        "🧠 Smart Analysis"
    ])

    with tab1:
        fig1 = px.line(filtered_display, x='Timestamp_local', y='Download', color='Tool',
                       title='Download Evolution (bps)')
        fig1.update_xaxes(
            tickformat="%H:%M\n%m/%d",
            dtick=300000,
            rangeslider=dict(visible=True, thickness=0.05)
        )
        st.plotly_chart(fig1, width='stretch')

        fig2 = px.line(filtered_display, x='Timestamp_local', y='Upload', color='Tool',
                       title='Upload Evolution (bps)')
        fig2.update_xaxes(
            tickformat="%H:%M\n%m/%d",
            dtick=300000,
            rangeslider=dict(visible=True, thickness=0.05)
        )
        st.plotly_chart(fig2, width='stretch')

    with tab2:
        fig3 = px.box(filtered_display, x='Tool', y='Download', color='Tool',
                      title='Download Distribution by Tool')
        st.plotly_chart(fig3, width='stretch')

        fig4 = px.box(filtered_display, x='Tool', y='Ping', color='Tool',
                      title='Ping Distribution by Tool')
        st.plotly_chart(fig4, width='stretch')

    with tab3:
        fig5 = px.scatter(filtered_display, x='Ping', y='Download', color='Tool',
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
                      title='Avg Download (Mbps): Weekday vs Weekend')
        st.plotly_chart(fig6, width='stretch')

    with tab5:
        st.subheader("🌍 Server Locations")
        fast_data = filtered[filtered['Tool'] == 'fast'].copy()
        if not fast_data.empty:
            fast_data['Server Lat'] = 39.8283
            fast_data['Server Lon'] = -98.5795
            fast_data['Server Name'] = 'Fast.com (Netflix) - Global'
            filtered_map = pd.concat([filtered, fast_data], ignore_index=True)
        else:
            filtered_map = filtered

        server_locations = filtered_map[filtered_map['Server Lat'] != 0].drop_duplicates(
            subset=['Server ID', 'Server Name', 'Server Lat', 'Server Lon']
        )
        if not server_locations.empty:
            # CORREÇÃO: usa px.scatter_map em vez de px.scatter_mapbox
            fig_map = px.scatter_map(
                server_locations,
                lat='Server Lat',
                lon='Server Lon',
                color='Tool',
                hover_name='Server Name',
                hover_data=['Sponsor', 'Distance'],
                title='Servers Used for Tests',
                zoom=4,
                height=400
            )
            st.plotly_chart(fig_map, width='stretch')
        else:
            st.info("No server location data available.")

    with tab6:
        filtered_display = filtered.copy()
        filtered_display['Test Type'] = filtered_display.apply(
            lambda row: 'Download Only' if row['Tool'] == 'fast'
            else 'Full' if row['Upload'] > 0
            else 'Partial',
            axis=1
        )
        st.dataframe(
            filtered_display[[
                'Timestamp_local', 'Tool', 'Server Name', 'Ping',
                'Download', 'Upload', 'Test Type'
            ]].head(100),
            width='stretch',
            hide_index=True
        )

    with tab7:
        st.subheader("🧠 Smart Analysis by Day and Time")
        
        if filtered.empty:
            st.warning("Not enough data for analysis.")
        else:
            filtered['Hour'] = filtered['Timestamp_local'].dt.hour
            filtered['DayOfWeek'] = filtered['Timestamp_local'].dt.day_name()
            filtered['DayNum'] = filtered['DayOfWeek'].map({
                'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
                'Friday': 4, 'Saturday': 5, 'Sunday': 6
            })
            filtered['Download_Mbps'] = filtered['Download'] / 1e6
            filtered['Upload_Mbps'] = filtered['Upload'] / 1e6
            
            # Heatmap de Download
            pivot = filtered.pivot_table(index='DayNum', columns='Hour', values='Download_Mbps', aggfunc='mean')
            pivot = pivot.reindex(index=range(7), columns=range(24))
            
            fig_heatmap = px.imshow(
                pivot,
                labels=dict(x="Hour of Day", y="Day of Week", color="Download (Mbps)"),
                x=[f"{h:02d}:00" for h in range(24)],
                y=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                title="Heatmap: Average Download by Day of Week and Hour",
                color_continuous_scale='YlOrRd'
            )
            st.plotly_chart(fig_heatmap, width='stretch')
            
            # Heatmap de Upload
            pivot_ul = filtered.pivot_table(index='DayNum', columns='Hour', values='Upload_Mbps', aggfunc='mean')
            pivot_ul = pivot_ul.reindex(index=range(7), columns=range(24))
            
            fig_heatmap_ul = px.imshow(
                pivot_ul,
                labels=dict(x="Hour of Day", y="Day of Week", color="Upload (Mbps)"),
                x=[f"{h:02d}:00" for h in range(24)],
                y=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                title="Heatmap: Average Upload by Day of Week and Hour",
                color_continuous_scale='YlGnBu'
            )
            st.plotly_chart(fig_heatmap_ul, width='stretch')
            
            st.markdown("### 📊 Analysis Summary")
            
            threshold_50 = 500 * 0.5
            issues = []
            
            for day in range(7):
                for hour in range(24):
                    val = pivot.loc[day, hour] if pd.notna(pivot.loc[day, hour]) else None
                    if val is not None and val < threshold_50:
                        day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day]
                        issues.append(f"• {day_name} at {hour:02d}:00 - {val:.1f} Mbps ({val/500*100:.1f}% of contract)")
            
            if issues:
                st.warning("**Times with speed below 50% of contracted:**")
                for issue in issues[:20]:
                    st.write(issue)
            else:
                st.success("No times with speed below 50% of contracted.")
            
            weekday_avg = filtered[~filtered['IsWeekend']].groupby('Hour')['Download_Mbps'].mean()
            weekend_avg = filtered[filtered['IsWeekend']].groupby('Hour')['Download_Mbps'].mean()
            
            throttle_issues = []
            for hour in range(24):
                if hour in weekday_avg.index and hour in weekend_avg.index:
                    diff_pct = ((weekday_avg[hour] - weekend_avg[hour]) / weekday_avg[hour]) * 100 if weekday_avg[hour] > 0 else 0
                    if diff_pct > 20:
                        throttle_issues.append(f"• {hour:02d}:00 - {diff_pct:.1f}% reduction on weekends")
            
            if throttle_issues:
                st.warning("**Possible throttling times (difference > 20%):**")
                for issue in throttle_issues[:20]:
                    st.write(issue)
            else:
                st.success("No throttling detected.")
            
            day_avg = filtered.groupby('DayNum')['Download_Mbps'].mean().reindex(range(7))
            worst_day_idx = day_avg.idxmin()
            worst_day = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][worst_day_idx]
            worst_day_value = day_avg[worst_day_idx]
            
            st.info(f"**Worst day of week:** {worst_day} with average of {worst_day_value:.1f} Mbps ({worst_day_value/500*100:.1f}% of contract)")
            
            st.markdown("---")
            st.markdown("**Conclusion:** Analysis identifies patterns of speed degradation at specific times, which may indicate provider infrastructure issues or traffic management practices (throttling).")

    # EXPORTAR PARA PDF (SIDEBAR)
    st.sidebar.markdown("---")
    st.sidebar.subheader("📄 Generate PDF Report")

    isp_list = list(PLANS.keys())
    isp_name = st.sidebar.selectbox(
        "ISP Name",
        isp_list,
        index=isp_list.index(DEFAULT_ISP),
        key="isp_name_export"
    )

    plans = PLANS[isp_name]
    plan_names = [p['name'] for p in plans]

    if 'plan_name_export' not in st.session_state:
        st.session_state.plan_name_export = plan_names[0]
    else:
        if st.session_state.plan_name_export not in plan_names:
            st.session_state.plan_name_export = plan_names[0]

    plan_name = st.sidebar.selectbox(
        "Plan Name",
        plan_names,
        index=plan_names.index(st.session_state.plan_name_export),
        key="plan_name_export"
    )

    with st.sidebar.form("pdf_report_form"):
        st.markdown("### Personal Information")
        client_name = st.text_input("Client Name", DEFAULT_CLIENT, key="client_name")
        attorney_name = st.text_input("Attorney Name (optional)", "", key="attorney_name")
        address = st.text_area("Address (CEP, City, State)", "Guaxupé, MG, Brazil", key="address")

        st.markdown("### Select Data Period")
        export_days = st.slider("Last N days", 1, 45, 7, key="export_days")

        tool_options = list(df['Tool'].unique()) + ["All Tools"]
        export_tool = st.selectbox("Tool to export", tool_options, index=len(tool_options)-1, key="export_tool")

        uploaded_file = st.file_uploader("Upload Bill (PDF, optional)", type=['pdf'], key="bill_upload")

        submitted = st.form_submit_button("Generate PDF Report")

        if submitted:
            plan_download = 500
            plan_upload = 250
            for p in plans:
                if p['name'] == plan_name:
                    plan_download = p['download']
                    plan_upload = p['upload']
                    break

            href = generate_report(
                df=df,
                client_name=client_name,
                isp_name=isp_name,
                plan_name=plan_name,
                attorney_name=attorney_name,
                address=address,
                export_days=export_days,
                export_tool=export_tool,
                uploaded_file=uploaded_file,
                log_dir=LOG_DIR,
                plan_download=plan_download,
                plan_upload=plan_upload,
                valor_mensal=172.00,
                meses=48,
                num_clientes=4500
            )
            if href:
                st.sidebar.markdown(href, unsafe_allow_html=True)
                st.sidebar.success("PDF generated successfully!")


if __name__ == "__main__":
    main()