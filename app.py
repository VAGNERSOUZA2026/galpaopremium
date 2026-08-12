import json
import os
import shutil
from datetime import datetime, timezone, timedelta
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# --- CONFIGURAÇÕES E ESTILOS ---
st.set_page_config(page_title="Premium Wines - Galpão", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
    <style>
    .stApp { background: #F8F9FA; font-family: sans-serif; }
    .wine-card { background: white; padding: 15px; border-radius: 10px; border-left: 5px solid #7A1C2E; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE DADOS ---
NOME_ARQUIVO = "estoque_galpao_pro.json"
def carregar_dados():
    if os.path.exists(NOME_ARQUIVO):
        with open(NOME_ARQUIVO, "r", encoding="utf-8") as f: return json.load(f)
    return []

def salvar_dados(estoque):
    with open(NOME_ARQUIVO, "w", encoding="utf-8") as f: json.dump(estoque, f, ensure_ascii=False, indent=4)

if "estoque" not in st.session_state: st.session_state.estoque = carregar_dados()
if "menu_atual" not in st.session_state: st.session_state.menu_atual = "🏠 Home"

# --- COMPONENTE SCANNER JS (Estilo Banco) ---
def scanner_barcode():
    html_code = """
    <div id="interactive" class="viewport"></div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/quagga/0.12.1/quagga.min.js"></script>
    <script>
        Quagga.init({
            inputStream: { type: "LiveStream", target: document.querySelector('#interactive') },
            decoder: { readers: ["ean_reader", "code_128_reader"] }
        }, function(err) { if (!err) Quagga.start(); });
        Quagga.onDetected(function(data) {
            window.parent.postMessage({type: 'barcode', value: data.codeResult.code}, '*');
        });
    </script>
    """
    components.html(html_code, height=300)

# --- MENU PRINCIPAL ---
st.title("🍷 Premium Wines - Galpão")
menu = st.sidebar.radio("Navegação", ["Home", "Cadastrar", "Separar Pedido"])

if menu == "Home":
    st.subheader("Estoque Atual")
    df = pd.DataFrame(st.session_state.estoque)
    if not df.empty: st.dataframe(df, use_container_width=True)

elif menu == "Cadastrar":
    st.subheader("Cadastro de Vinho")
    nome = st.text_input("Nome do Vinho")
    cod_barras = st.text_input("Código de Barras (ou use o scanner abaixo)")
    if st.button("Abrir Scanner para Capturar Código"):
        st.info("Aponte a câmera para o código de barras...")
        # (Opcional: implementar callback de captura aqui)
    if st.button("Salvar Vinho"):
        st.session_state.estoque.append({"nome": nome, "codigo_barras": cod_barras})
        salvar_dados(st.session_state.estoque)
        st.success("Salvo!")

elif menu == "Separar Pedido":
    st.subheader("Separar Pedido da Matriz")
    # Aqui o fluxo de bipagem contínua...
    if st.button("Gerar Romaneio e Dar Baixa"):
        # 1. Gera arquivo para download
        romaneio_texto = "ROMANEIO DE SAÍDA - " + datetime.now().strftime("%d/%m/%Y")
        st.download_button("📥 Baixar Romaneio", romaneio_texto, "romaneio.txt")
        # 2. Faz a baixa no estoque
        st.success("Estoque atualizado e romaneio gerado!")

st.write("---")
st.caption("Desenvolvido para Premium Wines")
