"""
Dashboard Streamlit para Análise de Estabelecimentos RFB
Autor: Felipe
Data: 2025-10-14
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import utils

# Configuração da página
st.set_page_config(
    page_title="Dashboard RFB - Estabelecimentos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_data
def load_dataset():
    """
    Carrega o dataset principal a partir de múltiplos arquivos divididos.
    
    ⚠️ ALTERAÇÃO: Agora carrega 4 arquivos ao invés de 1
    """
    # Lista dos arquivos divididos
    arquivos = [
        "dados/estabelecimentos_filtrado_parte1.csv",
        "dados/estabelecimentos_filtrado_parte2.csv",
        "dados/estabelecimentos_filtrado_parte3.csv",
        "dados/estabelecimentos_filtrado_parte4.csv"
    ]
    
    # Lista para armazenar os DataFrames
    dfs = []
    
    # Carregar cada arquivo
    for i, arquivo in enumerate(arquivos, 1):
        try:
            df_temp = utils.load_data(arquivo)
            dfs.append(df_temp)
        except Exception as e:
            st.warning(f"⚠️ Erro ao carregar {arquivo}: {str(e)}")
    
    # Concatenar todos os DataFrames
    if dfs:
        df_completo = pd.concat(dfs, ignore_index=True)
        return df_completo
    else:
        raise Exception("Nenhum arquivo foi carregado com sucesso!")


def main():
    # Header principal
    st.markdown('<p class="main-header">📊 Dashboard de Análise - Estabelecimentos RFB</p>', unsafe_allow_html=True)
    st.markdown("---")

    # Carregar dados
    with st.spinner("Carregando dados... Isso pode levar alguns segundos."):
        try:
            df = load_dataset()
        except Exception as e:
            st.error(f"❌ Erro ao carregar dados: {str(e)}")
            st.stop()

    # Sidebar - Filtros
    st.sidebar.header("🔍 Filtros")

    # Filtro de situação cadastral
    situacoes_disponiveis = sorted(df['situacao_descricao'].dropna().unique().tolist())
    situacoes_selecionadas = st.sidebar.multiselect(
        "Situação Cadastral",
        options=situacoes_disponiveis,
        default=[]
    )

    # Filtro de tipo (matriz/filial)
    tipos_disponiveis = sorted(df['tipo_estabelecimento'].dropna().unique().tolist())
    tipos_selecionados = st.sidebar.multiselect(
        "Tipo de Estabelecimento",
        options=tipos_disponiveis,
        default=[]
    )

    # Filtro de município
    municipios_disponiveis = sorted(df['nome_municipio'].dropna().unique().tolist())
    municipios_selecionados = st.sidebar.multiselect(
        "Município",
        options=municipios_disponiveis,
        default=[]
    )

    # Filtro de ano de início
    anos_disponiveis = sorted([int(x) for x in df['ano_inicio'].dropna().unique() if 1900 <= x <= datetime.now().year])
    if anos_disponiveis:
        ano_min, ano_max = min(anos_disponiveis), max(anos_disponiveis)
        anos_selecionados = st.sidebar.slider(
            "Ano de Início da Atividade",
            min_value=ano_min,
            max_value=ano_max,
            value=(ano_min, ano_max)
        )
    else:
        anos_selecionados = None

    # Aplicar filtros
    filters = {}
    if situacoes_selecionadas:
        filters['situacao_descricao'] = situacoes_selecionadas
    if tipos_selecionados:
        filters['tipo_estabelecimento'] = tipos_selecionados
    if municipios_selecionados:
        filters['nome_municipio'] = municipios_selecionados

    df_filtered = utils.filter_dataframe(df, filters)

    # Aplicar filtro de ano
    if anos_selecionados:
        df_filtered = df_filtered[
            (df_filtered['ano_inicio'] >= anos_selecionados[0]) &
            (df_filtered['ano_inicio'] <= anos_selecionados[1])
        ]

    # Informação sobre filtros aplicados
    if len(df_filtered) < len(df):
        st.sidebar.info(f"📌 Mostrando {len(df_filtered):,} de {len(df):,} estabelecimentos")

    # Botão para limpar filtros
    if st.sidebar.button("🔄 Limpar Filtros"):
        st.rerun()

    # Tabs principais
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Visão Geral",
        "🏢 Situação Cadastral",
        "🗺️ Análise Geográfica",
        "📅 Análise Temporal",
        "💼 CNAEs",
        "📥 Exportar Dados"
    ])

    # TAB 1: Visão Geral
    with tab1:
        st.header("Visão Geral dos Dados")

        # Estatísticas resumidas
        stats = utils.get_summary_stats(df_filtered)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Total de Estabelecimentos",
                value=f"{stats['total_estabelecimentos']:,}"
            )

        with col2:
            st.metric(
                label="Estabelecimentos Ativos",
                value=f"{stats['total_ativos']:,}",
            )

        with col3:
            st.metric(
                label="Municípios",
                value=f"{stats['total_municipios']:,}"
            )

        with col4:
            st.metric(
                label="CNAEs Distintos",
                value=f"{stats['total_cnaes']:,}"
            )

        st.markdown("---")

        # Gráficos em colunas
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Distribuição Matriz/Filial")
            dist_mf = utils.get_matriz_filial_distribution(df_filtered)

            fig_mf = px.pie(
                dist_mf,
                values='Quantidade',
                names='Tipo',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_mf.update_traces(textposition='inside', textinfo='percent+label')
            fig_mf.update_layout(height=400)
            st.plotly_chart(fig_mf, use_container_width=True, config={'displayModeBar': False})

        with col2:
            st.subheader("Distribuição por Situação")
            dist_sit = utils.get_situacao_distribution(df_filtered)

            fig_sit = px.bar(
                dist_sit,
                x='Situação',
                y='Quantidade',
                color='Situação',
                color_discrete_sequence=px.colors.qualitative.Set1
            )
            fig_sit.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig_sit, use_container_width=True, config={'displayModeBar': False})

    # TAB 2: Situação Cadastral
    with tab2:
        st.header("Análise por Situação Cadastral")

        dist_situacao = utils.get_situacao_distribution(df_filtered)

        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Distribuição Detalhada")
            fig = px.bar(
                dist_situacao,
                x='Quantidade',
                y='Situação',
                orientation='h',
                color='Situação',
                text='Quantidade',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_traces(texttemplate='%{text:,}', textposition='outside')
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        with col2:
            st.subheader("Tabela de Dados")
            dist_situacao['Percentual'] = (
                dist_situacao['Quantidade'] / dist_situacao['Quantidade'].sum() * 100
            ).round(2)
            dist_situacao['Percentual'] = dist_situacao['Percentual'].astype(str) + '%'
            st.dataframe(dist_situacao, hide_index=True, width='stretch')

        st.markdown("---")

        # Evolução das situações ao longo do tempo
        st.subheader("Evolução de Situações Cadastrais por Ano")

        df_ano_situacao = df_filtered.groupby(['ano_situacao', 'situacao_descricao']).size().reset_index(name='Quantidade')
        df_ano_situacao = df_ano_situacao[
            (df_ano_situacao['ano_situacao'].notna()) &
            (df_ano_situacao['ano_situacao'] >= 2000) &
            (df_ano_situacao['ano_situacao'] <= datetime.now().year)
        ]

        fig_evolucao = px.line(
            df_ano_situacao,
            x='ano_situacao',
            y='Quantidade',
            color='situacao_descricao',
            markers=True,
            labels={'ano_situacao': 'Ano', 'situacao_descricao': 'Situação'}
        )
        fig_evolucao.update_layout(height=500)
        st.plotly_chart(fig_evolucao, use_container_width=True, config={'displayModeBar': False})

    # TAB 3: Análise Geográfica
    with tab3:
        st.header("Análise Geográfica")

        # Mapa Coroplético do Rio Grande do Sul
        st.subheader("Mapa de Calor - Estabelecimentos por Município")

        try:
            # Carregar GeoJSON
            geojson_data = utils.load_geojson("dados/municipios_rs.json")

            # Preparar dados agregados por município
            mun_data = utils.get_municipios_data_for_map(df_filtered)

            # Normalizar nomes no GeoJSON para fazer match
            for feature in geojson_data['features']:
                feature['properties']['name_normalized'] = utils.normalize_municipio_name(
                    feature['properties']['name']
                )

            # Criar mapa coroplético (RdYlGn)
            fig_map = px.choropleth(
                mun_data,
                geojson=geojson_data,
                locations='municipio_normalizado',
                featureidkey="properties.name_normalized",
                color='quantidade',
                color_continuous_scale="YlOrRd", 
                hover_name='municipio',
                hover_data={'municipio_normalizado': False, 'quantidade': ':,'},
                labels={'quantidade': 'Estabelecimentos'}
            )

            # Ajustar layout do mapa
            fig_map.update_geos(
                fitbounds="locations",
                visible=False
            )

            fig_map.update_layout(
                height=600,
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
                coloraxis_colorbar=dict(
                    title="Quantidade",
                    tickformat=","
                )
            )

            st.plotly_chart(fig_map, use_container_width=True, config={'displayModeBar': False})

        except Exception as e:
            st.warning(f"Não foi possível carregar o mapa: {str(e)}")
            st.info("Verifique se o arquivo 'municipios_rs.json' está no diretório correto.")

        st.markdown("---")

        # Top municípios
        top_n = st.slider("Número de municípios a exibir", 5, 50, 20, step=5)

        top_municipios = utils.get_top_municipios(df_filtered, top_n=top_n)

        col1, col2 = st.columns([3, 2])

        with col1:
            st.subheader(f"Top {top_n} Municípios com Mais Estabelecimentos")
            fig_mun = px.bar(
                top_municipios,
                x='Quantidade',
                y='Município',
                orientation='h',
                text='Quantidade',
                color='Quantidade',
                color_continuous_scale='Blues'
            )
            fig_mun.update_traces(texttemplate='%{text:,}', textposition='outside')
            fig_mun.update_layout(height=600, showlegend=False)
            fig_mun.update_yaxes(categoryorder='total ascending')
            st.plotly_chart(fig_mun, use_container_width=True, config={'displayModeBar': False})

        with col2:
            st.subheader("Dados Detalhados")
            top_municipios['Percentual'] = (
                top_municipios['Quantidade'] / len(df_filtered) * 100
            ).round(2)
            top_municipios['Percentual'] = top_municipios['Percentual'].astype(str) + '%'
            st.dataframe(top_municipios, hide_index=True, width='stretch', height=600)

    # TAB 4: Análise Temporal
    with tab4:
        st.header("Análise Temporal")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Evolução de Aberturas por Ano")

            timeline_inicio = utils.get_timeline_data(df_filtered, 'ano_inicio')

            fig_timeline = px.area(
                timeline_inicio,
                x='Ano',
                y='Quantidade',
                markers=True,
                line_shape='spline',
                color_discrete_sequence=['#1f77b4']
            )
            fig_timeline.update_layout(height=400)
            st.plotly_chart(fig_timeline, use_container_width=True, config={'displayModeBar': False})

        with col2:
            st.subheader("Mudanças de Situação por Ano")

            timeline_situacao = utils.get_timeline_data(df_filtered, 'ano_situacao')

            fig_situacao = px.bar(
                timeline_situacao,
                x='Ano',
                y='Quantidade',
                color_discrete_sequence=['#ff7f0e']
            )
            fig_situacao.update_layout(height=400)
            st.plotly_chart(fig_situacao, use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")

        # Distribuição por década
        st.subheader("Estabelecimentos por Década de Abertura")

        df_decada = df_filtered[df_filtered['ano_inicio'].notna()].copy()
        df_decada['decada'] = (df_decada['ano_inicio'] // 10 * 10).astype(int)
        dist_decada = df_decada['decada'].value_counts().sort_index().reset_index()
        dist_decada.columns = ['Década', 'Quantidade']
        dist_decada['Década'] = dist_decada['Década'].astype(str) + 's'

        fig_decada = px.bar(
            dist_decada,
            x='Década',
            y='Quantidade',
            text='Quantidade',
            color='Quantidade',
            color_continuous_scale='Viridis'
        )
        fig_decada.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig_decada.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_decada, use_container_width=True, config={'displayModeBar': False})

    # TAB 5: CNAEs
    with tab5:
        st.header("Análise por CNAE")

        st.info("📌 CNAE = Classificação Nacional de Atividades Econômicas")

        top_cnae_n = st.slider("Número de CNAEs a exibir", 5, 50, 20, step=5)

        top_cnaes = utils.get_top_cnaes(df_filtered, top_n=top_cnae_n)

        # col1, col2 = st.columns([3, 2])

        # with col1:
        #     st.subheader(f"Top {top_cnae_n} CNAEs Mais Comuns")
        #     fig_cnae = px.bar(
        #         top_cnaes,
        #         x='Quantidade',
        #         y='CNAE',
        #         orientation='h',
        #         text='Quantidade',
        #         color='Quantidade',
        #         color_continuous_scale='Greens'
        #     )
        #     fig_cnae.update_traces(texttemplate='%{text:,}', textposition='outside')
        #     fig_cnae.update_layout(height=600, showlegend=False)
        #     fig_cnae.update_yaxes(categoryorder='total ascending')
        #     st.plotly_chart(fig_cnae, use_container_width=True)

        # with col2:
        st.subheader("Dados Detalhados")
        top_cnaes['Percentual'] = (
            top_cnaes['Quantidade'] / len(df_filtered) * 100
        ).round(2)
        top_cnaes['Percentual'] = top_cnaes['Percentual'].astype(str) + '%'
        st.dataframe(top_cnaes, hide_index=True, width='stretch', height=600)

        st.markdown("---")

        # Treemap de CNAEs
        st.subheader("Treemap de Distribuição de CNAEs")

        top_cnaes_treemap = utils.get_top_cnaes(df_filtered, top_n=30)

        fig_treemap = px.treemap(
            top_cnaes_treemap,
            path=['CNAE'],
            values='Quantidade',
            color='Quantidade',
            color_continuous_scale='RdYlGn',
            hover_data={'Quantidade': ':,'}
        )
        fig_treemap.update_layout(height=500)
        st.plotly_chart(fig_treemap, use_container_width=True, config={'displayModeBar': False})

    # TAB 6: Exportar Dados
    with tab6:
        st.header("Exportar Dados Filtrados")

        st.info(f"📊 Você está prestes a exportar {len(df_filtered):,} registros.")

        # Opções de exportação
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Formato CSV")
            st.markdown("Exportar dados em formato CSV (texto separado por vírgulas)")

            csv_data = utils.export_to_csv(df_filtered)

            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"estabelecimentos_filtrados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                width='stretch'
            )

        with col2:
            st.subheader("Formato Excel")
            st.markdown("Exportar dados em formato Excel (.xlsx)")

            if st.button("Preparar Excel", width='stretch'):
                with st.spinner("Preparando arquivo Excel..."):
                    excel_data = utils.export_to_excel(df_filtered)

                    st.download_button(
                        label="📥 Download Excel",
                        data=excel_data,
                        file_name=f"estabelecimentos_filtrados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        width='stretch'
                    )

        st.markdown("---")

        # Preview dos dados
        st.subheader("Preview dos Dados")

        n_rows = st.slider("Número de linhas para visualizar", 10, 1000, 100, step=10)

        st.dataframe(
            df_filtered.head(n_rows),
            hide_index=True,
            width='stretch',
            height=400
        )

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 1rem;'>
            Dashboard de Análise de Estabelecimentos RFB |
            Desenvolvido com Streamlit |
            Dados: Receita Federal do Brasil
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
