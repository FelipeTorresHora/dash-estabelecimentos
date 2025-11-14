"""
Dashboard Streamlit para Análise de Estabelecimentos Ativos RFB (RS)
Autor: Felipe
Data: 2025-10-17
"""

import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
import utils
import squarify
import warnings
warnings.filterwarnings('ignore')

# Configuração da página
st.set_page_config(
    page_title="Dashboard RFB - Estabelecimentos Ativos (RS)",
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
        color: #0d3d56;
        text-align: center;
        padding: 1rem 0;
    }
    .section-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1a5f7a;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #0d3d56;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_data
def load_dataset():
    """
    Carrega o dataset principal a partir de múltiplos arquivos divididos.

    ⚠️ OTIMIZAÇÃO: Retorna DOIS DataFrames (ativos e fechados) em uma única passada
    para evitar carregamento duplicado.

    Returns:
        tuple: (df_ativos, df_fechados)
    """
    # Lista dos arquivos divididos
    arquivos = [
        "dados/estabelecimentos_filtrado_parte1.parquet",
        "dados/estabelecimentos_filtrado_parte2.parquet",
        "dados/estabelecimentos_filtrado_parte3.parquet",
        "dados/estabelecimentos_filtrado_parte4.parquet"
    ]

    # Listas para armazenar os DataFrames
    dfs_ativos = []
    dfs_fechados = []

    # Carregar cada arquivo e separar ativos/fechados
    for arquivo in arquivos:
        try:
            df_temp = utils.load_data(arquivo)

            # VALIDAÇÃO: Verificar se coluna existe
            if 'situacao_cadastral' not in df_temp.columns:
                raise ValueError(f"Coluna 'situacao_cadastral' não encontrada em {arquivo}")

            # Separar empresas ativas (situacao_cadastral = '02') e fechadas (demais)
            # NOTA: Normalização de formato já feita em utils.load_data()
            df_ativos = df_temp[df_temp['situacao_cadastral'] == '02'].copy()
            df_fechados = df_temp[df_temp['situacao_cadastral'] != '02'].copy()

            # VALIDAÇÃO: Alertar se não há dados
            if len(df_ativos) == 0 and len(df_fechados) == 0:
                st.warning(f"⚠️ {arquivo}: Nenhum registro encontrado após filtragem de situação cadastral")

            dfs_ativos.append(df_ativos)
            dfs_fechados.append(df_fechados)

        except Exception as e:
            st.error(f"❌ ERRO CRÍTICO ao carregar {arquivo}: {str(e)}")
            raise  # Re-lançar exceção para parar execução

    # Concatenar todos os DataFrames
    if dfs_ativos:
        df_ativos = pd.concat(dfs_ativos, ignore_index=True)
        df_fechados = pd.concat(dfs_fechados, ignore_index=True) if dfs_fechados else pd.DataFrame()

        # VALIDAÇÃO FINAL: Mostrar contagem de registros
        st.info(f"✅ Dados carregados: {len(df_ativos):,} ativos, {len(df_fechados):,} fechados")

        return df_ativos, df_fechados
    else:
        raise Exception("Nenhum arquivo foi carregado com sucesso!")


def main():
    # ============================================
    # HEADER PRINCIPAL
    # ============================================
    st.markdown('<p class="main-header">📊 Dashboard - Análise de estabelecimentos no Rio Grande do Sul</p>', unsafe_allow_html=True)
    st.markdown("---")

    # ============================================
    # CARREGAR DADOS
    # ============================================
    with st.spinner("🔄 Carregando dados... Primeira inicialização pode levar até 15 segundos."):
        try:
            df, df_baixadas = load_dataset()
        except Exception as e:
            st.error(f"❌ Erro ao carregar dados: {str(e)}")
            st.stop()

    # Carregar descrições de CNAEs
    try:
        df_cnae = utils.load_cnae_descriptions("dados/codigos_cnae_2.csv")
    except Exception as e:
        st.warning(f"⚠️ Não foi possível carregar descrições de CNAEs: {str(e)}")
        st.info("Os gráficos de CNAE mostrarão apenas códigos numéricos.")
        # DataFrame vazio como fallback
        df_cnae = pd.DataFrame(columns=['CNAE', 'DESCRIÇÃO'])

    # ============================================
    # SIDEBAR - FILTROS
    # ============================================
    st.sidebar.header("🔍 Filtros")

    # Filtro de município
    municipios_disponiveis = sorted(df['nome_municipio'].dropna().unique().tolist())
    municipios_selecionados = st.sidebar.multiselect(
        "Município",
        options=municipios_disponiveis,
        default=[]
    )

    # Filtro de CNAE
    cnaes_selecionados = []
    if not df_cnae.empty:
        # Obter CNAEs únicos dos dados
        cnaes_nos_dados = df['cnae_fiscal_principal'].dropna().unique()

        # Filtrar apenas CNAEs que existem nos dados e criar opções com descrição
        df_cnae_filtrado = df_cnae[df_cnae['CNAE'].isin(cnaes_nos_dados)].copy()
        df_cnae_filtrado['CNAE_Display'] = df_cnae_filtrado['CNAE'] + ' - ' + df_cnae_filtrado['DESCRIÇÃO']

        # Ordenar por descrição
        df_cnae_filtrado = df_cnae_filtrado.sort_values('DESCRIÇÃO')

        # Criar mapeamento display -> código
        cnae_options = df_cnae_filtrado['CNAE_Display'].tolist()
        cnae_mapping = dict(zip(df_cnae_filtrado['CNAE_Display'], df_cnae_filtrado['CNAE']))

        cnaes_selecionados_display = st.sidebar.multiselect(
            "CNAE - Atividade Econômica",
            options=cnae_options,
            default=[],
            help="Classificação Nacional de Atividades Econômicas"
        )

        # Converter display para códigos
        cnaes_selecionados = [cnae_mapping[display] for display in cnaes_selecionados_display]
    else:
        # Fallback se não houver descrições
        cnaes_disponiveis = sorted(df['cnae_fiscal_principal'].dropna().unique().tolist())
        cnaes_selecionados = st.sidebar.multiselect(
            "CNAE - Atividade Econômica",
            options=cnaes_disponiveis,
            default=[],
            help="Classificação Nacional de Atividades Econômicas"
        )

    # Filtro de ano de início
    anos_disponiveis = sorted([int(x) for x in df['ano_inicio'].dropna().unique() if 1900 <= x <= datetime.now().year])
    if anos_disponiveis:
        ano_min, ano_max = min(anos_disponiveis), max(anos_disponiveis)
        anos_selecionados = st.sidebar.slider(
            "Empresas que tiveram data de inicio de atividade entre os anos:",
            min_value=ano_min,
            max_value=ano_max,
            value=(ano_min, ano_max)
        )
    else:
        anos_selecionados = None

    # Aplicar filtros
    filters = {}
    if municipios_selecionados:
        filters['nome_municipio'] = municipios_selecionados
    if cnaes_selecionados:
        filters['cnae_fiscal_principal'] = cnaes_selecionados

    df_filtered = utils.filter_dataframe(df, filters)

    # Aplicar filtro de ano
    if anos_selecionados:
        df_filtered = df_filtered[
            (df_filtered['ano_inicio'] >= anos_selecionados[0]) &
            (df_filtered['ano_inicio'] <= anos_selecionados[1])
        ]

    # Aplicar os mesmos filtros ao DataFrame de empresas baixadas
    df_baixadas_filtered = utils.filter_dataframe(df_baixadas, filters)
    if anos_selecionados:
        df_baixadas_filtered = df_baixadas_filtered[
            (df_baixadas_filtered['ano_inicio'] >= anos_selecionados[0]) &
            (df_baixadas_filtered['ano_inicio'] <= anos_selecionados[1])
        ]

    # Informação sobre filtros aplicados
    if len(df_filtered) < len(df):
        st.sidebar.info(f"📌 Mostrando {len(df_filtered):,} de {len(df):,} estabelecimentos")
    else:
        st.sidebar.success(f"✅ Total: {len(df):,} estabelecimentos")

    # Botão para limpar filtros
    if st.sidebar.button("🔄 Limpar Filtros"):
        st.rerun()

    # ============================================
    # TABS PRINCIPAIS (LAZY LOADING)
    # ============================================
    # Inicializar session_state para controle de lazy loading
    if 'tabs_loaded' not in st.session_state:
        st.session_state.tabs_loaded = {
            'visao_geral': True,  # Sempre carregado
            'geografica': False,
            'temporal': False,
            'fechadas': False,
            'cnae': False
        }

    # Criar tabs
    tab1, tab3, tab4, tab5 = st.tabs([
        "📌 Visão Geral",
        "📅 Análise Temporal",
        "📉 Empresas Fechadas",
        "💼 Análise CNAE"
    ])

    # ============================================
    # TAB 1: VISÃO GERAL (SEMPRE CARREGADA)
    # ============================================
    with tab1:
        st.markdown('<p class="section-header">📌 Visão Geral</p>', unsafe_allow_html=True)

        # Estatísticas resumidas
        stats = utils.get_summary_stats(df_filtered, df_baixadas_filtered)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="Total de Estabelecimentos",
                value=f"{stats['total_estabelecimentos']:,}"
            )

        with col2:
            st.metric(
                label="Municípios",
                value=f"{stats['total_municipios']:,}"
            )

        with col3:
            st.metric(
                label="CNAEs Distintos",
                value=f"{stats['total_cnaes']:,}"
            )

        # Mapa Coroplético do Rio Grande do Sul
        st.subheader("Mapa de Calor - Estabelecimentos por Município")

        try:
            import geopandas as gpd

            # Carregar GeoJSON
            geojson_data = utils.load_geojson("dados/municipios_rs.json")

            # Preparar dados agregados por município
            mun_data = utils.get_municipios_data_for_map(df_filtered)

            # Converter GeoJSON para GeoDataFrame
            gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])

            # Normalizar nomes
            gdf['name_normalized'] = gdf['name'].apply(utils.normalize_municipio_name)

            # Fazer merge com os dados
            gdf = gdf.merge(
                mun_data,
                left_on='name_normalized',
                right_on='municipio_normalizado',
                how='left'
            )

            # Preencher NaN com 0
            gdf['quantidade'] = gdf['quantidade'].fillna(0)

            # Criar mapa coroplético com matplotlib
            fig_map, ax = plt.subplots(figsize=(14, 10))

            # Plotar o mapa
            gdf.plot(
                column='quantidade',
                cmap='YlOrRd',
                linewidth=0.5,
                edgecolor='black',
                legend=True,
                ax=ax,
                legend_kwds={
                    'label': 'Quantidade de Estabelecimentos',
                    'orientation': 'vertical',
                    'shrink': 0.7
                }
            )

            ax.set_title('Distribuição de Estabelecimentos por Município (RS)',
                        fontsize=14, fontweight='bold', pad=20)
            ax.axis('off')
            plt.tight_layout()
            st.pyplot(fig_map)

        except Exception as e:
            st.warning(f"⚠️ Não foi possível carregar o mapa: {str(e)}")
            st.info("Verifique se o arquivo 'municipios_rs.json' está no diretório correto.")

        st.markdown("---")

        # Top municípios
        st.subheader("Top Municípios com Mais Estabelecimentos")

        top_n = st.slider("Número de municípios a exibir", 5, 50, 20, step=5, key="slider_municipios")

        top_municipios = utils.get_top_municipios(df_filtered, top_n=top_n)

        col1, col2 = st.columns([3, 2])

        with col1:
            # Criar gráfico de barras horizontal
            fig_mun, ax = plt.subplots(figsize=(12, max(8, top_n * 0.4)))

            # Ordenar dados
            top_municipios_sorted = top_municipios.sort_values('Quantidade', ascending=True)

            # Criar paleta de cores gradiente (mais escura)
            norm = plt.Normalize(
                vmin=top_municipios_sorted['Quantidade'].min(),
                vmax=top_municipios_sorted['Quantidade'].max()
            )
            colors = plt.cm.YlGnBu(norm(top_municipios_sorted['Quantidade']))

            bars = ax.barh(
                top_municipios_sorted['Município'],
                top_municipios_sorted['Quantidade'],
                color=colors,
                edgecolor='black',
                linewidth=0.5
            )

            # Adicionar rótulos de valor nas barras
            for bar in bars:
                width = bar.get_width()
                ax.text(
                    width,
                    bar.get_y() + bar.get_height() / 2.,
                    f'{int(width):,}',
                    ha='left',
                    va='center',
                    fontsize=9,
                    fontweight='bold'
                )

            ax.set_xlabel('Quantidade', fontsize=11, fontweight='bold')
            ax.set_ylabel('Município', fontsize=11, fontweight='bold')
            plt.tight_layout()
            st.pyplot(fig_mun)

        with col2:
            st.markdown("### Dados Detalhados")
            top_municipios['Percentual'] = (
                top_municipios['Quantidade'] / len(df_filtered) * 100
            ).round(2)
            top_municipios['Percentual'] = top_municipios['Percentual'].astype(str) + '%'
            st.dataframe(top_municipios, hide_index=True, use_container_width=True, height=600)

    # Aplicar filtros aos dados de empresas fechadas para as Tabs 3 e 4
    # NOTA: Para essas tabs, usa ano_situacao (ano de fechamento) em vez de ano_inicio
    try:
        # Aplicar filtros de município e CNAE
        df_baixadas_filtered = utils.filter_dataframe(df_baixadas, filters)

        # Aplicar filtro de ano usando ano_situacao (data de fechamento)
        if not df_baixadas_filtered.empty and anos_selecionados:
            df_baixadas_filtered = df_baixadas_filtered[
                (df_baixadas_filtered['ano_situacao'] >= anos_selecionados[0]) &
                (df_baixadas_filtered['ano_situacao'] <= anos_selecionados[1])
            ]
    except Exception as e:
        df_baixadas_filtered = pd.DataFrame()  # DataFrame vazio em caso de erro

    # ============================================
    # TAB 3: ANÁLISE TEMPORAL (LAZY LOADING)
    # ============================================
    with tab3:
        # Marcar tab como carregada
        st.session_state.tabs_loaded['temporal'] = True

        st.markdown('<p class="section-header">📅 Análise Temporal</p>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Evolução de Aberturas por Ano (Estabelecimentos Ativos)")

            timeline_inicio = utils.get_timeline_data(df_filtered, 'ano_inicio')

            # Criar gráfico de área com matplotlib (cor mais escura)
            fig_timeline, ax = plt.subplots(figsize=(12, 6))

            ax.fill_between(
                timeline_inicio['Ano'],
                timeline_inicio['Quantidade'],
                alpha=0.5,
                color='#0d3d56'
            )

            ax.plot(
                timeline_inicio['Ano'],
                timeline_inicio['Quantidade'],
                marker='o',
                color='#0d3d56',
                linewidth=2.5,
                markersize=6
            )

            ax.set_xlabel('Ano', fontsize=11, fontweight='bold')
            ax.set_ylabel('Quantidade', fontsize=11, fontweight='bold')
            ax.grid(True, alpha=0.3, linestyle='--')
            plt.tight_layout()
            st.pyplot(fig_timeline)

            st.info("ℹ️ Este gráfico mostra quantos estabelecimentos **ativos hoje** iniciaram suas atividades em cada ano.")

        with col2:
            st.subheader("📊 Evolução de Fechamentos por ano (Estabelecimentos Fechadas)")

            if not df_baixadas_filtered.empty:
                timeline_baixadas = utils.get_timeline_data(df_baixadas_filtered, date_column='ano_situacao')

                if not timeline_baixadas.empty:
                    fig_timeline_fechadas, ax_timeline_fechadas = plt.subplots(figsize=(12, 6))

                    ax_timeline_fechadas.plot(
                        timeline_baixadas['Ano'],
                        timeline_baixadas['Quantidade'],
                        marker='o',
                        linewidth=2,
                        markersize=6,
                        color='#d62728',
                        label='Fechamentos'
                    )

                    ax_timeline_fechadas.fill_between(
                        timeline_baixadas['Ano'],
                        timeline_baixadas['Quantidade'],
                        alpha=0.3,
                        color='#d62728'
                    )

                    ax_timeline_fechadas.set_xlabel('Ano', fontsize=11, fontweight='bold')
                    ax_timeline_fechadas.set_ylabel('Quantidade de Fechamentos', fontsize=11, fontweight='bold')
                    ax_timeline_fechadas.grid(True, alpha=0.3, linestyle='--')
                    ax_timeline_fechadas.legend()

                    plt.tight_layout()
                    st.pyplot(fig_timeline_fechadas)

                    st.info("ℹ️ Gráfico mostrando a quantidade total de fechamentos de empresas por ano.")
                else:
                    st.warning("Não há dados de timeline disponíveis.")
            else:
                st.warning("Não foi possível carregar dados de empresas fechadas.")

    # ============================================
    # TAB 4: ANÁLISE DE EMPRESAS FECHADAS (LAZY LOADING)
    # ============================================
    with tab4:
        # Marcar tab como carregada
        st.session_state.tabs_loaded['fechadas'] = True

        st.markdown('<p class="section-header">📉 Análise de Empresas Fechadas</p>', unsafe_allow_html=True)

        # Nota: df_baixadas_filtered já foi carregado antes da seção de análise temporal
        try:
            if not df_baixadas_filtered.empty:
                # Calcular info do período
                if anos_selecionados:
                    periodo_info = f"Fechamentos entre {anos_selecionados[0]} e {anos_selecionados[1]}"
                else:
                    periodo_info = "Todos os períodos"

                # Informações sobre situações cadastrais não-ativas
                st.info(f"""
                📌 **Empresas Fechadas**: Situação cadastral diferente de ATIVA
                - **Período:** {periodo_info}
                - **Total de fechamentos no período:** {len(df_baixadas_filtered):,}
                - **Tipos incluídos:** NULA, SUSPENSA, INAPTA, BAIXADA
                """)

                # Distribuição por tipo de situação cadastral
                col1, col2, col3, col4 = st.columns(4)

                situacao_counts = df_baixadas_filtered['situacao_descricao'].value_counts()

                with col1:
                    baixada = situacao_counts.get('BAIXADA', 0)
                    st.metric("Baixadas", f"{baixada:,}")

                with col2:
                    suspensa = situacao_counts.get('SUSPENSA', 0)
                    st.metric("Suspensas", f"{suspensa:,}")

                with col3:
                    inapta = situacao_counts.get('INAPTA', 0)
                    st.metric("Inaptas", f"{inapta:,}")

                with col4:
                    nula = situacao_counts.get('NULA', 0)
                    st.metric("Nulas", f"{nula:,}")

                # Mapa geográfico de fechamentos por município
                st.subheader("🗺️ Mapa Geográfico - Fechamentos por Município")

                try:
                    import geopandas as gpd

                    # Carregar GeoJSON dos municípios do RS
                    geojson_data = utils.load_geojson("dados/municipios_rs.json")

                    # Preparar dados agregados por município
                    mun_data_fechadas = utils.get_municipios_data_for_map(df_baixadas_filtered)

                    # Converter GeoJSON para GeoDataFrame
                    gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])

                    # Normalizar nomes dos municípios para merge
                    gdf['name_normalized'] = gdf['name'].apply(utils.normalize_municipio_name)

                    # Fazer merge com os dados de fechamentos
                    gdf = gdf.merge(
                        mun_data_fechadas,
                        left_on='name_normalized',
                        right_on='municipio_normalizado',
                        how='left'
                    )

                    # Preencher municípios sem dados com 0
                    gdf['quantidade'] = gdf['quantidade'].fillna(0)

                    # Criar mapa coroplético
                    fig_map_fechadas, ax_fechadas = plt.subplots(figsize=(14, 10))

                    # Plotar o mapa com cores representando quantidade de fechamentos
                    gdf.plot(
                        column='quantidade',
                        cmap='Reds',  # Paleta vermelha para fechamentos
                        linewidth=0.5,
                        edgecolor='black',
                        legend=True,
                        ax=ax_fechadas,
                        legend_kwds={
                            'label': 'Quantidade de Fechamentos',
                            'orientation': 'vertical',
                            'shrink': 0.7
                        }
                    )

                    ax_fechadas.set_title(
                        'Distribuição de Empresas Fechadas por Município (RS)',
                        fontsize=14,
                        fontweight='bold',
                        pad=20
                    )
                    ax_fechadas.axis('off')
                    plt.tight_layout()
                    st.pyplot(fig_map_fechadas)

                    st.info(f"ℹ️ Mapa geográfico do Rio Grande do Sul mostrando a distribuição de fechamentos por município. {periodo_info}. Cores mais intensas indicam maior quantidade de fechamentos.")

                except Exception as e:
                    st.warning(f"⚠️ Não foi possível carregar o mapa geográfico: {str(e)}")
                    st.info("Verifique se o arquivo 'dados/municipios_rs.json' está disponível.")

            else:
                st.warning("Não foram encontradas empresas fechadas nos dados.")

        except FileNotFoundError:
            st.error("❌ Arquivo de dados brutos não encontrado. Certifique-se de que o arquivo 'dado_bruto/estabelecimentos_filtrado.csv' existe.")
        except Exception as e:
            st.error(f"❌ Erro ao carregar dados de empresas fechadas: {str(e)}")

    # ============================================
    # TAB 5: ANÁLISE POR CNAE (LAZY LOADING)
    # ============================================
    with tab5:
        # Marcar tab como carregada
        st.session_state.tabs_loaded['cnae'] = True

        st.markdown('<p class="section-header">💼 Análise por CNAE</p>', unsafe_allow_html=True)

        st.info("📌 CNAE = Classificação Nacional de Atividades Econômicas")

        # Treemap de CNAEs
        st.subheader("Treemap de Distribuição de CNAEs")

        # Usar função com descrições se df_cnae disponível
        if not df_cnae.empty:
            top_cnaes_treemap = utils.get_top_cnaes_with_description(df_filtered, df_cnae, top_n=30)
        else:
            top_cnaes_treemap = utils.get_top_cnaes(df_filtered, top_n=30)
            top_cnaes_treemap['CNAE_Descricao'] = top_cnaes_treemap['CNAE']

        # Criar treemap com squarify
        fig_treemap, ax = plt.subplots(figsize=(16, 10))

        # Normalizar valores para cores (reversed para cores mais escuras)
        norm = plt.Normalize(
            vmin=top_cnaes_treemap['Quantidade'].min(),
            vmax=top_cnaes_treemap['Quantidade'].max()
        )
        colors = plt.cm.RdYlGn_r(norm(top_cnaes_treemap['Quantidade']))

        # Criar labels truncados para o treemap
        labels = []
        for _, row in top_cnaes_treemap.iterrows():
            desc = row['CNAE_Descricao']
            # Truncar descrições longas
            if len(desc) > 50:
                desc = desc[:47] + '...'
            labels.append(f"{desc}\n{row['Quantidade']:,}")

        # Criar treemap
        squarify.plot(
            sizes=top_cnaes_treemap['Quantidade'],
            label=labels,
            color=colors,
            alpha=0.8,
            ax=ax,
            text_kwargs={'fontsize': 8, 'weight': 'bold', 'color': 'white'}
        )

        ax.set_title('Distribuição de CNAEs por Atividade Econômica (Top 30)',
                    fontsize=14, fontweight='bold', pad=20)
        ax.axis('off')
        plt.tight_layout()
        st.pyplot(fig_treemap)

        st.markdown("---")

        # Tabela detalhada de CNAEs
        st.subheader("Dados Detalhados dos Top CNAEs")

        top_cnae_n = st.slider("Número de CNAEs a exibir", 10, 100, 30, step=10, key="slider_cnaes")

        # Usar função com descrições se df_cnae disponível
        if not df_cnae.empty:
            top_cnaes = utils.get_top_cnaes_with_description(df_filtered, df_cnae, top_n=top_cnae_n)
        else:
            top_cnaes = utils.get_top_cnaes(df_filtered, top_n=top_cnae_n)

        top_cnaes['Percentual'] = (
            top_cnaes['Quantidade'] / len(df_filtered) * 100
        ).round(2)
        top_cnaes['Percentual'] = top_cnaes['Percentual'].astype(str) + '%'

        # Selecionar colunas para exibição
        if not df_cnae.empty and 'DESCRIÇÃO' in top_cnaes.columns:
            top_cnaes_display = top_cnaes[['CNAE', 'DESCRIÇÃO', 'Quantidade', 'Percentual']]
        else:
            top_cnaes_display = top_cnaes[['CNAE', 'Quantidade', 'Percentual']]

        st.dataframe(top_cnaes_display, hide_index=True, use_container_width=True, height=600)

    # # ============================================
    # # SEÇÃO 5: EXPORTAR DADOS
    # # ============================================
    # st.markdown("---")
    # st.markdown('<p class="section-header">📥 Exportar Dados</p>', unsafe_allow_html=True)

    # st.info(f"📊 Você está prestes a exportar {len(df_filtered):,} registros.")

    # # Opções de exportação
    # col1, col2 = st.columns(2)

    # with col1:
    #     st.subheader("Formato CSV")
    #     st.markdown("Exportar dados em formato CSV (texto separado por vírgulas)")

    #     csv_data = utils.export_to_csv(df_filtered)

    #     st.download_button(
    #         label="📥 Download CSV",
    #         data=csv_data,
    #         file_name=f"estabelecimentos_ativos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    #         mime="text/csv",
    #         use_container_width=True
    #     )

    # with col2:
    #     st.subheader("Formato Excel")
    #     st.markdown("Exportar dados em formato Excel (.xlsx)")

    #     if st.button("Preparar Excel", use_container_width=True):
    #         with st.spinner("Preparando arquivo Excel..."):
    #             excel_data = utils.export_to_excel(df_filtered)

    #             st.download_button(
    #                 label="📥 Download Excel",
    #                 data=excel_data,
    #                 file_name=f"estabelecimentos_ativos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
    #                 mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    #                 use_container_width=True
    #             )

    # st.markdown("---")

    # # Preview dos dados
    # st.subheader("Preview dos Dados")

    # n_rows = st.slider("Número de linhas para visualizar", 10, 1000, 100, step=10, key="slider_preview")

    # st.dataframe(
    #     df_filtered.head(n_rows),
    #     hide_index=True,
    #     use_container_width=True,
    #     height=400
    # )

    # # ============================================
    # # FOOTER
    # # ============================================
    # st.markdown("---")
    # st.markdown(
    #     """
    #     <div style='text-align: center; color: #666; padding: 1rem;'>
    #         Dashboard de Análise - Estabelecimentos Ativos RFB (RS) |
    #         Desenvolvido com Streamlit e Seaborn |
    #         Dados: Receita Federal do Brasil
    #     </div>
    #     """,
    #     unsafe_allow_html=True
    # )


if __name__ == "__main__":
    main()
