import json
import os
import shutil
from datetime import datetime, timezone, timedelta
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

# Estilização CSS com bloqueio de pull-to-refresh para celulares
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

if not os.path.exists(PASTA_BACKUP):
    os.makedirs(PASTA_BACKUP)

LISTA_CORREDORES = [f"Corredor {i:02d}" for i in range(1, 26)]
LISTA_LOCAIS_TIPO = ["Pallet", "Prateleira"]
LISTA_NUMEROS_LOCAL = [f"Item {i:02d}" for i in range(1, 26)]
LISTA_LADOS = ["Direito", "Esquerdo", "Centro / Único"]
OPCOES_CAIXA = ["Caixa com 12 garrafas", "Caixa com 6 garrafas", "Caixa com 3 garrafas", "Caixa com 2 garrafas", "Garrafa Avulsa (1 un)", "Outra quantidade"]

def obter_saudacao():
    # Fuso horário de Brasília (UTC-3)
    fuso_brasilia = timezone(timedelta(hours=-3))
    hora = datetime.now(fuso_brasilia).hour
    if 0 <= hora < 12: return "Bom dia"
    elif 12 <= hora < 18: return "Boa tarde"
    else: return "Boa noite"

def realizar_backup(nome_arquivo):
    if os.path.exists(nome_arquivo):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy(nome_arquivo, os.path.join(PASTA_BACKUP, f"backup_{timestamp}_{nome_arquivo}"))

def carregar_dados():
    if os.path.exists(NOME_ARQUIVO):
        try:
            with open(NOME_ARQUIVO, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return [{"nome": "Château Margaux", "tipo": "Tinto", "safra": "2015", "localizacao": "Corredor 01 - Pallet 01", "lado": "Direito", "caixa": "Caixa com 12 garrafas", "foto": ""}]

def salvar_dados(estoque):
    with open(NOME_ARQUIVO, "w", encoding="utf-8") as f: json.dump(estoque, f, ensure_ascii=False, indent=4)
    realizar_backup(NOME_ARQUIVO)

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
                    if str(val).strip():
                        linhas.append(str(val).strip())
        elif extensao == 'docx':
            doc = Document(arquivo_enviado)
            for p in doc.paragraphs:
                if p.text.strip():
                    linhas.append(p.text.strip())
            for tabela in doc.tables:
                for linha in tabela.rows:
                    for celula in linha.cells:
                        if celula.text.strip():
                            linhas.append(celula.text.strip())
        elif extensao == 'txt':
            conteudo = arquivo_enviado.getvalue().decode("utf-8")
            linhas = [l.strip() for l in conteudo.split("\n") if l.strip()]
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
    return linhas

# Sessão
if "estoque" not in st.session_state: st.session_state.estoque = carregar_dados()
if "usuarios" not in st.session_state: st.session_state.usuarios = carregar_usuarios()
if "menu_atual" not in st.session_state: st.session_state.menu_atual = "🏠 Home"
if "termo_busca" not in st.session_state: st.session_state.termo_busca = ""
if "vinho_para_duplicar" not in st.session_state: st.session_state.vinho_para_duplicar = None

# Recuperação de sessão via URL
query_params = st.query_params
user_url = query_params.get("user", None)
cargo_url = query_params.get("cargo", "Operador")

if "usuario_logado" not in st.session_state or st.session_state.usuario_logado is None:
    if user_url:
        st.session_state.usuario_logado = {"nome": user_url, "cargo": cargo_url}
    else:
        st.session_state.usuario_logado = None

# --- TELA DE LOGIN / CADASTRO / DEV ---
if st.session_state.usuario_logado is None:
    st.write("")
    _, col_centro, _ = st.columns([1, 1.3, 1])
    with col_centro:
        if os.path.exists("imagem premium.jpeg"):
            _, col_img, _ = st.columns([1, 1.8, 1])
            with col_img: st.image("imagem premium.jpeg", width=190)
        
        st.markdown(
            """
            <div style="text-align: center; margin-top: 10px; margin-bottom: 20px;">
                <h1 style="color: #7A1C2E; font-size: 1.6rem; font-weight: 800; margin-bottom: 0; letter-spacing: 1px;">PREMIUM WINES</h1>
                <h2 style="color: #7A1C2E; font-size: 1.3rem; font-weight: 700; margin-top: 2px; letter-spacing: 2px;">GALPÃO</h2>
                <p style="color: #6C757D; font-size: 0.9rem; margin-top: 5px;">Controle Inteligente de Estoque e Vinhos</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        tab_login, tab_cadastro, tab_dev = st.tabs(["🔑 Entrar", "👤 Criar Conta", "⚙️ Dev"])
        
        with tab_login:
            with st.form("login_form"):
                u = st.text_input("Usuário").strip()
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
                n = st.text_input("Nome / Usuário").strip()
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
                            registrar_log(n, "Criação de Conta", "Novo cadastro simples realizado")
                            st.session_state.usuario_logado = novo
                            st.query_params["user"] = novo['nome']
                            st.query_params["cargo"] = novo['cargo']
                            st.rerun()
                    else: st.error("Preencha todos os campos.")
        
        with tab_dev:
            with st.form("dev_form"):
                sp = st.text_input("Senha Mestra", type="password")
                st.write("")
                if st.form_submit_button("ACESSAR DEV", use_container_width=True):
                    if sp == SENHA_DEV:
                        dev_obj = {"nome": "Dev", "cargo": "Desenvolvedor"}
                        st.session_state.usuario_logado = dev_obj
                        st.query_params["user"] = "Dev"
                        st.query_params["cargo"] = "Desenvolvedor"
                        st.rerun()
                    else: st.error("Senha incorreta.")
    st.stop()

# --- TOPO LOGADO ---
c_t1, c_t2, c_t3 = st.columns([3, 2, 1])
with c_t1: st.markdown(f"<span style='color: #7A1C2E; font-weight: bold;'>🍷 PREMIUM WINES GALPÃO</span> | Usuário: <b>{st.session_state.usuario_logado['nome']}</b>", unsafe_allow_html=True)
with c_t2:
    if st.session_state.menu_atual != "🏠 Home":
        if st.button("⬅️ Voltar ao Menu", use_container_width=True): st.session_state.menu_atual = "🏠 Home"; st.rerun()
with c_t3:
    if st.button("🚪 Sair", use_container_width=True): 
        st.session_state.usuario_logado = None
        st.query_params.clear()
        st.session_state.menu_atual = "🏠 Home"
        st.rerun()

st.markdown("---")

# --- MENU PRINCIPAL (HOME) ---
if st.session_state.menu_atual == "🏠 Home":
    if os.path.exists("imagem premium.jpeg"):
        _, c_img, _ = st.columns([1.5, 1, 1.5])
        with c_img:
            st.image("imagem premium.jpeg", width=220)
    
    saudacao = obter_saudacao()
    st.markdown(
        f"""
        <div style="text-align: center; margin-bottom: 25px;">
            <p style="color: #6C757D; margin-bottom: 0; font-size: 1.1rem;">{saudacao},</p>
            <h1 style="color: #7A1C2E; font-size: 2.2rem; font-weight: 800; margin-top: 0;">{st.session_state.usuario_logado['nome']}! 👋</h1>
            <p style="color: #495057; font-size: 0.95rem;">Escolha abaixo a opção desejada para gerenciar o galpão:</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🔍 Buscar / Filtros\n\nMúltiplos critérios", use_container_width=True): st.session_state.menu_atual = "Filtros"; st.rerun()
    with c2:
        if st.button("🗺️ Mapa de Separação\n\nEnviar arquivo ou lista", use_container_width=True): st.session_state.menu_atual = "MapaSeparacao"; st.rerun()
    with c3:
        if st.button("🍷 Estoque Completo\n\nVer todos os vinhos", use_container_width=True): st.session_state.menu_atual = "Estoque"; st.rerun()

    st.write("")
    c4, c5, c6 = st.columns(3)
    with c4:
        if st.button("➕ Cadastrar Vinho\n\nAdicionar ao sistema", use_container_width=True): st.session_state.vinho_para_duplicar = None; st.session_state.menu_atual = "Cadastrar"; st.rerun()
    with c5:
        if st.button("📱 Gerar QR Code\n\nEtiquetas de locais", use_container_width=True): st.session_state.menu_atual = "GerarQR"; st.rerun()
    with c6:
        if st.button("📋 Histórico\n\nLogs de Auditoria", use_container_width=True): st.session_state.menu_atual = "Historico"; st.rerun()

    st.write("")
    c7, c8, c9 = st.columns(3)
    with c7:
        if st.button("📷 Escanear Local\n\nCâmera QR", use_container_width=True): st.session_state.menu_atual = "Scanner"; st.rerun()
    with c8:
        if st.button("✏️ Editar Vinho\n\nModificar item", use_container_width=True): st.session_state.menu_atual = "Editar"; st.rerun()
    with c9:
        if st.button("🗑️ Excluir Vinho\n\nRemover item", use_container_width=True): st.session_state.menu_atual = "Excluir"; st.rerun()

    if st.session_state.usuario_logado['cargo'] in ["Administrador", "Desenvolvedor"] or st.session_state.usuario_logado['nome'] == "Dev":
        st.write("")
        if st.button("⚙️ Gerenciar Contas Cadastradas", use_container_width=True):
            st.session_state.menu_atual = "GerenciarUsuarios"
            st.rerun()

elif st.session_state.menu_atual == "Filtros":
    st.subheader("🔍 Busca por Nome ou Voz")
    c_texto, c_voz = st.columns([4, 1])
    with c_texto:
        termo = st.text_input("Filtrar por Nome:", value=st.session_state.termo_busca).strip()
    with c_voz:
        st.write("<br>", unsafe_allow_html=True)
        if st.button("🎙️ Voz"):
            resultado = buscar_por_voz()
            if resultado:
                st.session_state.termo_busca = resultado
                st.rerun()
    
    if termo or st.session_state.termo_busca:
        termo_pesquisa = termo.lower() if termo else st.session_state.termo_busca.lower()
        res = [v for v in st.session_state.estoque if termo_pesquisa in v.get("nome", "").lower()]
        if res:
            for v in res:
                col_f1, col_f2 = st.columns([1, 4])
                with col_f1:
                    if v.get("foto") and os.path.exists(v.get("foto")):
                        st.image(v.get("foto"), width=90)
                    else:
                        st.write("Sem foto")
                with col_f2:
                    st.markdown(
                        f"""<div class='wine-card'>
                            <div class='wine-title'>🍷 {v.get('nome')} ({v.get('safra', '')})</div>
                            <p style="font-size: 1rem; margin-top: 8px;">
                                Tipo: <b>{v.get('tipo', 'N/A')}</b><br><br>
                                <span class='badge-pallet-grande'>📍 {v.get('localizacao', 'Não informada')} ({v.get('lado', '')})</span><br><br>
                                <span class='badge-caixa-grande'>📦 {v.get('caixa', 'N/A')}</span>
                            </p>
                        </div>""", 
                        unsafe_allow_html=True
                    )
        else:
            st.info("Nenhum vinho encontrado com este nome.")
    else:
        st.info("Digite algo no campo acima ou use a busca por voz.")

elif st.session_state.menu_atual == "MapaSeparacao":
    st.subheader("🗺️ Mapa de Separação (Rota Otimizada)")
    st.markdown("Envie o arquivo recebido (**Excel** ou **Word**) ou cole a lista abaixo para gerar o roteiro automático de busca no galpão:")
    arquivo_enviado = st.file_uploader("📂 Enviar arquivo da lista (Word .docx ou Excel .xlsx)", type=["xlsx", "xls", "docx", "txt"])
    st.markdown("<p style='text-align: center; color: #6C757D; font-weight: bold; margin: 10px 0;'>— OU —</p>", unsafe_allow_html=True)
    lista_texto_usuario = st.text_area("Digite ou cole os vinhos manualmente (um por linha):", height=120)
    
    if st.button("Gerar Mapa de Rota"):
        linhas = []
        if arquivo_enviado is not None:
            linhas = extrair_linhas_de_arquivo(arquivo_enviado)
        elif lista_texto_usuario.strip():
            linhas = [l.strip() for l in lista_texto_usuario.split("\n") if l.strip()]
            
        if linhas:
            vinhos_encontrados = []
            vinhos_nao_encontrados = []
            for item in linhas:
                encontrado = None
                for v in st.session_state.estoque:
                    if item.lower() in v.get("nome", "").lower():
                        encontrado = v
                        break
                if encontrado:
                    if encontrado not in vinhos_encontrados:
                        vinhos_encontrados.append(encontrado)
                else:
                    vinhos_nao_encontrados.append(item)
            
            vinhos_encontrados.sort(key=lambda x: x.get('localizacao', ''))
            st.markdown("---")
            st.markdown(f"### 📍 Rota Otimizada de Coleta ({len(vinhos_encontrados)} itens encontrados)")
            if vinhos_encontrados:
                for idx, v in enumerate(vinhos_encontrados, 1):
                    st.markdown(
                        f"""<div class='wine-card'>
                            <div style="font-size: 0.9rem; color: #6C757D; font-weight: bold;">PASSO {idx:02d}</div>
                            <div class='wine-title'>🍷 {v.get('nome')} ({v.get('safra', '')})</div>
                            <p style="font-size: 1rem; margin-top: 6px;">
                                <span class='badge-pallet-grande'>📍 {v.get('localizacao', 'Não informada')} — Lado: {v.get('lado', '')}</span><br><br>
                                <span class='badge-caixa-grande'>📦 Embalagem: {v.get('caixa', 'N/A')}</span>
                            </p>
                        </div>""",
                        unsafe_allow_html=True
                    )
            if vinhos_nao_encontrados:
                st.warning(f"⚠️ Itens não encontrados: {', '.join(vinhos_nao_encontrados)}")
        else:
            st.error("Por favor, envie um arquivo ou digite os itens.")

elif st.session_state.menu_atual == "Scanner":
    st.subheader("📷 Escanear QR Code do Local")
    foto = st.camera_input("Capturar Foto")
    if foto and OPENCV_DISPONIVEL:
        img = cv2.imdecode(np.frombuffer(foto.getvalue(), np.uint8), cv2.IMREAD_COLOR)
        val, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
        if val:
            termo_lido = val.strip().lower()
            st.success(f"Localizado: {val}")
            resultados = [
                v for v in st.session_state.estoque 
                if termo_lido in v.get('localizacao', '').lower()
            ]
            if resultados:
                st.write(f"### 🍷 Vinhos encontrados neste local:")
                for v in resultados:
                    st.markdown(
                        f"""<div class='wine-card'>
                   
