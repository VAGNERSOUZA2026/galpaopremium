import streamlit as st

st.title("Sistema de Gestão de Vinhos - Galpão")

# 1. Inicializar o contador do file_uploader no session_state se não existir
if "file_uploader_key" not in st.session_state:
    st.session_state.file_uploader_key = 0

# 2. Widgets de entrada vinculados ao session_state
codigo_barra = st.text_input(
    "Código de Barras do Mapa (Ex: 1234552)", 
    key="codigo_barra"
)

# O file_uploader usa uma chave dinâmica baseada no contador
arquivo_pedido = st.file_uploader(
    "Arquivo de Pedido (Excel ou TXT)", 
    type=["xlsx", "xls", "txt", "csv"], 
    key=f"arquivo_pedido_{st.session_state.file_uploader_key}"
)

itens_manuais = st.text_area(
    "Ou digite um item por linha no formato rápido (Nome / Safra / Qtd):", 
    key="itens_manuais"
)

# 3. Botão para salvar o pedido
if st.button("💾 Salvar Pedido no Sistema"):
    # Validação simples
    if not codigo_barra and not arquivo_pedido and not itens_manuais:
        st.warning("Preencha ou envie pelo menos um campo antes de salvar!")
    else:
        # ---- SEU CÓDIGO DE SALVAR NO BANCO/SISTEMA AQUI ----
        # Exemplo: salvar_pedido(codigo_barra, arquivo_pedido, itens_manuais)
        
        st.success("Pedido salvo com sucesso!")
        
        # 4. Limpar os campos normais via session_state
        # (Nota: não definimos st.session_state.arquivo_pedido aqui)
        st.session_state.codigo_barra = ""
        st.session_state.itens_manuais = ""
        
        # 5. Truque para limpar o file_uploader: 
        # Incrementar o contador muda o ID do componente, recriando-o vazio.
        st.session_state.file_uploader_key += 1
        
        # 6. Atualizar a tela imediatamente
        st.rerun()
