import streamlit as st

st.title("Sistema de Gestão de Vinhos - Galpão")

# Usar st.form limpa automaticamente todos os inputs de texto e arquivos ao submeter!
with st.form("form_pedido", clear_on_submit=True):
    
    codigo_barra = st.text_input("Código de Barras do Mapa (Ex: 1234552)")
    
    arquivo_pedido = st.file_uploader(
        "Arquivo de Pedido (Excel ou TXT)", 
        type=["xlsx", "xls", "txt", "csv"]
    )
    
    itens_manuais = st.text_area(
        "Ou digite um item por linha no formato rápido (Nome / Safra / Qtd):"
    )
    
    # O botão de envio do formulário
    submitted = st.form_submit_button("💾 Salvar Pedido no Sistema")

# A lógica executada após o clique no botão de envio:
if submitted:
    if not codigo_barra and not arquivo_pedido and not itens_manuais:
        st.warning("Preencha ou envie pelo menos um campo antes de salvar!")
    else:
        # ---- INSIRA SEU CÓDIGO DE SALVAR NO BANCO AQUI ----
        # Exemplo: 
        # salvar_pedido(codigo_barra, arquivo_pedido, itens_manuais)
        
        st.success("Pedido salvo com sucesso e formulários limpos!")
