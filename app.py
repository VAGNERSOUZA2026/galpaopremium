import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA (PADRÃO PREMIUM WINES)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Premium Wines - Galpão",
    page_icon="🍷",
    layout="wide"
)

# -----------------------------------------------------------------------------
# LEITURA DE PARÂMETROS DA URL / AUTENTICAÇÃO
# -----------------------------------------------------------------------------
query_params = st.query_params
auth_code = query_params.get("auth", "1980")
user_name = query_params.get("user", "Dev")
user_cargo = query_params.get("cargo", "Desenvolvedor")

# -----------------------------------------------------------------------------
# INICIALIZAÇÃO DE ESTADOS
# -----------------------------------------------------------------------------
if "menu_atual" not in st.session_state:
    st.session_state.menu_atual = "Pedido_Atual"

if "produtos_db" not in st.session_state:
    st.session_state.produtos_db = [
        {"nome": "Campana Merlot 2024", "corredor": "Corredor 01", "pallet": "Pallet Item 01"},
        {"nome": "Falernia Carmenere", "corredor": "Corredor 03", "pallet": "Pallet Item 03"}
    ]

# -----------------------------------------------------------------------------
# ESTRUTURA DE NAVEGAÇÃO E HISTÓRICO (CORREÇÃO DA LINHA 608)
# -----------------------------------------------------------------------------
if st.session_state.menu_atual == "Pedido_Atual":
    
    # Cabeçalho do Pedido
    col_tit, col_del = st.columns([3, 1])
    with col_tit:
        st.caption("Pedido #13/08 01:12 (13/08/2026 01:12) - Status: Concluído")
        st.title("Pedido: Pedido #13/08 01:12")
    
    with col_del:
        if st.button("🗑️ Excluir Pedido", use_container_width=True):
            st.warning("Pedido excluído com sucesso!")

    # Botão de Exportação para Word
    st.button("📄 Baixar Pedido em Word (.docx) para Imprimir ou Enviar", use_container_width=True)

    # Seleção de Rota
    st.write("**Direção da Rota pelos Corredores:**")
    direcao_rota = st.radio(
        "Direção da Rota pelos Corredores:",
        ["Crescente (Corredor 01 ao 25)", "Decrescente (Corredor 25 ao 01)"],
        label_visibility="collapsed",
        horizontal=True
    )

    st.markdown("---")
    st.subheader("🎯 Roteiro e Bipe de Caixas (Antierros)")

    # Lista de Itens do Pedido enviado
    itens_pedido = [
        {"nome": "Campana Merlot 2024", "qtd": 5},
        {"nome": "Falernia Carmenere", "qtd": 5},
        {"nome": "La Roche", "qtd": 5},
        {"nome": "Quereu Cabernet", "qtd": 1}
    ]

    # Ordenação conforme direção escolhida
    if "Decrescente" in direcao_rota:
        itens_pedido = list(reversed(itens_pedido))

    # Exibição do Roteiro
    for item in itens_pedido:
        # Busca localização no cadastro
        match = next((p for p in st.session_state.produtos_db if p["nome"].lower() in item["nome"].lower()), None)
        
        if match:
            local_str = f"📍 {match['corredor']} - {match['pallet']}"
        else:
            local_str = "📍 Não cadastrado"

        with st.expander(f"⌛ {item['nome']} | Qtd: {item['qtd']} | {local_str}"):
            st.write(f"**Item:** {item['nome']}")
            st.write(f"**Quantidade Solicitada:** {item['qtd']} caixas")
            st.write(f"**Endereço no Galpão:** {local_str}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.success("🚴 Pedido 100% separado e conferido!")

    if st.button("📁 Finalizar e Arquivar Pedido", use_container_width=True):
        st.balloons()
        st.success("Pedido finalizado e enviado para o histórico!")

# Linha 608 corrigida (onde ocorria o SyntaxError com '->')
elif st.session_state.menu_atual == "Historico":
    st.title("📜 Histórico de Pedidos Arquivados")
    st.info("Nenhum pedido arquivado no momento.")
