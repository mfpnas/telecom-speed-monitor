"""Dashboard Streamlit para o Telecom Speed Monitor."""

import streamlit as st
import pandas as pd
import plotly.express as px
import pytz
from .data_loader import load_data
from .filters import apply_time_filters
from .report_generator import generate_report


# ------------------------------------------------------------
# PLANOS DE INTERNET (BRASIL)
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
LOG_DIR = "/app/data/logs"


def main():
    """Função principal do dashboard."""
    # Configuração da página
    st.set_page_config(layout="wide", page_title="Telecom Speed Monitor")
    st.title("📡 Telecom Speed Monitor Dashboard")

    # Carregar dados
    df = load_data(LOG_DIR)
    if df.empty:
        st.warning("Nenhum dado encontrado. Aguarde o coletor iniciar.")
        st.stop()

    # ------------------------------------------------------------
    # SIDEBAR: TIMEZONE E FILTROS
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

    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filters")
    tools = st.sidebar.multiselect("Tools", df['Tool'].unique(), default=df['Tool'].unique())

    min_date = df['Timestamp'].min().date()
    max_date = df['Timestamp'].max().date()
    st.sidebar.write(f"Data range: {min_date} to {max_date}")

    start_date = st.sidebar.date_input("Start", min_date, min_value=min_date, max_value=max_date, key="start_date")
    end_date = st.sidebar.date_input("End", max_date, min_value=min_date, max_value=max_date, key="end_date")

    # ------------------------------------------------------------
    # PERÍODO PRINCIPAL
    # ------------------------------------------------------------
    st.markdown("---")
    period_options = [
        "Últimas 6 horas",
        "Últimas 12 horas",
        "Últimas 24 horas",
        "Últimos 3 dias",
        "Últimos 7 dias",
        "Completo"
    ]
    selected_period = st.selectbox(
        "📅 Período de exibição",
        period_options,
        index=0,
        help="Selecione o intervalo de tempo para exibição dos dados"
    )

    # ------------------------------------------------------------
    # APLICAR FILTROS
    # ------------------------------------------------------------
    filtered = apply_time_filters(df, tools, start_date, end_date, selected_period)
    if filtered.empty:
        st.warning("Nenhum dado com os filtros selecionados.")
        st.stop()

    filtered['Timestamp_local'] = filtered['Timestamp'].dt.tz_convert(user_tz)

    # ------------------------------------------------------------
    # MÉTRICAS RESUMO
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    # TABS
    # ------------------------------------------------------------
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Time Series", "📊 Boxplot", "📉 Scatter",
        "📅 Throttling", "🗺️ Server Map", "📋 Raw Data"
    ])

    with tab1:
        fig1 = px.line(filtered, x='Timestamp_local', y='Download', color='Tool',
                       title='Download Evolution (bps)')
        fig1.update_xaxes(
            tickformat="%H:%M\n%m/%d",
            dtick=300000,
            rangeslider=dict(visible=True, thickness=0.05)
        )
        st.plotly_chart(fig1, width='stretch')

        fig2 = px.line(filtered, x='Timestamp_local', y='Upload', color='Tool',
                       title='Upload Evolution (bps)')
        fig2.update_xaxes(
            tickformat="%H:%M\n%m/%d",
            dtick=300000,
            rangeslider=dict(visible=True, thickness=0.05)
        )
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
            ]].head(100)
        )

    # ------------------------------------------------------------
    # EXPORTAR PARA PDF
    # ------------------------------------------------------------
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
            # Extrair velocidades do plano selecionado
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
                valor_mensal=172.00,      # pode ser ajustado conforme necessário
                meses=48,
                num_clientes=4500
            )
            if href:
                st.sidebar.markdown(href, unsafe_allow_html=True)
                st.sidebar.success("PDF generated successfully!")


if __name__ == "__main__":
    main()