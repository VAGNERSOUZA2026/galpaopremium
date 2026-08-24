import streamlit as st

# 1. Inicializar as chaves no session_state se não existirem
if "codigo_barra" not in st.session_state:
    st.session_state.codigo_barra = ""
if "arquivo_pedido" not in st.session_state:
    st.session_state.arquivo_pedido = None
if "itens_manuais" not in st.session_state:
    st.session_state.itens_manuais = ""

st.title("Sistema de Gestão de Vinhos - Galpão")

# 2. Vincular os widgets ao session_state usando o parâmetro `key`
codigo_barra = st.text_input(
    "Código de Barras do Mapa (Ex: 1234552)", 
    key="codigo_barra"
)

arquivo_pedido = st.file_uploader(
    "Arquivo de Pedido (Excel ou TXT)", 
    type=["xlsx", "xls", "txt", "csv"], 
    key="arquivo_pedido"
)

itens_manuais = st.text_area(
    "Ou digite um item por linha no formato rápido (Nome / Safra / Qtd):", 
    key="itens_manuais"
)

# 3. Botão para salvar o pedido
if st.button("💾 Salvar Pedido no Sistema"):
    # Validação simples para garantir que há algo para salvar
    if not codigo_barra and not arquivo_pedido and not itens_manuais:
        st.warning("Preencha ou envie pelo menos um campo antes de salvar!")
    else:
        # ---- SEU CÓDIGO DE SALVAR NO BANCO/SISTEMA AQUI ----
        # Exemplo: salvar_pedido(codigo_barra, arquivo_pedido, itens_manuais)
        
        st.success("Pedido salvo com sucesso!")
        
        # 4. Limpar as variáveis do session_state
        st.session_state.codigo_barra = ""
        st.session_state.arquivo_pedido = None
        st.session_state.itens_manuais = ""
        
        # 5. Forçar a atualização imediata da tela
        st.rerun()
