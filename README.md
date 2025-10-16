# Dashboard de Análise - Estabelecimentos RFB

Dashboard interativo desenvolvido com Streamlit para análise de dados de estabelecimentos da Receita Federal do Brasil (RFB).

## Funcionalidades

### 1. Visão Geral
- Estatísticas gerais do dataset
- Total de estabelecimentos, matrizes e filiais
- Distribuição por situação cadastral
- Gráficos interativos de distribuição

### 2. Análise por Situação Cadastral
- Distribuição detalhada por situação (Ativa, Baixada, Inapta, etc.)
- Evolução temporal das mudanças de situação
- Tabelas com percentuais

### 3. Análise Geográfica
- **Mapa interativo do Rio Grande do Sul**: Visualização coroplética com densidade de estabelecimentos por município
- Top municípios com mais estabelecimentos
- Visualização configurável (5-50 municípios)
- Dados detalhados com percentuais

### 4. Análise Temporal
- Evolução de aberturas por ano
- Mudanças de situação ao longo do tempo
- Distribuição por década
- Gráficos de linha e área

### 5. Análise por CNAE
- Top CNAEs (atividades econômicas) mais comuns
- Treemap interativo de distribuição
- Dados detalhados com percentuais

### 6. Exportação de Dados
- Download em formato CSV
- Download em formato Excel
- Preview dos dados filtrados

## Filtros Disponíveis

O dashboard oferece filtros interativos na barra lateral:

- **Situação Cadastral**: Filtrar por Ativa, Baixada, Inapta, etc.
- **Tipo de Estabelecimento**: Matriz ou Filial
- **Município**: Selecionar municípios específicos
- **Ano de Início**: Filtrar por período de abertura

Todos os gráficos e estatísticas são atualizados automaticamente conforme os filtros aplicados.

## Instalação

### Requisitos
- Python 3.8 ou superior

### Passos

1. Clone ou baixe este repositório

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Como Usar

1. Certifique-se de que os seguintes arquivos estão no mesmo diretório que o `app.py`:
   - `estabelecimentos_filtrado.csv` (dados dos estabelecimentos)
   - `municipios_rs.json` (geometrias dos municípios do RS para o mapa)

2. Execute o aplicativo:
```bash
streamlit run app.py
```

3. O dashboard será aberto automaticamente no seu navegador (geralmente em `http://localhost:8501`)

4. Use os filtros na barra lateral para explorar os dados

5. Navegue pelas diferentes abas para ver análises específicas

## Estrutura do Projeto

```
RFB_CSV/
│
├── app.py                          # Aplicativo principal Streamlit
├── utils.py                        # Funções auxiliares de processamento
├── requirements.txt                # Dependências do projeto
├── README.md                       # Este arquivo
├── estabelecimentos_filtrado.csv   # Dataset dos estabelecimentos
└── municipios_rs.json              # GeoJSON com geometrias dos municípios do RS
```

## Tecnologias Utilizadas

- **Streamlit**: Framework para criar aplicativos web de dados
- **Pandas**: Manipulação e análise de dados
- **Plotly**: Visualizações interativas
- **NumPy**: Operações numéricas
- **OpenPyXL**: Exportação para Excel

## Dados

O dataset contém informações sobre estabelecimentos da RFB com as seguintes colunas:

- `cnpj_basico`: CNPJ base (8 primeiros dígitos)
- `identificador_matriz_filial`: 1=Matriz, 2=Filial
- `situacao_cadastral`: Código da situação cadastral
- `data_situacao_cadastral`: Data da última mudança de situação
- `data_inicio_atividade`: Data de início das atividades
- `cnae_fiscal_principal`: Código CNAE da atividade principal
- `nome_municipio`: Nome do município

## Otimizações

- **Cache de dados**: Os dados são carregados uma única vez e mantidos em cache
- **Processamento eficiente**: Uso otimizado do Pandas para milhões de registros
- **Gráficos responsivos**: Visualizações se adaptam ao tamanho da tela

## Solução de Problemas

### Erro ao carregar dados
- Verifique se o arquivo csv está no diretório correto
- Certifique-se de que o arquivo não está corrompido

### Mapa não aparece
- Verifique se o arquivo `municipios_rs.json` está no diretório dados
- O mapa usa o GeoJSON dos municípios do RS para criar a visualização coroplética

### Dashboard lento
- O primeiro carregamento pode levar alguns segundos devido ao tamanho do dataset
- Use os filtros para trabalhar com subconjuntos menores de dados

### Erro de memória
- O dataset é grande (~4.6 milhões de registros)