import streamlit as st
import json
import os
import shutil
from datetime import datetime
import pandas as pd
import urllib.parse
from streamlit_javascript import st_javascript

import openpyxl
from docx import Document

try:
    import cv2
    import numpy as np
    OPENCV_DISPONIVEL = True
except ImportError:
    OPENCV_DISPONIVEL = False

# 1. Configuração da página (DEVE SER A PRIMEIRA CHAMADA)
st.set_page_config(
    page_title="Wine Map Pro",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Estilização CSS Profissional (Dark Mode Exato Inspirado no Wine Map Pro)
st.markdown(
    """
    <style>
    /* Fundo Geral da Aplicação */
    .stApp {
        background-color: #121212 !important;
        color: #FFFFFF !important;
        font-family: 'Poppins', sans-serif;
    }

    /* Ocultar elementos padrão do Streamlit desnecessários para mobile/app */
    #MainMenu, header, footer {visibility: hidden;}
    [data-testid="stSidebar"] { display: none; }

    /* Cartões Modernos Estilo Wine Map Pro (#1E1E1E com bordas sutis) */
    .wine-card {
        background-color: #1E1E1E !important;
        border: 1px solid #2C2C2C !important;
        border-radius: 16px !important;
        padding: 20px !important;
        margin-bottom: 16px !important;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.4) !important;
    }

    .wine-card-metric {
        background-color: #1E1E1E !important;
        border: 1px solid #2C2C2C !important;
        border-radius: 16px !important;
        padding: 16px !important;
        text-align: center;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.3) !important;
    }

    /* Botões Principais (Tom Vinho #581825 com texto branco) */
    div.stButton > button {
        background-color: #581825 !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 12px 20px !important;
        width: 100%;
        box-shadow: 0px 4px 12px rgba(88, 24, 37, 0.4);
        transition: 0.2s ease-in-out;
    }
    div.stButton > button:hover {
        background-color: #7A1C2E !important;
        border: 1px solid #C9A227 !important;
        color: #FFD700 !important;
    }

    /* Títulos e Textos */
    h1, h2, h3, h4, p, span, label { color: #FFFFFF !important; }
    
    /* Inputs, Selects e TextAreas Estilizados */
    .stTextInput > div > div > input, .stSelectbox > div > div, .stTextArea textarea {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
        border: 1px solid #333333 !important;
        border-radius: 10px !important;
        padding: 10px !important;
    }
    
    /* Abas estilizadas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #121212;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1E1E1E;
        border-radius: 8px;
        color: #AAAAAA;
        border: 1px solid #333333;
    }
    .stTabs [aria-selected="true"] {
        background-color: #581825 !important;
        color: #FFFFFF !important;
        border: 1px solid #C9A227 !important;
    }
    </style>
    """, unsafe_allow_html=True
)

NOME_ARQUIVO = "estoque_galpao_pro.json"
ARQUIVO_USUARIOS = "usuarios_galpao.json"
ARQUIVO_LOGS = "logs_auditoria.json"
PASTA_BACKUP = "backups_estoque"
SENHA_DEV = "1980"

if not os.path.exists(PASTA_BACKUP):
    os.makedirs(PASTA_BACKUP)

LISTA_CORREDORES = [f"Corredor {i:02d}" for i in range(1, 26)]
LISTA_LOCAIS_TIPO = ["Pallet", "Prateleira"]
LISTA_NUMEROS_LOCAL = [f"Item {i:02d}" for i in range(1, 26)]
LISTA_LADOS = ["Direito", "Esquerdo", "Centro / Único"]
OPCOES_CAIXA = ["Caixa com 12 garrafas", "Caixa com 6 garrafas", "Caixa com 3 garrafas", "Caixa com 2 garrafas", "Garrafa Avulsa (1 un)", "Outra quantidade"]

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

def gerar_qr_code_api(texto):
    return f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={urllib.parse.quote(texto)}"

# Estados da Sessão
if "estoque" not in st.session_state: st.session_state.estoque = carregar_dados()
if "usuarios" not in st.session_state: st.session_state.usuarios = carregar_usuarios()
if "menu_atual" not in st.session_state: st.session_state.menu_atual = "🏠 Home"
if "vinho_para_duplicar" not in st.session_state: st.session_state.vinho_para_duplicar = None

# Persistência via URL (mantém logado ao atualizar a página)
query_params = st.query_params
user_url = query_params.get("user", None)
cargo_url = query_params.get("cargo", "Operador")

if "usuario_logado" not in st.session_state or st.session_state.usuario_logado is None:
    if user_url:
        st.session_state.usuario_logado = {"nome": user_url, "cargo": cargo_url}
    else:
        st.session_state.usuario_logado = None

# --- TELA DE LOGIN (Estilo Pro da Imagem) ---
if st.session_state.usuario_logado is None:
    st.write("")
    _, col_centro, _ = st.columns([1, 1.2, 1])
    with col_centro:
        st.markdown(
            """
            <div class="wine-card" style="text-align: center;">
                <h1 style="color: #C9A227; font-size: 1.8rem; font-weight: 800; margin-bottom: 5px;">WINE MAP PRO</h1>
                <p style="color: #AAAAAA; font-size: 0.95rem; margin-top: 0;">Acesse sua conta para continuar</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        tab_login, tab_cadastro = st.tabs(["🔑 Entrar", "👤 Criar Conta"])
        
        with tab_login:
            with st.form("login_form"):
                u = st.text_input("Usuário ou e-mail").strip()
                p = st.text_input("Senha", type="password").strip()
                st.write("")
                if st.form_submit_button("ENTRAR", use_container_width=True):
                    user = next((x for x in st.session_state.usuarios if x['nome'].lower() == u.lower() and x['senha'] == p), None)
                    if user:
                        st.session_state.usuario_logado = user
                        st.query_params["user"] = user['nome']
                        st.query_params["cargo"] = user['cargo']
                        st.rerun()
                    else: st.error("Usuário ou senha incorretos.")
        
        with tab_cadastro:
            with st.form("cadastro_form"):
                n = st.text_input("Nome do usuário").strip()
                s = st.text_input("Senha", type="password").strip()
                st.write("")
                if st.form_submit_button("CADASTRAR E ENTRAR", use_container_width=True):
                    if n and s:
                        if any(x['nome'].lower() == n.lower() for x in st.session_state.usuarios):
                            st.error("Este usuário já existe.")
                        else:
                            novo = {"nome": n, "cargo": "Operador", "senha": s}
                            st.session_state.usuarios.append(novo)
                            salvar_usuarios(st.session_state.usuarios)
                            registrar_log(n, "Criação de Conta", "Novo cadastro realizado")
                            st.session_state.usuario_logado = novo
                            st.query_params["user"] = novo['nome']
                            st.query_params["cargo"] = novo['cargo']
                            st.rerun()
                    else: st.error("Preencha todos os campos.")
    st.stop()

# --- TOPO DO APLICATIVO LOGADO ---
c_t1, c_t2 = st.columns([4, 1])
with c_t1: 
    st.markdown(f"<span style='color: #C9A227; font-weight: bold;'>🍷 WINE MAP PRO</span> | Olá, <b>{st.session_state.usuario_logado['nome']}</b>", unsafe_allow_html=True)
with c_t2:
    if st.button("🚪 Sair", use_container_width=True): 
        st.session_state.usuario_logado = None
        st.query_params.clear()
        st.session_state.menu_atual = "🏠 Home"
        st.rerun()

st.markdown("---")

# Se não estiver na Home, mostra botão de voltar
if st.session_state.menu_atual != "🏠 Home":
    if st.button("⬅️ Voltar para o Dashboard (Home)"):
        st.session_state.menu_atual = "🏠 Home"
        st.rerun()
    st.write("")

# --- PAINEL HOME / DASHBOARD (Igual ao Print 3 da imagem) ---
if st.session_state.menu_atual == "🏠 Home":
    saudacao = obter_saudacao()
    total_vinhos = len(st.session_state.estoque)
    
    st.markdown(
        f"""
        <div class="wine-card">
            <h3 style="color: #FFFFFF; font-size: 1.4rem; margin-bottom: 0;">{saudacao}, <span style="color: #C9A227;">{st.session_state.usuario_logado['nome']}! 👋</span></h3>
            <p style="color: #AAAAAA; font-size: 0.9rem; margin-top: 5px;">Bem-vindo ao WineMap Pro</p>
            
            <div style="display: flex; gap: 12px; margin-top: 15px;">
                <div style="background-color: #252525; padding: 12px 16px; border-radius: 12px; flex: 1; border: 1px solid #333;">
                    <span style="color: #C9A227; font-size: 1.2rem; font-weight: bold;">{total_vinhos}</span><br>
                    <span style="color: #888; font-size: 0.8rem;">Vinhos cadastrados</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("#### Ações rápidas")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("➕ Novo Cadastro", use_container_width=True):
            st.session_state.vinho_para_duplicar = None
            st.session_state.menu_atual = "Cadastrar"
            st.rerun()
    with c2:
        if st.button("🔍 Buscar Vinho", use_container_width=True):
            st.session_state.menu_atual = "Filtros"
            st.rerun()
    with c3:
        if st.button("🍷 Estoque", use_container_width=True):
            st.session_state.menu_atual = "Estoque"
            st.rerun()

    st.write("")
    c4, c5 = st.columns(2)
    with c4:
        if st.button("🗺️ Mapa de Separação", use_container_width=True):
            st.session_state.menu_atual = "MapaSeparacao"
            st.rerun()
    with c5:
        if st.button("📱 Gerar QR Code", use_container_width=True):
            st.session_state.menu_atual = "GerarQR"
            st.rerun()

    if st.session_state.usuario_logado['cargo'] in ["Administrador", "Desenvolvedor"] or st.session_state.usuario_logado['nome'] == "Dev":
        st.write("")
        if st.button("⚙️ Gerenciar Contas e Senhas", use_container_width=True):
            st.session_state.menu_atual = "GerenciarUsuarios"
            st.rerun()

# --- TELA DE BUSCA (Print 4) ---
elif st.session_state.menu_atual == "Filtros":
    st.markdown("### 🔍 Buscar Vinho")
    termo = st.text_input("Pesquisar por nome, vinícola...", placeholder="Digite o nome do vinho...").strip()
    
    if termo:
        res = [v for v in st.session_state.estoque if termo.lower() in v.get("nome", "").lower()]
        st.markdown(f"<p style='color: #888;'>Resultados ({len(res)})</p>", unsafe_allow_html=True)
        if res:
            for v in res:
                st.markdown(
                    f"""
                    <div class="wine-card">
                        <h4 style="color: #C9A227; margin: 0;">🍷 {v.get('nome')}</h4>
                        <p style="margin: 5px 0; color: #DDD;">{v.get('tipo')} | Safra {v.get('safra')}</p>
                        <small style="color: #888;">📍 Localização: {v.get('localizacao')} (Lado {v.get('lado')})</small><br>
                        <small style="color: #888;">📦 {v.get('caixa')}</small>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
        else:
            st.info("Nenhum vinho encontrado.")
    else:
        st.info("Digite algo na barra acima para iniciar a busca.")

# --- TELA DE CADASTRO (Print 5) ---
elif st.session_state.menu_atual == "Cadastrar":
    st.markdown("### ➕ Novo Cadastro")
    dados_padrao = st.session_state.vinho_para_duplicar if st.session_state.vinho_para_duplicar else {}
    
    with st.form("cad_form", clear_on_submit=True):
        nome = st.text_input("Nome do vinho", value=dados_padrao.get("nome", ""))
        tipo = st.text_input("Tipo (ex: Tinto, Branco)", value=dados_padrao.get("tipo", ""))
        safra = st.text_input("Safra", value=dados_padrao.get("safra", "2024"))
        
        c1, c2, c3 = st.columns(3)
        with c1: cor = st.selectbox("Corredor", LISTA_CORREDORES)
        with c2: tipo_ local = st.selectbox("Local", LISTA_LOCAIS_TIPO)
        with c3: num_local = st.selectbox("Número", LISTA_NUMEROS_LOCAL)
        
        lado = st.selectbox("Lado", LISTA_LADOS)
        caixa = st.selectbox("Quantidade / Caixa", OPCOES_CAIXA)
        foto_vinho = st.file_uploader("Adicionar foto do rótulo", type=["jpg", "png", "jpeg"])
        
        st.write("")
        if st.form_submit_button("SALVAR", use_container_width=True):
            caminho_foto = dados_padrao.get("foto", "")
            if foto_vinho is not None:
                os.makedirs("fotos_vinhos", exist_ok=True)
                caminho_foto = os.path.join("fotos_vinhos", foto_vinho.name)
                with open(caminho_foto, "wb") as f:
                    f.write(foto_vinho.getbuffer())
            
            localizacao_completa = f"{cor} - {tipo_ local} {num_local.replace('Item ', '')}"
            st.session_state.estoque.append({
                "nome": nome.title(),
                "tipo": tipo.title(),
                "safra": safra,
                "localizacao": localizacao_completa,
                "lado": lado,
                "caixa": caixa,
                "foto": caminho_foto
            })
            salvar_dados(st.session_state.estoque)
            registrar_log(st.session_state.usuario_logado['nome'], "Cadastro", f"Adicionou {nome}")
            st.success("Vinho cadastrado com sucesso!")
            st.session_state.vinho_para_duplicar = None

# --- TELA DE ESTOQUE (Print 6) ---
elif st.session_state.menu_atual == "Estoque":
    st.markdown("### 🍷 Estoque")
    for idx, v in enumerate(st.session_state.estoque):
        st.markdown(
            f"""
            <div class="wine-card">
                <h4 style="color: #C9A227; margin: 0;">🍷 {v.get('nome')} ({v.get('safra')})</h4>
                <p style="margin: 5px 0; color: #DDD;">Tipo: {v.get('tipo')}</p>
                <p style="margin: 5px 0; color: #AAA; font-size: 0.9rem;">📍 {v.get('localizacao')} | 📦 {v.get('caixa')}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

# --- MAPA DE SEPARAÇÃO ---
elif st.session_state.menu_atual == "MapaSeparacao":
    st.markdown("### 🗺️ Mapa de Separação")
    lista_texto = st.text_area("Cole sua lista de vinhos (um por linha):", placeholder="Ex:\nChâteau Margaux\nCatena Zapata")
    if st.button("Gerar Rota"):
        if lista_texto.strip():
            linhas = [l.strip() for l in lista_texto.split("\n") if l.strip()]
            encontrados = [v for v in st.session_state.estoque if any(l.lower() in v.get('nome', '').lower() for l in linhas)]
            
            st.markdown("#### Rota Otimizada")
            for v in encontrados:
                st.markdown(
                    f"""
                    <div class="wine-card">
                        <h4 style="color: #C9A227; margin: 0;">{v.get('nome')}</h4>
                        <p style="margin: 5px 0;">📍 {v.get('localizacao')} (Lado {v.get('lado')})</p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
        else:
            st.warning("Insira uma lista de vinhos.")

# --- GERAR QR CODE ---
elif st.session_state.menu_atual == "GerarQR":
    st.markdown("### 📱 Gerar QR Code de Local")
    c = st.selectbox("Corredor", LISTA_CORREDORES)
    tl = st.selectbox("Tipo", LISTA_LOCAIS_TIPO)
    nl = st.selectbox("Número", LISTA_NUMEROS_LOCAL)
    texto_qr = f"{c} - {tl} {nl.replace('Item ', '')}"
    if st.button("Gerar Etiqueta"):
        st.image(gerar_qr_code_api(texto_qr), width=200)
        st.info(f"Local: {texto_qr}")

# --- GERENCIAR USUÁRIOS ---
elif st.session_state.menu_atual == "GerenciarUsuarios":
    st.markdown("### ⚙️ Gerenciar Contas")
    df = pd.DataFrame(st.session_state.usuarios)[["nome", "senha"]]
    df.columns = ["Usuário", "Senha"]
    st.dataframe(df, use_container_width=True)
