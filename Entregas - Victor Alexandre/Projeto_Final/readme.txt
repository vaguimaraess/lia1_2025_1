# Projeto de Análise de Vendas para Energia Solar

**Versão:** 1.0
**Data:** 25 de Junho de 2025

---

## 1. Resumo do Projeto

Este projeto consiste em um sistema de Business Intelligence (BI) e gestão de vendas desenvolvido em Python com a biblioteca Streamlit. Ele é composto por dois aplicativos principais:

1.  **Aplicativo de Coleta (`app.solar.py`):** Uma interface simples para que os funcionários de campo registrem informações detalhadas de cada visita a um cliente potencial. Os dados coletados incluem informações do cliente, localização (incluindo coordenadas geográficas), perfil do cliente e valor da fatura de energia.

2.  **Dashboard de Análise Estratégica (`app.analisesolar.py`):** Uma plataforma completa para a equipe de gestão. Ela consolida todos os dados coletados, permitindo análises aprofundadas através de filtros interativos, rankings de desempenho, mapas geográficos, e funcionalidades avançadas como:
    * **Orientador IA:** Utiliza a API do Google Gemini para gerar análises e recomendações estratégicas.
    * **Plano de Ação:** Permite transformar as recomendações da IA em tarefas rastreáveis.
    * **Gestão de Metas:** Ferramenta para definir e acompanhar metas de desempenho da equipe.
    * **Automação:** Gera resumos para comunicação e permite a exportação de dados.

---

## 2. Estrutura dos Arquivos

O projeto utiliza os seguintes arquivos, que devem estar no mesmo diretório:

* `app.solar.py`: O código do aplicativo de coleta de dados.
* `app.analisesolar.py`: O código do dashboard de análise estratégica.
* `dados_visitas.csv`: Arquivo onde os dados das visitas são armazenados. (É criado pelo app de coleta).
* `planos_de_acao.csv`: Arquivo que armazena as tarefas criadas a partir das recomendações da IA.
* `metas_equipe.csv`: Arquivo que armazena as metas de desempenho da equipe.
* `README.txt`: Este arquivo de instruções.

---

## 3. Como Executar o Projeto

### Pré-requisitos

* Python 3.8 ou superior instalado.

### Instalação de Bibliotecas

Abra o terminal ou prompt de comando e instale as bibliotecas necessárias com o seguinte comando:

```bash
pip install streamlit pandas plotly google-generativeai numpy
```

### Execução dos Aplicativos

1.  **Para iniciar o App de Coleta:**
    Navegue até o diretório do projeto no terminal e execute:
    ```bash
    streamlit run app.solar.py
    ```

2.  **Para iniciar o Dashboard de Análise:**
    Abra um novo terminal, navegue até o mesmo diretório e execute:
    ```bash
    streamlit run app.analisesolar.py
    ```

---

## 4. Instruções de Uso

### App de Coleta
- Preencha todos os campos do formulário para cada visita realizada.
- **Coordenadas Geográficas:** Este campo é opcional, mas **altamente recomendado** para a funcionalidade do mapa no dashboard. Para obtê-las, pesquise o endereço no Google Maps, clique com o botão direito no local exato e, em seguida, clique nas coordenadas que aparecem para copiá-las. Cole a latitude e a longitude nos campos correspondentes.
- Clique em "Registrar Visita" para salvar os dados.

### Dashboard de Análise

- **Filtros (Barra Lateral):** Use os filtros de data, local, funcionário e perfil para segmentar os dados que são exibidos em todas as abas do dashboard.

- **Aba "Ações Rápidas":**
    - **Gerador de Foco Semanal:** Defina critérios para gerar uma mensagem pronta com os clientes prioritários para a equipe contatar.
    - **Exportar Dados:** Baixe os dados atualmente filtrados como um arquivo CSV.

- **Aba "Análise Geográfica":**
    - Visualize um mapa interativo com a localização das visitas. O tamanho e a cor dos pontos representam o valor da fatura, destacando as áreas de maior potencial.

- **Aba "Ranking & Metas":**
    - Veja os rankings de desempenho da equipe com base em visitas, ticket médio e potencial gerado.
    - Acompanhe o progresso de cada funcionário em relação às metas definidas.

- **Aba "Orientador IA":**
    - Clique no botão "Gerar Análise e Recomendações" para que a IA do Google analise os dados filtrados e forneça insights estratégicos.
    - **Requisito:** É necessário configurar uma chave de API do Google (veja a seção 5).

- **Aba "Plano de Ação":**
    - Após a IA gerar uma análise, você pode usar o formulário nesta aba para transformar uma recomendação em uma tarefa específica, atribuindo um responsável e um prazo.
    - Acompanhe todas as ações em andamento na tabela.

- **Área do Gestor (Barra Lateral):**
    - Para definir novas metas, digite a senha `admin123` no campo "Senha para definir metas".
    - Um formulário aparecerá para criar novas metas de "Nº de Visitas" ou "Ticket Médio" para cada funcionário.

---

## 5. Configuração da API do Google (Para a IA)

Para que a funcionalidade "Orientador IA" funcione, você precisa de uma chave de API do Google AI Studio.

1.  Obtenha sua chave de API em [https://aistudio.google.com/](https://aistudio.google.com/).
2.  Quando for publicar seu aplicativo (ex: no Streamlit Community Cloud), crie um "Secret" chamado `GOOGLE_API_KEY` e cole sua chave de API lá. O aplicativo está programado para ler esta variável de ambiente de forma segura.
