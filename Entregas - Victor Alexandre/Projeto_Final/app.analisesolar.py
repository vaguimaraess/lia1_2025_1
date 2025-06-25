import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
import google.generativeai as genai
import numpy as np

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Dashboard de Análise Estratégica",
    page_icon="🧠",
    layout="wide"
)

# --- CONSTANTES E CONFIGURAÇÕES ---
NOME_ARQUIVO_DADOS = 'dados_visitas.csv'
NOME_ARQUIVO_ACOES = 'planos_de_acao.csv'
NOME_ARQUIVO_METAS = 'metas_equipe.csv'

LISTA_FUNCIONARIOS = [
    "Ana Julia", "Bruno Carvalho", "Carla Dias", "Daniel Martins", "Fernanda Souza", "Victor Alexandre", "Vinicius Alexandre"
]
PERFIS_CLIENTE = ["Residencial", "Comercial", "Industrial", "Agronegócio", "Condomínio"]

# --- CONFIGURAÇÃO DO MODELO DE IA (GEMINI) ---
modelo_ia = None
try:
    if 'GOOGLE_API_KEY' in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        modelo_ia = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.sidebar.error(f"Erro ao configurar a API do Google: {e}. A funcionalidade de IA está desabilitada.")

# --- FUNÇÕES DE CARREGAMENTO E PREPARAÇÃO DE DADOS ---
@st.cache_data(ttl=300)
def carregar_dados(caminho_arquivo, colunas_data=[]):
    """Função genérica para carregar dados de arquivos CSV."""
    if not os.path.exists(caminho_arquivo):
        return pd.DataFrame()
    try:
        df = pd.read_csv(caminho_arquivo, encoding='latin1')
        for col in colunas_data:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        return df
    except pd.errors.EmptyDataError:
        return pd.DataFrame()

def preparar_dados_visitas(df):
    """Prepara o DataFrame de visitas, garantindo que as colunas existam."""
    if df.empty:
        return df
    df['valor_fatura_r$'] = pd.to_numeric(df['valor_fatura_r$'], errors='coerce').fillna(0)
    for col in ['cidade', 'estado', 'nome_funcionario', 'perfil_cliente', 'telefone']:
        if col not in df.columns:
            df[col] = ''
        df[col] = df[col].fillna('')
    if 'data_visita' in df.columns and pd.api.types.is_datetime64_any_dtype(df['data_visita']):
      df['mes_ano'] = df['data_visita'].dt.to_period('M').astype(str)
    for col in ['latitude', 'longitude']:
        if col not in df.columns:
            df[col] = np.nan
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

# --- FUNÇÃO HELPER PARA DOWNLOAD ---
@st.cache_data
def convert_df_to_csv(df):
    """Converte um DataFrame para CSV em bytes, pronto para download."""
    return df.to_csv(index=False).encode('utf-8')

# --- CARREGANDO TODOS OS DADOS ---
df_visitas = preparar_dados_visitas(carregar_dados(NOME_ARQUIVO_DADOS, colunas_data=['data_visita']))

# --- TÍTULO E FILTROS LATERAIS ---
st.title("🧠 Dashboard de Análise Estratégica de Vendas")
st.sidebar.title("Opções")
st.sidebar.header("Filtros de Análise")

if df_visitas.empty:
    st.warning("Nenhum dado de visita encontrado. Comece registrando visitas no app de coleta.")
    st.stop()
# --- FILTROS ---
estado_selecionado = st.sidebar.multiselect('Estado', options=sorted(df_visitas['estado'].unique()), default=sorted(df_visitas['estado'].unique()))
cidades_disponiveis = sorted(df_visitas[df_visitas['estado'].isin(estado_selecionado)]['cidade'].unique())
cidade_selecionada = st.sidebar.multiselect('Cidade', options=cidades_disponiveis, default=cidades_disponiveis)
funcionario_selecionado = st.sidebar.multiselect('Funcionário', options=LISTA_FUNCIONARIOS, default=LISTA_FUNCIONARIOS)

# NOVO FILTRO: Perfil de Cliente
perfis_disponiveis = sorted(list(set(p for sublist in df_visitas['perfil_cliente'].str.split(',') for p in sublist if p)))
perfil_selecionado = st.sidebar.multiselect('Perfil do Cliente', options=perfis_disponiveis, default=perfis_disponiveis)

min_date, max_date = df_visitas['data_visita'].min().date(), df_visitas['data_visita'].max().date()
if min_date <= max_date:
    data_selecionada = st.sidebar.date_input('Período da Visita', value=(min_date, max_date), min_value=min_date, max_value=max_date)
else:
    data_selecionada = (min_date, max_date)

# --- APLICANDO FILTROS ---
df_filtrado = df_visitas.copy()
if len(data_selecionada) == 2:
    df_filtrado = df_filtrado[df_filtrado['data_visita'].dt.date.between(data_selecionada[0], data_selecionada[1])]
if estado_selecionado:
    df_filtrado = df_filtrado[df_filtrado['estado'].isin(estado_selecionado)]
if cidade_selecionada:
    df_filtrado = df_filtrado[df_filtrado['cidade'].isin(cidade_selecionada)]
if funcionario_selecionado:
    df_filtrado = df_filtrado[df_filtrado['nome_funcionario'].isin(funcionario_selecionado)]

# Lógica do novo filtro de perfil
if perfil_selecionado:
    df_filtrado = df_filtrado[df_filtrado['perfil_cliente'].str.contains('|'.join(perfil_selecionado), na=False)]


# --- ÁREA DO GESTOR PARA METAS ---
st.sidebar.markdown("---")
st.sidebar.header("Área do Gestor")
senha_gestor = st.sidebar.text_input("Senha para definir metas", type="password")

if senha_gestor == "admin123":
    with st.sidebar.expander("Definir Nova Meta"):
        with st.form("form_nova_meta"):
            meta_funcionario = st.selectbox("Funcionário", options=LISTA_FUNCIONARIOS)
            meta_metrica = st.selectbox("Métrica", options=["Nº de Visitas", "Ticket Médio (R$)"])
            meta_valor = st.number_input("Valor da Meta", min_value=0)
            meta_periodo = st.text_input("Período (ex: Julho/2025)", value=datetime.now().strftime("%B/%Y"))
            
            submitted_meta = st.form_submit_button("Salvar Meta")
            if submitted_meta:
                id_meta = f"META-{meta_funcionario}-{meta_periodo.replace('/', '-')}"
                nova_meta = pd.DataFrame([{'id_meta': id_meta, 'funcionario': meta_funcionario, 'metrica': meta_metrica, 'valor_meta': meta_valor, 'periodo': meta_periodo}])
                
                df_metas_existente = carregar_dados(NOME_ARQUIVO_METAS)
                
                # CORREÇÃO: Apenas tenta filtrar se o DataFrame não estiver vazio.
                if not df_metas_existente.empty:
                    df_metas_existente = df_metas_existente[df_metas_existente['id_meta'] != id_meta]
                
                df_metas_atualizado = pd.concat([df_metas_existente, nova_meta], ignore_index=True)
                df_metas_atualizado.to_csv(NOME_ARQUIVO_METAS, index=False)
                st.sidebar.success(f"Meta salva para {meta_funcionario}!")
                st.cache_data.clear()

# --- SEÇÃO PRINCIPAL - ABAS ---
tab_rapida, tab_geo, tab_rank, tab_ia, tab_acao, tab_graficos = st.tabs([
    "🚀 Ações Rápidas", 
    "🗺️ Análise Geográfica",
    "🏆 Ranking & Metas", 
    "🤖 Orientador IA", 
    "🎯 Plano de Ação", 
    "📊 Gráficos Detalhados"
])

with tab_rapida:
    st.header("🚀 Ações Rápidas e Comunicação")
    st.markdown("Use estas ferramentas para agilizar a comunicação e exportar dados.")

    # --- FERRAMENTA 1: GERADOR DE FOCO SEMANAL ---
    st.subheader("Gerador de Foco Semanal")
    
    col_foco1, col_foco2 = st.columns(2)
    top_n = col_foco1.number_input("Nº de clientes prioritários para focar", min_value=1, max_value=20, value=5)
    fatura_minima = col_foco2.number_input("Apenas clientes com fatura acima de (R$)", min_value=0, value=500)
    
    if st.button("Gerar Mensagem de Foco"):
        clientes_foco = df_filtrado[df_filtrado['valor_fatura_r$'] >= fatura_minima]
        clientes_foco = clientes_foco.nlargest(top_n, 'valor_fatura_r$')

        if clientes_foco.empty:
            st.warning("Nenhum cliente encontrado com os critérios de foco definidos.")
        else:
            data_inicio_foco = datetime.now().strftime("%d/%m/%Y")
            mensagem = f"🎯 FOCO DA SEMANA - {data_inicio_foco} 🎯\n\n"
            mensagem += "Equipe, vamos priorizar o contato com os seguintes clientes de alto potencial identificados na plataforma:\n\n"
            
            for index, row in clientes_foco.iterrows():
                mensagem += f"👤 Cliente: {row['nome_consumidor']}\n"
                mensagem += f"📍 Cidade: {row['cidade']}\n"
                mensagem += f"📞 Telefone: {row['telefone']}\n"
                mensagem += f"💰 Potencial (Fatura): R$ {row['valor_fatura_r$']:.2f}\n"
                mensagem += "--------------------------------------\n"
            
            st.text_area("Mensagem pronta para copiar e colar:", value=mensagem, height=300)

    st.markdown("---")

    # --- FERRAMENTA 2: EXPORTAR DADOS ---
    st.subheader("Exportar Dados Filtrados")
    st.markdown("Baixe a seleção de dados atual (considerando todos os filtros da barra lateral) em formato CSV.")
    
    if not df_filtrado.empty:
        csv_data = convert_df_to_csv(df_filtrado)
        st.download_button(
           label="📥 Baixar Dados para CSV",
           data=csv_data,
           file_name=f"dados_solares_{datetime.now().strftime('%Y%m%d')}.csv",
           mime='text/csv',
        )
    else:
        st.info("Não há dados para exportar com os filtros atuais.")

with tab_geo:
    # --- NOVA SEÇÃO: ANÁLISE GEOGRÁFICA ---
    st.header("🗺️ Análise Geográfica das Visitas")
    st.markdown("Visualize a distribuição e o potencial das visitas no mapa. Use os filtros na barra lateral para refinar.")
    
    df_mapa = df_filtrado.dropna(subset=['latitude', 'longitude']).copy()
    df_mapa = df_mapa[(df_mapa['latitude'] != 0) & (df_mapa['longitude'] != 0)] # Remove pontos na coordenada 0,0

    if df_mapa.empty:
        st.info("Nenhuma visita com coordenadas geográficas no período ou filtros selecionados. Adicione coordenadas no app de coleta para visualizar o mapa.")
    else:
        st.subheader("Mapa de Calor de Potencial")
        fig_mapa = px.scatter_mapbox(
            df_mapa, 
            lat="latitude", 
            lon="longitude", 
            size="valor_fatura_r$",
            color="valor_fatura_r$",
            hover_name="nome_consumidor",
            hover_data={"cidade": True, "valor_fatura_r$": True, "latitude": False, "longitude": False},
            color_continuous_scale=px.colors.cyclical.IceFire,
            size_max=50,
            zoom=3,
            mapbox_style="open-street-map"
        )
        fig_mapa.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_mapa, use_container_width=True)
        
        with st.expander("Ver dados geográficos detalhados"):
            st.dataframe(df_mapa[['nome_consumidor', 'cidade', 'valor_fatura_r$', 'perfil_cliente', 'latitude', 'longitude']])

with tab_rank:
    # --- SEÇÃO: RANKING & METAS ---
    st.header("🏆 Ranking & Metas da Equipe")
    if not df_filtrado.empty:
        st.subheader("Ranking de Performance (Período Selecionado)")
        col_rank1, col_rank2, col_rank3 = st.columns(3)
        
        with col_rank1:
            st.markdown("#### 🚀 Mais Visitas")
            ranking_visitas = df_filtrado['nome_funcionario'].value_counts().reset_index()
            ranking_visitas.columns = ['Funcionário', 'Nº de Visitas']
            st.dataframe(ranking_visitas, use_container_width=True, hide_index=True)

        with col_rank2:
            st.markdown("#### 💰 Maior Ticket Médio")
            ranking_ticket = df_filtrado.groupby('nome_funcionario')['valor_fatura_r$'].mean().round(2).sort_values(ascending=False).reset_index()
            ranking_ticket.columns = ['Funcionário', 'Ticket Médio (R$)']
            st.dataframe(ranking_ticket, use_container_width=True, hide_index=True)

        with col_rank3:
            st.markdown("#### 📈 Maior Potencial Gerado")
            ranking_potencial = df_filtrado.groupby('nome_funcionario')['valor_fatura_r$'].sum().sort_values(ascending=False).reset_index()
            ranking_potencial.columns = ['Funcionário', 'Potencial Total (R$)']
            st.dataframe(ranking_potencial, use_container_width=True, hide_index=True)

        st.subheader("Acompanhamento de Metas Individuais")
        df_metas = carregar_dados(NOME_ARQUIVO_METAS)
        if df_metas.empty:
            st.info("Nenhuma meta foi definida. Use a 'Área do Gestor' na barra lateral para criar metas.")
        else:
            for index, meta in df_metas.iterrows():
                with st.container(border=True):
                    st.markdown(f"**Funcionário:** {meta['funcionario']} | **Meta para:** {meta['periodo']}")
                    valor_atual = 0
                    if meta['metrica'] == 'Nº de Visitas':
                        valor_atual = ranking_visitas[ranking_visitas['Funcionário'] == meta['funcionario']]['Nº de Visitas'].sum()
                    elif meta['metrica'] == 'Ticket Médio (R$)':
                        if not ranking_ticket[ranking_ticket['Funcionário'] == meta['funcionario']].empty:
                            valor_atual = ranking_ticket[ranking_ticket['Funcionário'] == meta['funcionario']]['Ticket Médio (R$)'].iloc[0]

                    meta_valor = meta['valor_meta']
                    progresso = min(valor_atual / meta_valor, 1.0) if meta_valor > 0 else 0.0
                    col_meta1, col_meta2 = st.columns([1, 3])
                    with col_meta1:
                        st.metric(label=meta['metrica'], value=f"{valor_atual:.2f}", delta=f"{valor_atual - meta_valor:.2f}")
                    with col_meta2:
                        st.markdown(f"**Progresso para a meta de {meta_valor}**")
                        st.progress(progresso, text=f"{progresso:.0%}")
    else:
        st.info("Sem dados no período selecionado para exibir o ranking.")

with tab_ia:
    # --- SEÇÃO DO ORIENTADOR IA (GEMINI) ---
    st.header("🤖 Orientador de Investimentos (IA)")
    if modelo_ia:
        if not df_filtrado.empty:
            if st.button("Gerar Análise e Recomendações"):
                with st.spinner("A IA está analisando os dados..."):
                    resumo_dados = f"Análise de dados de visitas para empresa de energia solar. Período: {data_selecionada[0]} a {data_selecionada[1]}. Filtros: Estados={estado_selecionado}, Cidades={cidade_selecionada}. Total de visitas: {len(df_filtrado)}. Fatura média: R$ {df_filtrado['valor_fatura_r$'].mean():.2f}. Top 3 cidades (fatura média): {df_filtrado.groupby('cidade')['valor_fatura_r$'].mean().nlargest(3).to_dict()}. Top 3 funcionários (nº visitas): {df_filtrado['nome_funcionario'].value_counts().nlargest(3).to_dict()}"
                    prompt = f"Você é um consultor de estratégia para uma empresa de energia solar. Baseado no resumo: {resumo_dados}\n\nEscreva uma análise em português (Markdown) com: 1. **Resumo Executivo**. 2. **Pontos de Destaque** (3 a 5 pontos). 3. **Recomendações Estratégicas** (3 ações claras)."
                    try:
                        resposta = modelo_ia.generate_content(prompt)
                        st.session_state['ultima_analise_ia'] = resposta.text
                    except Exception as e:
                        st.error(f"Não foi possível gerar a análise: {e}")
                        st.session_state['ultima_analise_ia'] = f"Erro na geração da análise: {e}"
        if 'ultima_analise_ia' in st.session_state:
            st.markdown("### Análise Gerada")
            st.markdown(st.session_state['ultima_analise_ia'])
    else:
        st.info("Funcionalidade de IA desabilitada. Configure a GOOGLE_API_KEY.")

with tab_acao:
    # --- SEÇÃO DO PLANO DE AÇÃO ---
    st.header("🎯 Plano de Ação Estratégico")
    if 'ultima_analise_ia' in st.session_state and "Erro" not in st.session_state['ultima_analise_ia']:
        with st.expander("➕ Criar nova ação a partir da análise", expanded=False):
            with st.form("form_nova_acao", clear_on_submit=True):
                recomendacao_base = st.text_area("Recomendação Original (IA)", value=st.session_state.get('ultima_analise_ia', ''), height=150, disabled=True)
                acao_especifica = st.text_input("Ação Específica", placeholder="Ex: Iniciar campanha de marketing digital em São Paulo.")
                responsavel = st.selectbox("Responsável", options=LISTA_FUNCIONARIOS, index=None, placeholder="Selecione um funcionário")
                prazo = st.date_input("Prazo", min_value=datetime.today())
                status_inicial = st.selectbox("Status", options=["A Fazer", "Em Andamento", "Concluído"], index=0)
                
                if st.form_submit_button("✅ Adicionar Ação"):
                    if not acao_especifica or not responsavel:
                        st.warning("Preencha 'Ação Específica' e 'Responsável'.")
                    else:
                        id_acao = f"ACAO-{int(datetime.now().timestamp())}"
                        nova_acao = pd.DataFrame([{'id_acao': id_acao, 'recomendacao_ia': recomendacao_base, 'acao_especifica': acao_especifica, 'responsavel': responsavel, 'prazo': pd.to_datetime(prazo), 'status': status_inicial, 'data_criacao': pd.to_datetime(datetime.now())}])
                        df_acoes_existente = carregar_dados(NOME_ARQUIVO_ACOES, colunas_data=['prazo', 'data_criacao'])
                        df_acoes_atualizado = pd.concat([df_acoes_existente, nova_acao], ignore_index=True)
                        df_acoes_atualizado.to_csv(NOME_ARQUIVO_ACOES, index=False)
                        st.success(f"Ação registrada para {responsavel}!")
                        st.cache_data.clear()

    st.subheader("Acompanhamento de Ações")
    df_acoes = carregar_dados(NOME_ARQUIVO_ACOES, colunas_data=['prazo', 'data_criacao'])
    if df_acoes.empty:
        st.info("Nenhum plano de ação foi criado. Gere uma análise de IA para começar.")
    else:
        col_f1, col_f2 = st.columns(2)
        filtro_resp = col_f1.multiselect("Filtrar Ação por Responsável", options=sorted(df_acoes['responsavel'].unique()), default=[])
        filtro_stat = col_f2.multiselect("Filtrar Ação por Status", options=sorted(df_acoes['status'].unique()), default=[])

        df_acoes_filtrado = df_acoes.copy()
        if filtro_resp:
            df_acoes_filtrado = df_acoes_filtrado[df_acoes_filtrado['responsavel'].isin(filtro_resp)]
        if filtro_stat:
            df_acoes_filtrado = df_acoes_filtrado[df_acoes_filtrado['status'].isin(filtro_stat)]
        st.dataframe(df_acoes_filtrado, use_container_width=True)

with tab_graficos:
    # --- SEÇÃO DE GRÁFICOS DETALHADOS ---
    st.header("📊 Análise Gráfica Detalhada")
    if not df_filtrado.empty:
        st.subheader("Métricas Principais do Período")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Visitas Realizadas", len(df_filtrado))
        col2.metric("Valor Médio da Fatura", f"R$ {df_filtrado['valor_fatura_r$'].mean():.2f}")
        col3.metric("Potencial Total (Soma das Faturas)", f"R$ {df_filtrado['valor_fatura_r$'].sum():,.2f}".replace(",", "_").replace(".", ",").replace("_", "."))

        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            st.subheader("Top Cidades por Fatura Média")
            top_cidades = df_filtrado.groupby('cidade')['valor_fatura_r$'].mean().nlargest(10).sort_values(ascending=True)
            if not top_cidades.empty:
                fig1 = px.bar(top_cidades, x='valor_fatura_r$', y=top_cidades.index, orientation='h', title='Top 10 Cidades com Maior Fatura Média', text='valor_fatura_r$')
                fig1.update_traces(texttemplate='R$ %{text:.2f}', textposition='inside')
                fig1.update_layout(xaxis_title="Valor Médio (R$)", yaxis_title="Cidade", uniformtext_minsize=8, uniformtext_mode='hide')
                st.plotly_chart(fig1, use_container_width=True)
        with col_graf2:
            st.subheader("Visitas por Funcionário")
            visitas_funcionario = df_filtrado['nome_funcionario'].value_counts().nlargest(10).sort_values(ascending=True)
            if not visitas_funcionario.empty:
                fig2 = px.bar(visitas_funcionario, x=visitas_funcionario.values, y=visitas_funcionario.index, orientation='h', title='Top 10 Funcionários por Nº de Visitas', text=visitas_funcionario.values)
                fig2.update_traces(texttemplate='%{text}', textposition='inside')
                fig2.update_layout(xaxis_title="Nº de Visitas", yaxis_title="Funcionário", uniformtext_minsize=8, uniformtext_mode='hide')
                st.plotly_chart(fig2, use_container_width=True)
        
        st.subheader("Análise Temporal")
        analise_temporal = df_filtrado.groupby('mes_ano').agg(total_visitas=('nome_consumidor', 'count'), valor_medio_fatura=('valor_fatura_r$', 'mean')).reset_index().sort_values('mes_ano')
        if not analise_temporal.empty:
            fig3 = px.line(analise_temporal, x='mes_ano', y='total_visitas', title='Evolução do Número de Visitas por Mês', markers=True, text='total_visitas')
            fig3.update_traces(textposition="top center")
            fig3.update_layout(xaxis_title="Mês", yaxis_title="Total de Visitas")
            st.plotly_chart(fig3, use_container_width=True)
        
        with st.expander("Ver Tabela de Dados Filtrados"):
            st.dataframe(df_filtrado)
    else:
        st.info("Nenhum registro encontrado para os filtros selecionados.")