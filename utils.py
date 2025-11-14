"""
Funções auxiliares para processamento de dados do RFB
"""
import pandas as pd
import streamlit as st
from datetime import datetime
import json


# Mapeamento de códigos de situação cadastral
SITUACAO_CADASTRAL = {
    '01': 'NULA',
    '02': 'ATIVA',
    '03': 'SUSPENSA',
    '04': 'INAPTA',
    '08': 'BAIXADA'
}


@st.cache_data
def load_data(file_path):
    """
    Carrega o arquivo CSV ou Parquet com otimização de tipos de dados
    """
    # Detectar formato pelo caminho do arquivo
    if file_path.endswith('.parquet'):
        # Ler Parquet (tipos já preservados no arquivo)
        df = pd.read_parquet(file_path, engine='pyarrow')

        # NORMALIZAR: Garantir formato de 2 dígitos para situacao_cadastral
        if 'situacao_cadastral' in df.columns:
            df['situacao_cadastral'] = df['situacao_cadastral'].astype(str).str.zfill(2).str.strip()
    else:
        # Ler CSV com tipos especificados
        dtype_spec = {
            'cnpj_basico': str,
            'situacao_cadastral': str,
            'data_situacao_cadastral': str,
            'data_inicio_atividade': str,
            'cnae_fiscal_principal': str,
            'nome_municipio': str
        }
        df = pd.read_csv(file_path, dtype=dtype_spec)

    # Processar dados
    df = process_data(df)

    return df


def process_data(df):
    """
    Processa e enriquece os dados do DataFrame
    """
    # Mapear situação cadastral
    df['situacao_descricao'] = df['situacao_cadastral'].map(SITUACAO_CADASTRAL)

    # Converter datas
    df['data_situacao_cadastral'] = pd.to_datetime(
        df['data_situacao_cadastral'],
        format='%Y%m%d',
        errors='coerce'
    )

    df['data_inicio_atividade'] = pd.to_datetime(
        df['data_inicio_atividade'],
        format='%Y%m%d',
        errors='coerce'
    )

    # Extrair ano das datas
    df['ano_situacao'] = df['data_situacao_cadastral'].dt.year
    df['ano_inicio'] = df['data_inicio_atividade'].dt.year

    return df


@st.cache_data
def load_data_baixadas(file_path):
    """
    Carrega o arquivo CSV ou Parquet apenas com empresas FECHADAS (situação cadastral != '02')
    Inclui: NULA ('01'), SUSPENSA ('03'), INAPTA ('04'), BAIXADA ('08')
    """
    # Detectar formato pelo caminho do arquivo
    if file_path.endswith('.parquet'):
        # Ler Parquet (tipos já preservados no arquivo)
        df = pd.read_parquet(file_path, engine='pyarrow')

        # NORMALIZAR: Garantir formato de 2 dígitos para situacao_cadastral
        if 'situacao_cadastral' in df.columns:
            df['situacao_cadastral'] = df['situacao_cadastral'].astype(str).str.zfill(2).str.strip()
    else:
        # Ler CSV com tipos especificados
        dtype_spec = {
            'cnpj_basico': str,
            'situacao_cadastral': str,
            'data_situacao_cadastral': str,
            'data_inicio_atividade': str,
            'cnae_fiscal_principal': str,
            'nome_municipio': str
        }
        df = pd.read_csv(file_path, dtype=dtype_spec)

    # Filtrar apenas empresas fechadas (situacao != '02' ATIVA)
    df = df[df['situacao_cadastral'] != '02'].copy()

    # Processar dados
    df = process_data(df)

    return df


def get_fechamentos_por_municipio_ano(df, top_n=20):
    """
    Prepara dados em formato pivot table para heatmap
    Retorna DataFrame com:
    - Linhas: Top N municípios com mais fechamentos
    - Colunas: Anos
    - Valores: Quantidade de fechamentos

    Args:
        df: DataFrame com empresas fechadas
        top_n: Número de municípios a exibir (padrão: 20)

    Returns:
        DataFrame pivotado pronto para heatmap
    """
    # Remover registros sem data válida
    df_valido = df[df['ano_situacao'].notna()].copy()

    # Filtrar anos válidos (últimos 30 anos, por exemplo)
    ano_atual = datetime.now().year
    df_valido = df_valido[
        (df_valido['ano_situacao'] >= ano_atual - 30) &
        (df_valido['ano_situacao'] <= ano_atual)
    ]

    # Identificar top municípios com mais fechamentos
    top_municipios = df_valido['nome_municipio'].value_counts().head(top_n).index
    df_top = df_valido[df_valido['nome_municipio'].isin(top_municipios)]

    # Criar pivot table
    heatmap_data = df_top.pivot_table(
        index='nome_municipio',
        columns='ano_situacao',
        values='cnpj_basico',
        aggfunc='count',
        fill_value=0
    )

    # Ordenar municípios por total de fechamentos (descendente)
    heatmap_data['total'] = heatmap_data.sum(axis=1)
    heatmap_data = heatmap_data.sort_values('total', ascending=False)
    heatmap_data = heatmap_data.drop('total', axis=1)

    return heatmap_data


def get_summary_stats(df, df_baixadas=None):
    """
    Retorna estatísticas resumidas do dataset

    Args:
        df: DataFrame com estabelecimentos (geralmente ativos)
        df_baixadas: DataFrame opcional com estabelecimentos baixados/inativos

    Returns:
        dict com estatísticas resumidas
    """
    # Calcular total de estabelecimentos (ativos + inativos se fornecido)
    total_estabelecimentos = len(df)
    if df_baixadas is not None:
        total_estabelecimentos += len(df_baixadas)

    # Calcular total de ativos (sempre do df principal)
    total_ativos = len(df[df['situacao_descricao'] == 'ATIVA'])

    # Calcular total de baixados
    if df_baixadas is not None:
        # Se df_baixadas fornecido, contar todos os registros nele
        total_baixados = len(df_baixadas)
    else:
        # Senão, buscar no df principal
        total_baixados = len(df[df['situacao_descricao'] == 'BAIXADA'])

    # Combinar DataFrames para estatísticas únicas (municípios e CNAEs)
    if df_baixadas is not None:
        df_combined = pd.concat([df, df_baixadas], ignore_index=True)
        total_municipios = df_combined['nome_municipio'].nunique()
        total_cnaes = df_combined['cnae_fiscal_principal'].nunique()
    else:
        total_municipios = df['nome_municipio'].nunique()
        total_cnaes = df['cnae_fiscal_principal'].nunique()

    stats = {
        'total_estabelecimentos': total_estabelecimentos,
        'total_ativos': total_ativos,
        'total_baixados': total_baixados,
        'total_municipios': total_municipios,
        'total_cnaes': total_cnaes
    }

    return stats


def get_top_municipios(df, top_n=20):
    """
    Retorna os top N municípios com mais estabelecimentos
    """
    top_mun = df['nome_municipio'].value_counts().head(top_n).reset_index()
    top_mun.columns = ['Município', 'Quantidade']
    # Sanitizar dados para evitar erros JavaScript
    top_mun = sanitize_chart_data(top_mun, text_columns=['Município'], numeric_columns=['Quantidade'])
    return top_mun


def get_top_cnaes(df, top_n=20):
    """
    Retorna os top N CNAEs mais comuns
    """
    top_cnae = df['cnae_fiscal_principal'].value_counts().head(top_n).reset_index()
    top_cnae.columns = ['CNAE', 'Quantidade']
    # Sanitizar dados para evitar erros JavaScript
    top_cnae = sanitize_chart_data(top_cnae, text_columns=['CNAE'], numeric_columns=['Quantidade'])
    return top_cnae


@st.cache_data
def load_cnae_descriptions(file_path="dados/codigos_cnae_2.csv"):
    """
    Carrega o arquivo CSV com descrições de CNAEs
    Formato esperado: CNAE;DESCRIÇÃO
    """
    df_cnae = pd.read_csv(file_path, sep=';', dtype={'CNAE': str}, encoding='utf-8-sig')
    # Remover espaços e garantir formato consistente
    df_cnae['CNAE'] = df_cnae['CNAE'].str.strip()
    df_cnae['DESCRIÇÃO'] = df_cnae['DESCRIÇÃO'].str.strip()
    return df_cnae


def get_top_cnaes_with_description(df, df_cnae, top_n=20):
    """
    Retorna os top N CNAEs mais comuns COM descrições
    """
    # Obter top CNAEs
    top_cnae = df['cnae_fiscal_principal'].value_counts().head(top_n).reset_index()
    top_cnae.columns = ['CNAE', 'Quantidade']

    # Garantir que CNAE é string
    top_cnae['CNAE'] = top_cnae['CNAE'].astype(str).str.strip()

    # Fazer merge com descrições
    top_cnae = top_cnae.merge(
        df_cnae[['CNAE', 'DESCRIÇÃO']],
        on='CNAE',
        how='left'
    )

    # Preencher descrições ausentes
    top_cnae['DESCRIÇÃO'] = top_cnae['DESCRIÇÃO'].fillna('Descrição não encontrada')

    # Criar coluna combinada para exibição
    top_cnae['CNAE_Descricao'] = top_cnae['CNAE'] + ' - ' + top_cnae['DESCRIÇÃO']

    # Sanitizar dados
    top_cnae = sanitize_chart_data(
        top_cnae,
        text_columns=['CNAE', 'DESCRIÇÃO', 'CNAE_Descricao'],
        numeric_columns=['Quantidade']
    )

    return top_cnae


def get_situacao_distribution(df):
    """
    Retorna a distribuição por situação cadastral
    """
    dist = df['situacao_descricao'].value_counts().reset_index()
    dist.columns = ['Situação', 'Quantidade']
    # Sanitizar dados para evitar erros JavaScript
    dist = sanitize_chart_data(dist, text_columns=['Situação'], numeric_columns=['Quantidade'])
    return dist


def get_timeline_data(df, date_column='ano_inicio'):
    """
    Retorna dados de evolução temporal
    """
    timeline = df[date_column].value_counts().sort_index().reset_index()
    timeline.columns = ['Ano', 'Quantidade']

    # Filtrar anos válidos (remover NaN e anos inválidos)
    timeline = timeline[timeline['Ano'].notna()]
    timeline = timeline[(timeline['Ano'] >= 1900) & (timeline['Ano'] <= datetime.now().year)]

    # Sanitizar dados para evitar erros JavaScript
    timeline = sanitize_chart_data(timeline, numeric_columns=['Ano', 'Quantidade'])

    return timeline


def filter_dataframe(df, filters):
    """
    Aplica filtros ao DataFrame

    Args:
        df: DataFrame original
        filters: dict com os filtros {'column': [values]}

    Returns:
        DataFrame filtrado
    """
    filtered_df = df.copy()

    for column, values in filters.items():
        if values and len(values) > 0:
            filtered_df = filtered_df[filtered_df[column].isin(values)]

    return filtered_df


def format_cnpj(cnpj_basico):
    """
    Formata o CNPJ básico (8 dígitos) para exibição
    """
    if pd.isna(cnpj_basico):
        return ''

    cnpj_str = str(cnpj_basico).zfill(8)
    return f"{cnpj_str[:2]}.{cnpj_str[2:5]}.{cnpj_str[5:8]}"


def export_to_csv(df):
    """
    Converte DataFrame para CSV para download
    """
    return df.to_csv(index=False).encode('utf-8')


def export_to_excel(df):
    """
    Converte DataFrame para Excel para download
    """
    from io import BytesIO
    output = BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Estabelecimentos')

    return output.getvalue()


@st.cache_data
def load_geojson(file_path="municipios_rs.json"):
    """
    Carrega o arquivo GeoJSON com os municípios do RS
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)

    return geojson_data


def normalize_municipio_name(name):
    """
    Normaliza o nome do município para fazer match com o GeoJSON
    Remove acentos e converte para maiúsculas
    """
    import unicodedata

    if pd.isna(name):
        return ''

    # Remove acentos
    nfkd = unicodedata.normalize('NFKD', str(name))
    name_normalized = ''.join([c for c in nfkd if not unicodedata.combining(c)])

    return name_normalized.upper().strip()


def get_municipios_data_for_map(df):
    """
    Prepara os dados agregados por município para o mapa
    """
    # Contar estabelecimentos por município
    mun_counts = df['nome_municipio'].value_counts().reset_index()
    mun_counts.columns = ['municipio', 'quantidade']

    # Normalizar nomes dos municípios
    mun_counts['municipio_normalizado'] = mun_counts['municipio'].apply(normalize_municipio_name)

    # Sanitizar dados para evitar erros JavaScript
    mun_counts = sanitize_chart_data(mun_counts, text_columns=['municipio', 'municipio_normalizado'], numeric_columns=['quantidade'])

    return mun_counts


def sanitize_chart_data(df, text_columns=None, numeric_columns=None):
    """
    Sanitiza dados para evitar erros JavaScript nos gráficos Plotly

    Args:
        df: DataFrame a ser sanitizado
        text_columns: lista de colunas de texto para limpar caracteres especiais
        numeric_columns: lista de colunas numéricas para remover NaN/Inf

    Returns:
        DataFrame sanitizado
    """
    df_clean = df.copy()

    # Limpar colunas de texto
    if text_columns:
        for col in text_columns:
            if col in df_clean.columns:
                # Remover caracteres problemáticos e substituir por versões seguras
                df_clean[col] = df_clean[col].astype(str)
                df_clean[col] = df_clean[col].str.replace(';', ',', regex=False)
                df_clean[col] = df_clean[col].str.replace("'", '', regex=False)
                df_clean[col] = df_clean[col].str.replace('"', '', regex=False)

    # Limpar colunas numéricas
    if numeric_columns:
        for col in numeric_columns:
            if col in df_clean.columns:
                # Remover NaN e valores infinitos
                df_clean = df_clean[df_clean[col].notna()]
                df_clean = df_clean[~df_clean[col].isin([float('inf'), float('-inf')])]

    return df_clean
