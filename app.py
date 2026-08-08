import json
import os
from datetime import datetime
import pandas as pd
import streamlit as st
import urllib.parse
import cv2
import numpy as np

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
    .wine-card {
        background-color: #FFFFFF; color: #1A1A1A; border-radius: 14px;
        padding: 16px; margin-bottom: 12px; border: 1px solid #E9ECEF;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.03);
    }
    .wine-title { color: #7A1C2E; font-size: 1.1rem; font-weight: 700; margin-bottom: 4px; }
    .wine-text { color: #495057; font-size: 0.85rem; }
    .badge-pallet {
        background-color: #7A1C2E; color: #FFFFFF; padding: 3px 8px;
        border-radius: 6px; font-weight: 600; font-size: 0.75rem; display: inline-block;
    }
    .stButton button {
        background-color: #7A1C2E !important; color: #FFFFFF !important;
        border-radius: 12px !important; font-weight: 600 !important;
        border: none !important; padding: 10px 16px !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Configurações de Arquivos e Constantes
NOME_ARQUIVO = "estoque_galpao_pro.json"
ARQUIVO_USUARIOS = "usuarios_galpao.json"
ARQUIVO_LOGS = "logs_auditoria.json"
SENHA_DEV = "1980"
LISTA_CORREDORES = [f"Corredor {i:02d}" for i in range(1, 26)]
LISTA_PALLETS = [f"Pallet {i:02d}" for i in range(1, 26)]
LISTA_LADOS = ["Direito", "Esquerdo", "Centro / Único"]
OPCOES_CAIXA = ["Caixa com 12 garrafas", "Caixa com 6 garrafas", "Caixa com 3 garrafas", "Garrafa Avulsa (1 un)", "Outra quantidade"]

def carregar_dados():
    if os.path.exists(NOME_ARQUIVO):
        try:
            with open(NOME_ARQUIVO, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return [{"nome": "Château Margaux", "tipo": "Tinto", "safra": "2015", "pallet": "Corredor 01 - Pallet 01", "lado": "Direito", "caixa": "Caixa com 12 garrafas", "volume": "750ml"}]

def salvar_dados(estoque):
    with open(NOME_ARQUIVO, "w", encoding="utf-8") as f: json.dump(estoque, f, ensure_ascii=False, indent=4)

def carregar_usuarios():
    if os.path.exists(ARQUIVO_USUARIOS):
        try:
            with open(ARQUIVO_USUARIOS, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return [{"nome": "Vagner Souza", "cargo": "Administrador", "senha": "1980"}]

def salvar_usuarios(usuarios):
    with open(ARQUIVO_USUARIOS, "w", encoding="utf-8") as f: json.dump(usuarios, f, ensure_ascii=False, indent=4)

def carregar_logs():
    if os.path.exists(ARQUIVO_LOGS):
        try:
            with open(ARQUIVO_LOGS, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return []

def registrar_log(usuario, acao, detalhes):
    logs = carregar_logs()
    logs.insert(0, {"data_hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "usuario": usuario, "acao": acao, "detalhes": detalhes})
    with open(ARQUIVO_LOGS, "w", encoding="utf-8") as f: json.dump(logs, f, ensure_ascii=False, indent=4)

# --- INICIALIZAÇÃO DE SESSÃO ---
if "estoque" not in st.session_state: st.session_state.estoque = carregar_dados()
if "usuarios" not in st.session_state: st.session_state.usuarios = carregar_usuarios()
if "usuario_logado" not in st.session_state: st.session_state.usuario_logado = None
if "menu_atual" not in st.session_state: st.session_state.menu_atual = "🏠 Home"
if "modo_dev" not in st.session_state: st.session_state.modo_dev = False

# --- TELA DE LOGIN / CADASTRO (UNIFICADA) ---
if st.session_state.usuario_logado is None:
    _, col_centro, _ = st.columns([1, 1.2, 1])
    with col_centro:
        with st.container(border=True):
            if os.path.exists("imagem premium.jpeg"):
                _, col_img, _ = st.columns([1, 1, 1])
                with col_img: st.image("imagem premium.jpeg", width=110)
            st.markdown("<h2 style='text-align: center; color: #7A1C2E;'>🍷 Wine Map Pro</h2>", unsafe_allow_html=True)
            
            tab1, tab2, tab3 = st.tabs(["🔑 Entrar", "👤 Cadastrar", "⚙️ Dev"])
            with tab1:
                with st.form("login"):
                    u = st.text_input("Usuário").strip()
                    p = st.text_input("Senha", type="password").strip()
                    if st.form_submit_button("ENTRAR", use_container_width=True):
                        user = next((x for x in st.session_state.usuarios if x['nome'].lower() == u.lower() and x['senha'] == p), None)
                        if user:
                            st.session_state.usuario_logado = user
                            st.rerun()
                        else: st.error("Dados incorretos.")
            with tab2:
                with st.form("cadastro"):
                    n = st.text_input("Nome").strip()
                    c = st.selectbox("Cargo", ["Operador", "Conferente", "Administrador"])
                    s = st.text_input("Senha", type="password").strip()
                    if st.form_submit_button("CADASTRAR", use_container_width=True):
                        st.session_state.usuarios.append({"nome": n, "cargo": c, "senha": s})
                        salvar_usuarios(st.session_state.usuarios)
                        st.success("Conta criada!")
            with tab3:
                with st.form("dev"):
                    sp = st.text_input("Senha Mestra", type="password")
                    if st.form_submit_button("ACESSO DEV", use_container_width=True):
                        if sp == SENHA_DEV:
                            st.session_state.modo_dev = True
                            st.session_state.usuario_logado = {"nome": "Dev", "cargo": "Desenvolvedor"}
                            st.rerun()
    st.stop()

# --- NAVEGAÇÃO E RESTRIÇÕES ---
col1, col2, col3 = st.columns([3, 1, 1])
with col1: st.write(f"Usuário: {st.session_state.usuario_logado['nome']}")
if st.button("🚪 Sair"):
    st.session_state.usuario_logado = None
    st.rerun()

st.markdown("---")

# --- LÓGICA DE TELAS ---
if st.session_state.menu_atual == "🏠 Home":
    st.subheader("Menu Principal")
    c1, c2, c3 = st.columns(3)
    if c1.button("📷 Scanner Real"): st.session_state.menu_atual = "Scanner"
    if c2.button("🍷 Estoque"): st.session_state.menu_atual = "Estoque"
    if st.button("Voltar"): st.session_state.menu_atual = "Home"

elif st.session_state.menu_atual == "Scanner":
    st.subheader("📷 Escanear QR Code Real")
    foto = st.camera_input("Capturar")
    if foto:
        bytes_data = foto.getvalue()
        img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
        val, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
        if val:
            st.success(f"Pallet encontrado: {val}")
            # Filtrar e exibir itens do pallet lido aqui...
        else:
            st.error("Nenhum código encontrado na imagem.")

# (Restante das funções de estoque, cadastro, etc seguem a mesma lógica...)
