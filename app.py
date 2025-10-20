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
    # ============================================
    # HEADER PRINCIPAL
    # ============================================
    st.markdown('<p class="main-header">📊 Dashboard - Estabelecimentos Ativos RFB (RS)</p>', unsafe_allow_html=True)
    st.markdown("*Análise de estabelecimentos com situação cadastral ativa no Rio Grande do Sul*")
    st.markdown("---")

    # ============================================
    # CARREGAR DADOS
    # ============================================
    with st.spinner("Carregando dados... Isso pode levar alguns segundos."):
        try:
            df = load_dataset()
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
    else:
        st.sidebar.success(f"✅ Total: {len(df):,} estabelecimentos")

    # Botão para limpar filtros
    if st.sidebar.button("🔄 Limpar Filtros"):
        st.rerun()

    # ============================================
    # SEÇÃO 1: MÉTRICAS PRINCIPAIS + MATRIZ/FILIAL
    # ============================================
    st.markdown('<p class="section-header">📌 Visão Geral</p>', unsafe_allow_html=True)

    # Estatísticas resumidas
    stats = utils.get_summary_stats(df_filtered)

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

    st.markdown("---")

    # Gráfico de Distribuição Matriz/Filial
    st.subheader("🏢 Distribuição Matriz/Filial")

    col1, col2 = st.columns([2, 1])

    with col1:
        dist_mf = utils.get_matriz_filial_distribution(df_filtered)

        # Criar gráfico de pizza com matplotlib
        fig_mf, ax = plt.subplots(figsize=(10, 6))
        colors = sns.color_palette("dark", len(dist_mf))

        wedges, texts, autotexts = ax.pie(
            dist_mf['Quantidade'],
            labels=dist_mf['Tipo'],
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            wedgeprops=dict(width=0.6),
            textprops={'fontsize': 12, 'weight': 'bold'}
        )

        # Melhorar aparência do texto
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(11)

        for text in texts:
            text.set_fontsize(12)
            text.set_fontweight('bold')

        ax.axis('equal')
        plt.tight_layout()
        st.pyplot(fig_mf)

    with col2:
        st.markdown("### Dados")
        dist_mf['Percentual'] = (
            dist_mf['Quantidade'] / dist_mf['Quantidade'].sum() * 100
        ).round(2)
        dist_mf['Percentual'] = dist_mf['Percentual'].astype(str) + '%'
        st.dataframe(dist_mf, hide_index=True, use_container_width=True)

    # ============================================
    # SEÇÃO 2: ANÁLISE GEOGRÁFICA
    # ============================================
    st.markdown("---")
    st.markdown('<p class="section-header">🗺️ Análise Geográfica</p>', unsafe_allow_html=True)

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

    # ============================================
    # SEÇÃO 3: ANÁLISE TEMPORAL
    # ============================================
    st.markdown("---")
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
        st.subheader("Estabelecimentos Ativos por Década de Início")

        df_decada = df_filtered[df_filtered['ano_inicio'].notna()].copy()
        df_decada['decada'] = (df_decada['ano_inicio'] // 10 * 10).astype(int)
        dist_decada = df_decada['decada'].value_counts().sort_index().reset_index()
        dist_decada.columns = ['Década', 'Quantidade']
        dist_decada['Década'] = dist_decada['Década'].astype(str) + 's'

        # Criar gráfico de barras com matplotlib (cores mais escuras)
        fig_decada, ax = plt.subplots(figsize=(12, 6))

        # Criar paleta de cores gradiente (mais escura)
        norm = plt.Normalize(
            vmin=dist_decada['Quantidade'].min(),
            vmax=dist_decada['Quantidade'].max()
        )
        colors = plt.cm.cividis(norm(dist_decada['Quantidade']))

        bars = ax.bar(
            dist_decada['Década'],
            dist_decada['Quantidade'],
            color=colors,
            edgecolor='black',
            linewidth=0.7
        )

        # Adicionar rótulos de valor nas barras
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height,
                f'{int(height):,}',
                ha='center',
                va='bottom',
                fontsize=9,
                fontweight='bold'
            )

        ax.set_xlabel('Década', fontsize=11, fontweight='bold')
        ax.set_ylabel('Quantidade', fontsize=11, fontweight='bold')
        ax.tick_params(axis='x', rotation=45)
        plt.xticks(ha='right')
        plt.tight_layout()
        st.pyplot(fig_decada)

        st.info("ℹ️ Agrupa os estabelecimentos ativos por década de início de atividade (ex: 2010s = iniciados entre 2010-2019).")

    # ============================================
    # SEÇÃO 4: ANÁLISE POR CNAE
    # ============================================
    st.markdown("---")
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

    # ============================================
    # SEÇÃO 5: EXPORTAR DADOS
    # ============================================
    st.markdown("---")
    st.markdown('<p class="section-header">📥 Exportar Dados</p>', unsafe_allow_html=True)

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
            file_name=f"estabelecimentos_ativos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col2:
        st.subheader("Formato Excel")
        st.markdown("Exportar dados em formato Excel (.xlsx)")

        if st.button("Preparar Excel", use_container_width=True):
            with st.spinner("Preparando arquivo Excel..."):
                excel_data = utils.export_to_excel(df_filtered)

                st.download_button(
                    label="📥 Download Excel",
                    data=excel_data,
                    file_name=f"estabelecimentos_ativos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

    st.markdown("---")

    # Preview dos dados
    st.subheader("Preview dos Dados")

    n_rows = st.slider("Número de linhas para visualizar", 10, 1000, 100, step=10, key="slider_preview")

    st.dataframe(
        df_filtered.head(n_rows),
        hide_index=True,
        use_container_width=True,
        height=400
    )

    # ============================================
    # FOOTER
    # ============================================
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 1rem;'>
            Dashboard de Análise - Estabelecimentos Ativos RFB (RS) |
            Desenvolvido com Streamlit e Seaborn |
            Dados: Receita Federal do Brasil
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
