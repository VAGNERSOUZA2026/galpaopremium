Atue como um Engenheiro de Software Sênior e Especialista em UI/UX com Python e Streamlit. 

Preciso que você crie um protótipo funcional em Streamlit para o aplicativo "Wine Map Pro" (Sistema de Gestão de Estoque e Localização de Vinhos), baseado nas seguintes especificações visuais e funcionais:

1. TEMA E IDENTIDADE VISUAL:
- Tema escuro (Dark Mode) simulando o design da imagem: fundo preto/grafista (#121212), detalhes em vinho/bordô (#581825), acentos em dourado/amarelo (#C9A227) e texto em branco (#FFFFFF).
- Uso de componentes customizados ou st.markdown com CSS injetado para estilizar botões, métricas e cartões com bordas arredondadas e as cores do projeto.

2. ESTRUTURA DE NAVEGAÇÃO (Menu Lateral / Sidebar):
- Logo "Wine Map Pro" com o ícone de taça.
- Menu de navegação lateral contendo as seguintes páginas principais:
  - 📊 Dashboard (Visão geral com métricas: Total de vinhos cadastrados, Paletas ocupadas, Alertas de estoque).
  - 🔍 Buscar Vinho (Barra de pesquisa e filtros por Tipo, Safra, País e Corredor).
  - ➕ Cadastro (Formulário para adicionar novos vinhos com campos de nome, tipo, safra, país, vinícola, volume, quantidade e localização).
  - 📦 Estoque (Tabela completa do inventário dividida por abas: Tinto, Branco, Espumante).
  - 🗺️ Mapa do Galpão (Visualização em grade dos corredores com status de ocupação: Livre, Quase Cheio, Cheio).
  - 📈 Relatórios (Opções para exportar dados em Excel/CSV e PDF fictícios).

3. REQUISITOS TÉCNICOS:
- Utilize a biblioteca Streamlit (st.sidebar, st.selectbox, st.metric, st.dataframe, st.columns, st.tabs, etc.).
- Crie um banco de dados simulado em memória (usando Pandas DataFrames com dados mockados de vinhos como Château Margaux, Miolo Reserva, Catena Zapata, Pêra-Manca) para que todas as telas interajam e filtrem os dados corretamente.
- O código deve estar limpo, bem comentado e pronto para ser executado localmente com o comando `streamlit run`.

Por favor, forneça o código Python completo estruturado para este aplicativo.
