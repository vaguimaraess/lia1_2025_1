import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="App de Coleta de Dados - Energia Solar",
    page_icon="☀️",
    layout="wide"
)

# --- CONSTANTES E CONFIGURAÇÕES ---
NOME_ARQUIVO_DADOS = 'dados_visitas.csv'

LISTA_FUNCIONARIOS = [
    "Ana Julia", "Bruno Carvalho", "Carla Dias", "Daniel Martins", "Fernanda Souza", "Victor Alexandre", "Vinicius Alexandre"
]
# NOVA LISTA: Perfis de cliente para segmentação
PERFIS_CLIENTE = ["Residencial", "Comercial", "Industrial", "Agronegócio", "Condomínio"]

# --- FUNÇÕES AUXILIARES ---
def carregar_dados():
    if os.path.exists(NOME_ARQUIVO_DADOS):
        try:
            return pd.read_csv(NOME_ARQUIVO_DADOS)
        except pd.errors.EmptyDataError:
            return criar_dataframe_vazio()
    else:
        return criar_dataframe_vazio()

def criar_dataframe_vazio():
    """Cria um DataFrame com a estrutura completa, incluindo as novas colunas."""
    colunas = [
        'data_visita', 'nome_funcionario', 'nome_consumidor', 'cidade', 
        'estado', 'endereco', 'telefone', 'valor_fatura_r$', 'observacoes',
        'latitude', 'longitude', 'perfil_cliente' # NOVAS COLUNAS
    ]
    return pd.DataFrame(columns=colunas)

# --- INTERFACE PRINCIPAL DO STREAMLIT ---
st.title("☀️ Aplicativo de Coleta de Dados de Visitas")
st.markdown("---")
st.header("📝 Registrar Nova Visita")

with st.form("form_nova_visita", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        nome_funcionario = st.selectbox("Selecione seu Nome", options=LISTA_FUNCIONARIOS, index=None, placeholder="Selecione seu nome na lista")
        nome_consumidor = st.text_input("Nome do Consumidor", placeholder="Nome do cliente visitado")
        valor_fatura = st.number_input("Valor Médio da Fatura de Energia (R$)", min_value=0.0, format="%.2f")
        
        # NOVO: Campo para perfil do cliente
        perfil_cliente = st.multiselect("Perfil do Cliente", options=PERFIS_CLIENTE, placeholder="Selecione um ou mais perfis")
        
    with col2:
        telefone = st.text_input("Telefone/WhatsApp", placeholder="(XX) XXXXX-XXXX")
        data_visita = st.date_input("Data da Visita", datetime.now())
        observacoes = st.text_area("Observações", placeholder="Cliente interessado, telhado com boa orientação, etc.")

    st.markdown("#### Localização da Visita")
    col_end1, col_end2 = st.columns(2)
    with col_end1:
        cidade = st.text_input("Cidade", placeholder="Ex: Goiânia")
        estado = st.selectbox("Estado", ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'], index=8)
    with col_end2:
        endereco = st.text_area("Endereço Completo", placeholder="Rua das Flores, 123, Setor Bueno")

    # NOVOS CAMPOS: Latitude e Longitude
    st.markdown("##### Coordenadas Geográficas (Opcional, mas recomendado)")
    st.info("Para obter, procure o endereço no Google Maps, clique com o botão direito no local e depois clique nas coordenadas para copiar.")
    col_geo1, col_geo2 = st.columns(2)
    with col_geo1:
        latitude = st.number_input("Latitude", placeholder="-16.686891", format="%.6f")
    with col_geo2:
        longitude = st.number_input("Longitude", placeholder="-49.264870", format="%.6f")

    submitted = st.form_submit_button("✅ Registrar Visita")

    if submitted:
        if not nome_funcionario or not nome_consumidor or not endereco or not cidade:
            st.warning("Por favor, preencha os campos obrigatórios (Funcionário, Consumidor, Endereço e Cidade).")
        else:
            try:
                df_existente = carregar_dados()
                
                # Converte a lista de perfis para uma string separada por vírgulas
                perfis_str = ",".join(perfil_cliente) if perfil_cliente else ""

                novo_dado = pd.DataFrame([{
                    'data_visita': data_visita.strftime('%Y-%m-%d'),
                    'nome_funcionario': nome_funcionario,
                    'nome_consumidor': nome_consumidor,
                    'cidade': cidade,
                    'estado': estado,
                    'endereco': endereco,
                    'telefone': telefone,
                    'valor_fatura_r$': valor_fatura,
                    'observacoes': observacoes,
                    'latitude': latitude,
                    'longitude': longitude,
                    'perfil_cliente': perfis_str
                }])
                
                df_atualizado = pd.concat([df_existente, novo_dado], ignore_index=True)
                df_atualizado.to_csv(NOME_ARQUIVO_DADOS, index=False)
                st.success("🎉 Visita registrada com sucesso!")
            except Exception as e:
                st.error(f"Ocorreu um erro ao salvar os dados: {e}")

st.markdown("---")
# --- SEÇÃO DE VISUALIZAÇÃO DE DADOS (VISÃO DO FUNCIONÁRIO) ---
st.header("📊 Suas Últimas Visitas Registradas")

# Carregar os dados para visualização
df_dados = carregar_dados()

if df_dados.empty:
    st.info("Ainda não há dados coletados para exibir. Comece registrando uma nova visita no formulário acima.")
else:
    # Garantir que as colunas de data e valor estão nos formatos corretos para análise
    df_dados['data_visita'] = pd.to_datetime(df_dados['data_visita'])
    df_dados['valor_fatura_r$'] = pd.to_numeric(df_dados['valor_fatura_r$'])

    st.write("Visão geral de todos os registros:")
    st.dataframe(df_dados.tail(10), use_container_width=True) # Mostrar apenas os 10 últimos registros

    # --- Filtro interativo para o funcionário ver seus próprios dados ---
    st.subheader("Filtrar seus resultados")
    funcionario_selecionado = st.selectbox(
        "Ver registros de:", 
        options=['Todos'] + sorted(df_dados['nome_funcionario'].unique().tolist())
    )

    if funcionario_selecionado != 'Todos':
        df_filtrado = df_dados[df_dados['nome_funcionario'] == funcionario_selecionado]
    else:
        df_filtrado = df_dados

    if not df_filtrado.empty:
        col_analise1, col_analise2 = st.columns(2)
        with col_analise1:
            total_visitas = len(df_filtrado)
            st.metric("Total de Visitas Registradas", f"{total_visitas}")
        with col_analise2:
            fatura_media = df_filtrado['valor_fatura_r$'].mean()
            st.metric("Valor Médio da Fatura", f"R$ {fatura_media:.2f}")

        st.write(f"Detalhes para: **{funcionario_selecionado}**")
        st.dataframe(df_filtrado, use_container_width=True)
    else:
        st.write("Nenhum registro encontrado para a seleção.")
