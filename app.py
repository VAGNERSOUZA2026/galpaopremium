import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd
import urllib.parse

# 1. Configuração da página (DEVE SER A PRIMEIRA CHAMADA)
st.set_page_config(
    page_title="Premium Wines - Galpão",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Estilização CSS Personalizada
st.markdown(
    """
    <style>
    .stApp {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        font-family: 'Poppins', sans-serif;
    }
    #MainMenu, header, footer {visibility: hidden;}
    [data-testid="stSidebar"] { display: none; }

    /* Botões Principais no Tom Vinho */
    div.stButton > button {
        background-color: #7A1C2E !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 12px 20px !important;
        width: 100%;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.15);
    }
    div.stButton > button:hover {
        background-color: #581825 !important;
        color: #FFD700 !important;
    }
    </style>
    """, unsafe_allow_html=True
)

NOME_ARQUIVO = "estoque_galpao_pro.json"
ARQUIVO_USUARIOS = "usuarios_galpao.json"
ARQUIVO_LOGS = "logs_auditoria.json"

if "estoque" not in st.session_state:
    st.session_state.estoque = []
if "usuarios" not in st.session_state:
    st.session_state.usuarios = [{"nome": "Dev", "cargo": "Desenvolvedor", "senha": "1980"}]
if "menu_atual" not in st.session_state:
    st.session_state.menu_atual = "🏠 Home"

query_params = st.query_params
user_url = query_params.get("user", None)
cargo_url = query_params.get("cargo", "Operador")

if "usuario_logado" not in st.session_state or st.session_state.usuario_logado is None:
    if user_url:
        st.session_state.usuario_logado = {"nome": user_url, "cargo": cargo_url}
    else:
        st.session_state.usuario_logado = None

# --- TELA DE LOGIN ---
if st.session_state.usuario_logado is None:
    _, col_centro, _ = st.columns([1, 1.2, 1])
    with col_centro:
        st.markdown("### 🍷 PREMIUM WINES - Login")
        with st.form("login_form"):
            u = st.text_input("Usuário").strip()
            p = st.text_input("Senha", type="password").strip()
            if st.form_submit_button("ENTRAR", use_container_width=True):
                user = next((x for x in st.session_state.usuarios if x['nome'].lower() == u.lower() and x['senha'] == p), None)
                if user:
                    st.session_state.usuario_logado = user
                    st.query_params["user"] = user['nome']
                    st.query_params["cargo"] = user['cargo']
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
    st.stop()

# --- TOPO DO APLICATIVO ---
c_t1, c_t2 = st.columns([4, 1])
with c_t1: 
    st.markdown(f"🍷 **PREMIUM WINES GALPÃO** | Usuário: **{st.session_state.usuario_logado['nome']}**")
with c_t2:
    if st.button("🚪 Sair", use_container_width=True): 
        st.session_state.usuario_logado = None
        st.query_params.clear()
        st.session_state.menu_atual = "🏠 Home"
        st.rerun()

st.markdown("---")

if st.session_state.menu_atual != "🏠 Home":
    if st.button("⬅️ Voltar para o Início"):
        st.session_state.menu_atual = "🏠 Home"
        st.rerun()
    st.write("")

# --- PAINEL HOME (COM LOGO E SAUDAÇÃO PERFEITAMENTE CENTRALIZADAS) ---
if st.session_state.menu_atual == "🏠 Home":
    
    # Usando colunas para centralizar o bloco da imagem e saudação
    _, col_logo, _ = st.columns([2, 1.2, 2])
    with col_logo:
        if os.path.exists("logo_vinho.png"):
            st.image("logo_vinho.png", width=180)
        
        hora = datetime.now().hour
        saudacao = "Bom dia" if 0 <= hora < 12 else ("Boa tarde" if 12 <= hora < 18 else "Boa noite")
        st.markdown(f"<p style='text-align: center; margin-bottom: 0;'>{saudacao},</p>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align: center; color: #7A1C2E; margin-top: 0;'>{st.session_state.usuario_logado['nome']}! </h2>", unsafe_allow_html=True)
    
    st.markdown("<p style='text-align: center; color: #666; margin-bottom: 30px;'>Escolha abaixo a opção desejada para gerenciar o galpão:</p>", unsafe_allow_html=True)
    
    # Botões do Menu Principal
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🔍 Buscar / Filtros\n\nMúltiplos critérios", use_container_width=True):
            st.session_state.menu_atual = "Filtros"
            st.rerun()
    with c2:
        if st.button("🗺️ Mapa de Separação\n\nEnviar arquivo ou lista", use_container_width=True):
            st.session_state.menu_atual = "MapaSeparacao"
            st.rerun()
    with c3:
        if st.button("🍷 Estoque Completo\n\nVer todos os vinhos", use_container_width=True):
            st.session_state.menu_atual = "Estoque"
            st.rerun()

    st.write("")
    c4, c5, c6 = st.columns(3)
    with c4:
        if st.button("➕ Cadastrar Vinho\n\nAdicionar ao sistema", use_container_width=True):
            st.session_state.menu_atual = "Cadastrar"
            st.rerun()
    with c5:
        if st.button("📱 Gerar QR Code\n\nEtiquetas de locais", use_container_width=True):
            st.session_state.menu_atual = "GerarQR"
            st.rerun()
    with c6:
        if st.button("📋 Histórico\n\nLogs de Auditoria", use_container_width=True):
            st.session_state.menu_atual = "Historico"
            st.rerun()

# Demais telas do sistema
elif st.session_state.menu_atual == "Filtros":
    st.markdown("### 🔍 Buscar Vinho")
    termo = st.text_input("Digite o nome do vinho...").strip()
    if termo:
        st.info("Resultados da busca...")

elif st.session_state.menu_atual == "Cadastrar":
    st.markdown("### ➕ Novo Cadastro de Vinho")
    with st.form("form_cad"):
        st.text_input("Nome do Vinho")
        st.form_submit_button("Salvar")

elif st.session_state.menu_atual == "Estoque":
    st.markdown("### 🍷 Estoque Completo")
    st.write("Lista de vinhos cadastrados.")

elif st.session_state.menu_atual == "MapaSeparacao":
    st.markdown("### 🗺️ Mapa de Separação")
    st.text_area("Cole sua lista:")

elif st.session_state.menu_atual == "GerarQR":
    st.markdown("### 📱 Gerar QR Code")

elif st.session_state.menu_atual == "Historico":
    st.markdown("### 📋 Histórico de Logs")
