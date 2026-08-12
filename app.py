import json
import os
import shutil
from datetime import datetime, timezone, timedelta
import pandas as pd
import streamlit as st
import urllib.parse

st.set_page_config(page_title="Premium Wines - Galpão", layout="wide", initial_sidebar_state="collapsed")

# --- CSS ---
st.markdown("""
    <style>
    .stApp { background: #F8F9FA; }
    .wine-card { background: #FFFFFF; border-radius: 10px; padding: 15px; margin-bottom: 10px; border-left: 5px solid #7A1C2E; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .stButton button { background-color: #7A1C2E; color: white; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# --- Funções Auxiliares ---
def get_hora_brasilia():
    return datetime.now(timezone(timedelta(hours=-3)))

# --- Estado e Dados ---
if "estoque" not in st.session_state: st.session_state.estoque = []
if "menu_atual" not in st.session_state: st.session_state.menu_atual = "🏠 Home"

# --- Navegação ---
st.title("Premium Wines - Galpão")
menu = st.sidebar.radio("Navegação", ["Home", "Cadastrar", "Separar Pedido"])

if menu == "Home":
    st.subheader("Estoque Disponível")
    if st.session_state.estoque:
        st.table(pd.DataFrame(st.session_state.estoque))
    else: st.write("Estoque vazio.")

elif menu == "Cadastrar":
    st.subheader("Cadastrar Vinho")
    nome = st.text_input("Nome do Vinho")
    if st.button("Salvar"):
        st.session_state.estoque.append({"Nome": nome, "Status": "Ativo"})
        st.success("Vinho cadastrado!")

elif menu == "Separar Pedido":
    st.subheader("📦 Conferência de Pedido (Matriz)")
    
    # 1. Carregar Pedido
    pedido_input = st.text_area("Cole a lista de vinhos pedidos (um por linha):")
    if st.button("Carregar Pedido"):
        st.session_state.lista_pedido = [{"nome": item.strip(), "qtd_esperada": 1} for item in pedido_input.split("\n") if item.strip()]
    
    # 2. Conferência de Caixas
    if "lista_pedido" in st.session_state:
        df_pedido = pd.DataFrame(st.session_state.lista_pedido)
        df_pedido['Qtd_Descida'] = 0 # Nova coluna para você preencher
        
        st.write("### Preencha a quantidade que está descendo:")
        df_editado = st.data_editor(df_pedido, use_container_width=True)
        
        # 3. Gerar Romaneio com Hora de Brasília
        if st.button("Gerar Romaneio Final"):
            hora_br = get_hora_brasilia().strftime('%d/%m/%Y %H:%M')
            texto_romaneio = f"ROMANEIO DE ENVIO\nData: {hora_br}\n\nItens conferidos:\n"
            
            for _, row in df_editado.iterrows():
                texto_romaneio += f"- {row['nome']}: Pedido ({row['qtd_esperada']}) | Descida ({row['Qtd_Descida']})\n"
            
            st.download_button("📥 BAIXAR ROMANEIO .TXT", texto_romaneio, "romaneio_final.txt")
            st.success(f"Romaneio gerado com hora de Brasília: {hora_br}")
