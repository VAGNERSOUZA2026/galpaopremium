import json
import os
import shutil
from datetime import datetime
import pandas as pd
import streamlit as st
import urllib.parse
from streamlit_javascript import st_javascript

# Importação para ler arquivos Excel e Word
import openpyxl
from docx import Document

# Importação segura do OpenCV
try:
    import cv2
    import numpy as np
    OPENCV_DISPONIVEL = True
except ImportError:
    OPENCV_DISPONIVEL = False

# Configuração da página
st.set_page_config(
    page_title="Premium Wines - Galpão",
    page_icon="imagem premium.jpeg",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilização CSS
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(135deg, #F8F9FA 0%, #E9ECEF 100%); color: #1A1A1A; font-family: 'Poppins', sans-serif; overscroll-behavior-y: none; }
    [data-testid="stSidebar"] { display: none; }
    label { color: #7A1C2E !important; font-weight: 700 !important; font-size: 0.95rem !important; }
    .wine-card { background-color: #FFFFFF; color: #1A1A1A; border-radius: 14px; padding: 16px; margin-bottom: 12px; border: 1px solid #E9ECEF; box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.03); }
    .wine-title { color: #7A1C2E; font-size: 1.1rem; font-weight: 700; margin-bottom: 4px; }
    .badge-pallet-grande { background-color: #7A1C2E; color: #FFFFFF; padding: 6px 14px; border-radius: 8px; font-weight: 700; font-size: 1rem; display: inline-block; letter-spacing: 0.5px; box-shadow: 0px 2px 6px rgba(122, 28, 46, 0.2); }
    .badge-caixa-grande { background-color: #343A40; color: #FFFFFF; padding: 6px 14px; border-radius: 8px; font-weight: 700; font-size: 1rem; display: inline-block; letter-spacing: 0.5px; box-shadow: 0px 2px 6px rgba(52, 58, 64, 0.2); }
    .stButton button { background-color: #7A1C2E !important; color: #FFFFFF !important; border-radius: 12px !important; font-weight: 600 !important; border: none !important; padding: 10px 16px !important; width: 100%; box-shadow: 0px 4px 10px rgba(122, 28, 46, 0.2); }
    .stButton button:hover { background-color: #922338 !important; color: #FFD700 !important; }
    </style>
""", unsafe_allow_html=True,
)

NOME_ARQUIVO = "estoque_galpao_pro.json"
ARQUIVO_USUARIOS = "usuarios_galpao.json"
ARQUIVO_LOGS = "logs_auditoria.json"
PASTA_BACKUP = "backups_estoque"
SENHA_DEV = "1980"

if not os.path.exists(PASTA_BACKUP): os.makedirs(PASTA_BACKUP)

# --- Funções de Apoio ---
def obter_saudacao():
    hora = datetime.now().hour
    if 0 <= hora < 12: return "Bom dia"
    elif 12 <= hora < 18: return "Boa tarde"
    else: return "Boa noite"

def carregar_dados():
    if os.path.exists(NOME_ARQUIVO):
        try:
            with open(NOME_ARQUIVO, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return [{"nome": "Château Margaux", "tipo": "Tinto", "safra": "2015", "localizacao": "Corredor 01 - Pallet 01", "lado": "Direito", "caixa": "Caixa com 12 garrafas", "foto": ""}]

def salvar_dados(estoque):
    with open(NOME_ARQUIVO, "w", encoding="utf-8") as f: json.dump(estoque, f, ensure_ascii=False, indent=4)

def gerar_qr_code_api(texto):
    return f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={urllib.parse.quote(texto)}"

def buscar_por_voz():
    js_code = """
    window.SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'pt-BR';
    recognition.start();
    return new Promise((resolve) => {
        recognition.onresult = (event) => { resolve(event.results[0][0].transcript); };
        recognition.onerror = (event) => { resolve(""); };
    });
    """
    return st_javascript(js_code)

def extrair_linhas_de_arquivo(arquivo_enviado):
    linhas = []
    extensao = arquivo_enviado.name.split('.')[-1].lower()
    try:
        if extensao in ['xlsx', 'xls']:
            df = pd.read_excel(arquivo_enviado)
            for coluna in df.columns:
                for val in df[coluna].dropna():
                    if str(val).strip(): linhas.append(str(val).strip())
        elif extensao == 'docx':
            doc = Document(arquivo_enviado)
            for p in doc.paragraphs:
                if p.text.strip(): linhas.append(p.text.strip())
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")
    return linhas

# --- Sessão e Estado ---
if "estoque" not in st.session_state: st.session_state.estoque = carregar_dados()
if "usuario_logado" not in st.session_state: st.session_state.usuario_logado = None
if "menu_atual" not in st.session_state: st.session_state.menu_atual = "🏠 Home"

# --- LÓGICA DE NAVEGAÇÃO E SCANNER ---
if st.session_state.menu_atual == "Scanner":
    st.subheader("📷 Escanear QR Code do Local")
    foto = st.camera_input("Capturar Foto")
    if foto and OPENCV_DISPONIVEL:
        img = cv2.imdecode(np.frombuffer(foto.getvalue(), np.uint8), cv2.IMREAD_COLOR)
        val, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
        if val:
            valor_busca = val.strip().lower()
            st.success(f"Local lido: {val}")
            # Filtro robusto
            resultados = [v for v in st.session_state.estoque if valor_busca in v.get('localizacao', '').lower()]
            if resultados:
                st.write(f"### 🍷 Vinhos encontrados neste local:")
                for v in resultados:
                    st.markdown(
                        f"""<div class='wine-card'>
                            <div class='wine-title'>🍷 {v.get('nome', 'Sem nome')} ({v.get('safra', 'N/A')})</div>
                            <p>Local: {v.get('localizacao')}<br>Lado: {v.get('lado')}<br>📦 {v.get('caixa')}</p>
                        </div>""", 
                        unsafe_allow_html=True
                    )
            else:
                st.warning("Nenhum vinho encontrado com este QR Code.")
        else:
            st.error("QR Code não detectado.")

# [Adicione aqui os blocos restantes para Home, Filtros, Cadastrar, etc., conforme seu layout original]

# --- RODAPÉ E GESTÃO DE MENU ---
st.write("---")
if st.button("⬅️ Voltar ao Início"):
    st.session_state.menu_atual = "🏠 Home"
    st.rerun()
    
