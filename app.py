import json
import os
from datetime import datetime
import pandas as pd
import streamlit as st
import urllib.parse

# Importação condicional do OpenCV
try:
    import cv2
    import numpy as np
    OPENCV_DISPONIVEL = True
except ImportError:
    OPENCV_DISPONIVEL = False

# Configuração da página
st.set_page_config(
    page_title="Premium Wines - Wine Map Pro",
    page_icon="imagem premium.jpeg",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilização CSS
st.markdown(
    """
    <style>
    .stApp { background-color: #F8F9FA; color: #1A1A1A; font-family: 'Poppins', sans-serif; }
    [data-testid="stSidebar"] { display: none; }
    .wine-card { background-color: #FFFFFF; color: #1A1A1A; border-radius: 14px; padding: 16px; margin-bottom: 12px; border: 1px solid #E9ECEF; box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.03); }
    .wine-title { color: #7A1C2E; font-size: 1.1rem; font-weight: 700; margin-bottom: 4px; }
    .badge-pallet { background-color: #7A1C2E; color: #FFFFFF; padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 0.75rem; display: inline-block; }
    .stButton button { background-color: #7A1C2E !important; color: #FFFFFF !important; border-radius: 12px !important; font-weight: 600 !important; border: none !important; padding: 10px 16px !important; }
    </style>
""", unsafe_allow_html=True,
)

# Funções auxiliares
def obter_saudacao():
    hora = datetime.now().hour
    if 5 <= hora < 12: return "Bom dia"
    elif 12 <= hora < 18: return "Boa tarde"
    else: return "Boa noite"

def carregar_json(arquivo, padrao):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return padrao

def salvar_json(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f: json.dump(dados, f, ensure_ascii=False, indent=4)

# Inicialização
if "estoque" not in st.session_state: st.session_state.estoque = carregar_json("estoque_galpao_pro.json", [])
if "usuarios" not in st.session_state: st.session_state.usuarios = carregar_json("usuarios_galpao.json", [{"nome": "Vagner Souza", "cargo": "Administrador", "senha": "1980"}])
if "usuario_logado" not in st.session_state: st.session_state.usuario_logado = None
if "menu_atual" not in st.session_state: st.session_state.menu_atual = "🏠 Home"

# Login
if st.session_state.usuario_logado is None:
    _, col_centro, _ = st.columns([1, 1.2, 1])
    with col_centro:
        with st.container(border=True):
            if os.path.exists("imagem premium.jpeg"):
                _, col_img, _ = st.columns([1, 1, 1])
                with col_img: st.image("imagem premium.jpeg", width=110)
            st.markdown("<h2 style='text-align: center; color: #7A1C2E;'>🍷 Wine Map Pro</h2>", unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["🔑 Entrar", "⚙️ Dev"])
            with tab1:
                u = st.text_input("Usuário").strip()
                p = st.text_input("Senha", type="password").strip()
                if st.button("ENTRAR", use_container_width=True):
                    user = next((x for x in st.session_state.usuarios if x['nome'].lower() == u.lower() and x['senha'] == p), None)
                    if user: st.session_state.usuario_logado = user; st.rerun()
                    else: st.error("Dados incorretos.")
            with tab2:
                sp = st.text_input("Senha Mestra", type="password")
                if st.button("ACESSAR DEV", use_container_width=True):
                    if sp == "1980": st.session_state.usuario_logado = {"nome": "Dev", "cargo": "Desenvolvedor"}; st.rerun()
    st.stop()

# Navegação
st.markdown(f"**🍷 Premium Wines** | Usuário: {st.session_state.usuario_logado['nome']}")
if st.button("🚪 Sair"): st.session_state.usuario_logado = None; st.rerun()

if st.session_state.menu_atual == "🏠 Home":
    if os.path.exists("imagem premium.jpeg"):
        _, c_img, _ = st.columns([1, 1, 1])
        with c_img: st.image("imagem premium.jpeg", width=220)
    
    st.markdown(f"<h1 style='text-align: center; color: #7A1C2E;'>{obter_saudacao()}, {st.session_state.usuario_logado['nome']}! 👋</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    if col1.button("📷 Escanear QR", use_container_width=True): st.session_state.menu_atual = "Scanner"
    if col2.button("🍷 Estoque", use_container_width=True): st.session_state.menu_atual = "Estoque"
    if col3.button("➕ Cadastrar", use_container_width=True): st.session_state.menu_atual = "Cadastrar"

elif st.session_state.menu_atual == "Scanner":
    foto = st.camera_input("Capturar Pallet")
    if foto and OPENCV_DISPONIVEL:
        img = cv2.imdecode(np.frombuffer(foto.getvalue(), np.uint8), cv2.IMREAD_COLOR)
        val = cv2.QRCodeDetector().detectAndDecode(img)[0]
        if val: st.success(f"Pallet: {val}")
        else: st.error("Código não lido.")

elif st.session_state.menu_atual == "Estoque":
    st.write(pd.DataFrame(st.session_state.estoque))

elif st.session_state.menu_atual == "Cadastrar":
    with st.form("c"):
        nome = st.text_input("Nome")
        if st.form_submit_button("Salvar"):
            st.session_state.estoque.append({"nome": nome})
            salvar_json("estoque_galpao_pro.json", st.session_state.estoque)
            st.success("Salvo!")
