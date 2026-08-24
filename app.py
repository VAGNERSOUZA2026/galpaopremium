import streamlit as st

# ---- Resto das suas configurações, imports e conexão com banco/dados ----

st.title("Sistema de Gestão de Vinhos - Galpão")

# O formulário encapsula APENAS a parte de entrada dos dados e limpa tudo sozinho ao salvar
with st.form("form_pedido", clear_on_submit=True):
    
    codigo_barra = st.text_input("Código de Barras do Mapa (Ex: 1234552)")
    
    arquivo_pedido = st.file_uploader(
        "Arquivo de Pedido (Excel ou TXT)", 
        type=["xlsx", "xls", "txt", "csv"]
    )
    
    itens_manuais = st.text_area(
        "Ou digite um item por linha no formato rápido (Nome / Safra / Qtd):"
    )
    
    # Botão de envio de dentro do formulário
    submitted = st.form_submit_button("💾 Salvar Pedido no Sistema")

# Ação executada ao clicar em salvar:
if submitted:
    if not codigo_barra and not arquivo_pedido and not itens_manuais:
        st.warning("Preencha ou envie pelo menos um campo antes de salvar!")
    else:
        # ---- AQUI ENTRA O SEU CÓDIGO ORIGINAL QUE SALVA NO BANCO/SISTEMA ----
        # Exemplo: 
        # salvar_no_banco(codigo_barra, arquivo_pedido, itens_manuais)
        
        st.success("Pedido salvo com sucesso! Os campos foram limpos.")

# ==============================================================================
# ---- AQUI VOCÊ CONTINUA COM TODO O RESTO DO SEU CÓDIGO ORIGINAL DO APP ----
# Exemplo: Tabelas de listagem, gerenciamento de pedidos, exclusão semanal, etc.
# ==============================================================================

st.divider()
st.subheader("📦 Gerenciamento e Exclusão de Pedidos (Limpeza Semanal)")
# ... (todo o restante do seu layout original continua aqui embaixo intacto)
