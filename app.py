import json
import os
from datetime import datetime
import pandas as pd
import streamlit as st
import urllib.parse

# Importação segura do OpenCV
try:
    import cv2
    import numpy as np
    OPENCV_DISPONIVEL = True
except ImportError:
    OPENCV_DISPONIVEL = False

st.set_page_config(page_title="Premium Wines - Wine Map Pro", layout="wide", initial_sidebar_state="collapsed")

# CSS para garantir centralização total
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .logo-container { display: flex; justify-content: center; margin-bottom: 20px; }
    .center-text { text-align: center; }
    .stButton button { background-color: #7A1C2E !important; color: white !important; width: 100%; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES E DADOS ---
ARQUIVO_ESTOQUE = "estoque_galpao_pro.json"
ARQUIVO_USUARIOS = "usuarios_galpao.json"

def obter_saudacao():
    hora = datetime.now().hour
    if 5 <= hora < 12: return "Bom dia"
    elif 12 <= hora < 18: return "Boa tarde"
    else: return "Boa noite"

# Sessão
if "estoque" not in st.session_state: st.session_state.estoque = []
if "usuarios" not in st.session_state: st.session_state.usuarios = [{"nome": "Vagner Souza", "cargo": "Administrador", "senha": "1980"}]
if "usuario_logado" not in st.session_state: st.session_state.usuario_logado = None
if "menu_atual" not in st.session_state: st.session_state.menu_atual = "🏠 Home"

# --- TELA DE LOGIN ---
if st.session_state.usuario_logado is None:
    _, col_centro, _ = st.columns([1, 1.5, 1])
    with col_centro:
        # Logo centralizada via div HTML
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        if os.path.exists("imagem premium.jpeg"):
            st.image("imagem premium.jpeg", width=180)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<h2 class='center-text' style='color: #7A1C2E;'>🍷 Wine Map Pro</h2>", unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["🔑 Entrar", "👤 Cadastro", "⚙️ Dev"])
        
        with tab1:
            u = st.text_input("Usuário")
            p = st.text_input("Senha", type="password")
            if st.button("ENTRAR"):
                user = next((x for x in st.session_state.usuarios if x['nome'] == u and x['senha'] == p), None)
                if user: st.session_state.usuario_logado = user; st.rerun()
                else: st.error("Dados incorretos.")
        
        with tab2:
            n = st.text_input("Nome")
            s = st.text_input("Senha Nova", type="password")
            if st.button("CRIAR CONTA"):
                st.session_state.usuarios.append({"nome": n, "cargo": "Operador", "senha": s})
                st.success("Conta criada! Pode entrar.")
        
        with tab3:
            sp = st.text_input("Senha Mestra", type="password")
            if st.button("ACESSAR MODO GERENCIAR"):
                if sp == "1980":
                    st.session_state.usuario_logado = {"nome": "Dev", "cargo": "Admin"}
                    st.rerun()
                else: st.error("Senha Dev incorreta")
    st.stop()

# --- HOME LOGADO ---
# Cabeçalho
c_top1, c_top2 = st.columns([4, 1])
c_top1.write(f"Olá, **{st.session_state.usuario_logado['nome']}**")
if c_top2.button("🚪 Sair"): st.session_state.usuario_logado = None; st.rerun()

# Logo na Home
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
if os.path.exists("imagem premium.jpeg"): st.image("imagem premium.jpeg", width=220)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown(f"<h1 class='center-text' style='color: #7A1C2E;'>{obter_saudacao()}!</h1>", unsafe_allow_html=True)

# Botões do Menu
cols = st.columns(3)
if cols[0].button("🔍 Buscar/Filtros"): st.session_state.menu_atual = "Filtros"
if cols[1].button("📷 Escanear Pallet"): st.session_state.menu_atual = "Scanner"
if cols[2].button("🍷 Estoque Completo"): st.session_state.menu_atual = "Estoque"

cols2 = st.columns(3)
if cols2[0].button("➕ Cadastrar Vinho"): st.session_state.menu_atual = "Cadastrar"
if cols2[1].button("📱 Gerar QR Code"): st.session_state.menu_atual = "GerarQR"
if cols2[2].button("📋 Histórico"): st.session_state.menu_atual = "Historico"
