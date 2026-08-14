import streamlit as st
import pandas as pd
import json
import os
import random
from datetime import datetime, timedelta, timezone

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DE FUSO HORÁRIO E DATAS
# -----------------------------------------------------------------------------
fuso_br = timezone(timedelta(hours=-3))
hoje_dt = datetime.now(fuso_br)
data_hoje_id = hoje_dt.strftime("%Y-%m-%d")

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA (TEMA ESCURO)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Premium Wines | Galpão",
    page_icon="🍷",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# ESTILIZAÇÃO CSS CUSTOMIZADA
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Montserrat', sans-serif; 
        color: #F3F4F6;
    }

    .stApp {
        background-color: #111827;
        color: #F3F4F6;
    }

    .stTextInput label, .stSelectbox label, .stNumberInput label, .stFileUploader label, p, span, label {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }

    .app-header {
        background: #1F2937;
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 20px;
        border: 1px solid #374151;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.3);
    }
    .app-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #FFFFFF;
        margin: 0;
    }
    .app-subtitle {
        font-size: 0.85rem;
        color: #D1D5DB;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .card-team {
        background: #1F2937;
        border: 1px solid #374151;
        border-top: 4px solid #881337;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 15px;
        color: #FFFFFF;
    }

    div.stButton > button:first-child {
        background-color: #881337 !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        border: 1px solid #9F1239 !important;
        padding: 15px 20px !important;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.2);
        width: 100%;
    }
    div.stButton > button:first-child:hover {
        background-color: #9F1239 !important;
        border-color: #BE123C !important;
    }

    .stTextInput input, .stSelectbox select, .stNumberInput input {
        background-color: #374151 !important;
        color: #FFFFFF !important;
        border: 1px solid #4B5563 !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# ARQUIVOS JSON E PERSISTÊNCIA INTELIGENTE
# -----------------------------------------------------------------------------
DATA_FILE = "vinhas.json"
PEDIDOS_FILE = "pedidos.json"
ADMINS_FILE = "administradores.json"
AVISOS_FILE = "avisos.json"

def carregar_dados(filename, default):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def salvar_dados(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

# -----------------------------------------------------------------------------
# INICIALIZAÇÃO DO SESSION STATE
# -----------------------------------------------------------------------------
if "produtos" not in st.session_state:
    st.session_state.produtos = carregar_dados(DATA_FILE, [
        {"nome": "Campana Merlot", "corredor": "Corredor 01", "pallet": "Pallet Item 01"},
        {"nome": "Falernia Carmenere", "corredor": "Corredor 03", "pallet": "Pallet Item 03"}
    ])
if "pedidos" not in st.session_state:
    st.session_state.pedidos = carregar_dados(PEDIDOS_FILE, [])
if "administradores" not in st.session_state:
    st.session_state.administradores = carregar_dados(ADMINS_FILE, [{"nome": "Desenvolvedor", "login": "admin", "senha": "1980"}])
if "avisos" not in st.session_state:
    st.session_state.avisos = carregar_dados(AVISOS_FILE, {"aviso": "Bem-vindo ao sistema de galpão Premium Wines."})

if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "login"
if "menu_atual" not in st.session_state:
    st.session_state.menu_atual = "Dashboard"
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None
if "perfil_logado" not in st.session_state:
    st.session_state.perfil_logado = None

SENHA_MESTRE_DEV = "1980"

# -----------------------------------------------------------------------------
# TELA DE LOGIN
# -----------------------------------------------------------------------------
if st.session_state.pagina_atual == "login":
    st.markdown("""
    <div class='app-header' style='text-align: center;'>
        <div class='app-subtitle'>premium wines — galpão</div>
        <div class='app-title'>🍷 Gestão de Roteiro e Pedidos</div>
    </div>
    """, unsafe_allow_html=True)

    tab_entrar, tab_dev = st.tabs(["🔑 Entrar", "⚙️ Desenvolvedor"])

    with tab_entrar:
        st.subheader("Acesso ao Sistema")
        with st.form("form_login"):
            l_user = st.text_input("Usuário")
            l_pass = st.text_input("Senha", type="password")
            if st.form_submit_button("ENTRAR"):
                admin_encontrado = next((adm for adm in st.session_state.administradores if adm.get("login") == l_user and adm.get("senha") == l_pass), None)
                if admin_encontrado or (l_user == "admin" and l_pass == SENHA_MESTRE_DEV):
                    st.session_state.usuario_logado = l_user
                    st.session_state.perfil_logado = "Administrador"
                    st.session_state.pagina_atual = "dashboard"
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos!")

    with tab_dev:
        st.subheader("Acesso Rápido Desenvolvedor")
        with st.form("form_dev"):
            d_pass = st.text_input("Senha Mestre", type="password")
            if st.form_submit_button("ENTRAR COMO DEV"):
                if d_pass == SENHA_MESTRE_DEV:
                    st.session_state.usuario_logado = "Desenvolvedor"
                    st.session_state.perfil_logado = "Desenvolvedor"
                    st.session_state.pagina_atual = "dashboard"
                    st.rerun()
                else:
                    st.error("Senha incorreta!")

# -----------------------------------------------------------------------------
# PAINEL PRINCIPAL
# -----------------------------------------------------------------------------
else:
    st.markdown(f"""
    <div class='app-header'>
        <div class='app-subtitle'>Painel de Operações — Usuário: <b>{st.session_state.usuario_logado}</b></div>
        <div class='app-title'>Controle de Pedidos e Roteiro</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚪 Sair da Conta"):
        st.session_state.usuario_logado = None
        st.session_state.perfil_logado = None
        st.session_state.pagina_atual = "login"
        st.rerun()

    st.markdown("---")
    st.subheader("📦 Pedidos Recentes e Roteiro Antierros")

    # Exemplo visual dos itens conferidos com verificação de cadastro corrigida
    st.write("### Roteiro e Bipe de Caixas (Antierros)")
    
    itens_exemplo = [
        {"vinho": "Campana Merlot", "qtd": 5},
        {"vinho": "Falernia Carmenere", "qtd": 5},
        {"vinho": "La Roche", "qtd": 5},
        {"vinho": "Quereu Cabernet", "qtd": 1}
    ]

    for item in itens_exemplo:
        # Verifica se o vinho existe na base de dados cadastrada
        match_prod = next((p for p in st.session_state.produtos if p["nome"].lower() in item["vinho"].lower()), None)
        if match_prod:
            detalhe_corredor = f"📍 {match_prod['corredor']} - {match_prod['pallet']}"
        else:
            detalhe_corredor = "🛠️ Não cadastrado (Verifique o nome exato na base)"

        st.markdown(f"""
        <div class='card-team'>
            ⌛ <b>{item['vinho']}</b> | Qtd: {item['qtd']} | <code>{detalhe_corredor}</code>
        </div>
        """, unsafe_allow_html=True)
