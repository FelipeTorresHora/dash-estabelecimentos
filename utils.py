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

# Mapeamento de identificador matriz/filial
MATRIZ_FILIAL = {
    '1': 'MATRIZ',
    '2': 'FILIAL'
}


@st.cache_data
def load_data(file_path):
    """
    Carrega o arquivo CSV com otimização de tipos de dados
    """
    dtype_spec = {
        'cnpj_basico': str,
        'identificador_matriz_filial': str,
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

    # Mapear matriz/filial
    df['tipo_estabelecimento'] = df['identificador_matriz_filial'].map(MATRIZ_FILIAL)

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


def get_summary_stats(df):
    """
    Retorna estatísticas resumidas do dataset
    """
    stats = {
        'total_estabelecimentos': len(df),
        'total_matrizes': len(df[df['tipo_estabelecimento'] == 'MATRIZ']),
        'total_filiais': len(df[df['tipo_estabelecimento'] == 'FILIAL']),
        'total_ativos': len(df[df['situacao_descricao'] == 'ATIVA']),
        'total_baixados': len(df[df['situacao_descricao'] == 'BAIXADA']),
        'total_municipios': df['nome_municipio'].nunique(),
        'total_cnaes': df['cnae_fiscal_principal'].nunique()
    }

    return stats


def get_top_municipios(df, top_n=20):
    """
    Retorna os top N municípios com mais estabelecimentos
    """
    top_mun = df['nome_municipio'].value_counts().head(top_n).reset_index()
    top_mun.columns = ['Município', 'Quantidade']
    return top_mun


def get_top_cnaes(df, top_n=20):
    """
    Retorna os top N CNAEs mais comuns
    """
    top_cnae = df['cnae_fiscal_principal'].value_counts().head(top_n).reset_index()
    top_cnae.columns = ['CNAE', 'Quantidade']
    return top_cnae


def get_situacao_distribution(df):
    """
    Retorna a distribuição por situação cadastral
    """
    dist = df['situacao_descricao'].value_counts().reset_index()
    dist.columns = ['Situação', 'Quantidade']
    return dist


def get_matriz_filial_distribution(df):
    """
    Retorna a distribuição matriz/filial
    """
    dist = df['tipo_estabelecimento'].value_counts().reset_index()
    dist.columns = ['Tipo', 'Quantidade']
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

    return mun_counts
