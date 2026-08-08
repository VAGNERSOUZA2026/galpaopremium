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

# Configuração da página
st.set_page_config(
    page_title="Premium Wines - Wine Map Pro",
    page_icon="imagem premium.jpeg",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilização CSS Padrão
st.markdown(
    """
    <style>
    .stApp { background-color: #F8F9FA; color: #1A1A1A; font-family: 'Poppins', sans-serif; }
    [data-testid="stSidebar"] { display: none; }
    .wine-card { background-color: #FFFFFF; color: #1A1A1A; border-radius: 14px; padding: 16px; margin-bottom: 12px; border: 1px solid #E9ECEF; box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.03); }
    .wine-title { color: #7A1C2E; font-size: 1.1rem; font-weight: 700; margin-bottom: 4px; }
    .badge-pallet { background-color: #7A1C2E; color: #FFFFFF; padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 0.75rem; display: inline-block; }
    .stButton button { background-color: #7A1C2E !important; color: #FFFFFF !important; border-radius: 12px !important; font-weight: 600 !important; border: none !important; padding: 10px 16px !important; width: 100%; }
    .stButton button:hover { background-color: #922338 !important; color: #FFD700 !important; }
    </style>
""", unsafe_allow_html=True,
)

NOME_ARQUIVO = "estoque_galpao_pro.json"
ARQUIVO_USUARIOS = "usuarios_galpao.json"
ARQUIVO_LOGS = "logs_auditoria.json"
SENHA_DEV = "1980"

LISTA_CORREDORES = [f"Corredor {i:02d}" for i in range(1, 26)]
LISTA_PALLETS = [f"Pallet {i:02d}" for i in range(1, 26)]
LISTA_LADOS = ["Direito", "Esquerdo", "Centro / Único"]
OPCOES_CAIXA = ["Caixa com 12 garrafas", "Caixa com 6 garrafas", "Caixa com 3 garrafas", "Garrafa Avulsa (1 un)", "Outra quantidade"]

def obter_saudacao():
    hora = datetime.now().hour
    if 5 <= hora < 12: return "Bom dia"
    elif 12 <= hora < 18: return "Boa tarde"
    else: return "Boa noite"

def carregar_dados():
    if os.path.exists(NOME_ARQUIVO):
        try:
            with open(NOME_ARQUIVO, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return [{"nome": "Château Margaux", "tipo": "Tinto", "safra": "2015", "pallet": "Corredor 01 - Pallet 01", "lado": "Direito", "caixa": "Caixa com 12 garrafas"}]

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

# Sessão
if "estoque" not in st.session_state: st.session_state.estoque = carregar_dados()
if "usuarios" not in st.session_state: st.session_state.usuarios = carregar_usuarios()
if "usuario_logado" not in st.session_state: st.session_state.usuario_logado = None
if "menu_atual" not in st.session_state: st.session_state.menu_atual = "🏠 Home"

# --- TELA DE LOGIN / CADASTRO / DEV ---
if st.session_state.usuario_logado is None:
    st.write("")
    _, col_centro, _ = st.columns([1, 1.2, 1])
    with col_centro:
        with st.container(border=True):
            if os.path.exists("imagem premium.jpeg"):
                _, col_img, _ = st.columns([1, 1.2, 1])
                with col_img: st.image("imagem premium.jpeg", width=110)
            st.markdown("<h2 style='text-align: center; color: #7A1C2E; margin-bottom: 0;'>🍷 Wine Map Pro</h2>", unsafe_allow_html=True)
            
            tab_login, tab_cadastro, tab_dev = st.tabs(["🔑 Entrar", "👤 Criar Conta", "⚙️ Dev"])
            
            with tab_login:
                with st.form("login_form"):
                    u = st.text_input("Usuário").strip()
                    p = st.text_input("Senha", type="password").strip()
                    if st.form_submit_button("ENTRAR", use_container_width=True):
                        user = next((x for x in st.session_state.usuarios if x['nome'].lower() == u.lower() and x['senha'] == p), None)
                        if user:
                            st.session_state.usuario_logado = user
                            st.rerun()
                        else: st.error("Usuário ou senha incorretos.")
            
            with tab_cadastro:
                with st.form("cadastro_form"):
                    n = st.text_input("Nome Completo").strip()
                    c = st.selectbox("Cargo", ["Operador", "Conferente", "Administrador"])
                    s = st.text_input("Senha", type="password").strip()
                    if st.form_submit_button("CADASTRAR", use_container_width=True):
                        if n and s:
                            if any(x['nome'].lower() == n.lower() for x in st.session_state.usuarios):
                                st.error("Este usuário já existe.")
                            else:
                                novo = {"nome": n, "cargo": c, "senha": s}
                                st.session_state.usuarios.append(novo)
                                salvar_usuarios(st.session_state.usuarios)
                                registrar_log(n, "Criação de Conta", f"Cargo: {c}")
                                st.session_state.usuario_logado = novo
                                st.rerun()
                        else: st.error("Preencha todos os campos.")
            
            with tab_dev:
                with st.form("dev_form"):
                    sp = st.text_input("Senha Mestra", type="password")
                    if st.form_submit_button("ACESSAR DEV", use_container_width=True):
                        if sp == SENHA_DEV:
                            st.session_state.usuario_logado = {"nome": "Dev", "cargo": "Desenvolvedor"}
                            st.rerun()
                        else: st.error("Senha incorreta.")
    st.stop()

# --- TOPO LOGADO ---
c_t1, c_t2, c_t3 = st.columns([3, 2, 1])
with c_t1: st.markdown(f"<span style='color: #7A1C2E; font-weight: bold;'>🍷 Premium Wines</span> | Usuário: <b>{st.session_state.usuario_logado['nome']}</b>", unsafe_allow_html=True)
with c_t2:
    if st.session_state.menu_atual != "🏠 Home":
        if st.button("⬅️ Voltar ao Menu", use_container_width=True): st.session_state.menu_atual = "🏠 Home"; st.rerun()
with c_t3:
    if st.button("🚪 Sair", use_container_width=True): st.session_state.usuario_logado = None; st.session_state.menu_atual = "🏠 Home"; st.rerun()

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
        if st.button("📷 Escanear Pallet\n\nSelecionar Corredor", use_container_width=True): st.session_state.menu_atual = "Scanner"; st.rerun()
    with c3:
        if st.button("🍷 Estoque Completo\n\nVer todos os vinhos", use_container_width=True): st.session_state.menu_atual = "Estoque"; st.rerun()

    st.write("")
    c4, c5, c6 = st.columns(3)
    with c4:
        if st.button("➕ Cadastrar Vinho\n\n(Apenas Admin)", use_container_width=True): st.session_state.menu_atual = "Cadastrar"; st.rerun()
    with c5:
        if st.button("📱 Gerar QR Code\n\nEtiquetas de pallets", use_container_width=True): st.session_state.menu_atual = "GerarQR"; st.rerun()
    with c6:
        if st.button("📋 Histórico\n\nLogs de Auditoria", use_container_width=True): st.session_state.menu_atual = "Historico"; st.rerun()

    st.write("")
    c7, c8 = st.columns(2)
    with c7:
        if st.button("✏️ Editar Vinho\n\n(Apenas Admin)", use_container_width=True): st.session_state.menu_atual = "Editar"; st.rerun()
    with c8:
        if st.button("🗑️ Excluir Vinho\n\n(Apenas Admin)", use_container_width=True): st.session_state.menu_atual = "Excluir"; st.rerun()

    if st.session_state.usuario_logado['cargo'] in ["Administrador", "Desenvolvedor"] or st.session_state.usuario_logado['nome'] == "Dev":
        st.write("")
        if st.button("⚙️ Gerenciar Contas de Usuários (Editar/Excluir)", use_container_width=True):
            st.session_state.menu_atual = "GerenciarUsuarios"
            st.rerun()

elif st.session_state.menu_atual == "Filtros":
    st.subheader("🔍 Busca Avançada por Filtros")
    termo = st.text_input("Filtrar por Nome:").strip().lower()
    res = [v for v in st.session_state.estoque if termo in v.get("nome", "").lower()]
    for v in res:
        st.markdown(f"<div class='wine-card'><div class='wine-title'>🍷 {v.get('nome')} ({v.get('safra', '')})</div><p><span class='badge-pallet'>📍 {v.get('pallet', '')}</span></p></div>", unsafe_allow_html=True)

elif st.session_state.menu_atual == "Scanner":
    st.subheader("📷 Escanear QR Code do Pallet")
    foto = st.camera_input("Capturar Foto")
    if foto and OPENCV_DISPONIVEL:
        img = cv2.imdecode(np.frombuffer(foto.getvalue(), np.uint8), cv2.IMREAD_COLOR)
        val, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
        if val:
            st.success(f"Pallet: {val}")
            for v in [x for x in st.session_state.estoque if x.get('pallet') == val]:
                st.markdown(f"<div class='wine-card'><div class='wine-title'>🍷 {v.get('nome')}</div></div>", unsafe_allow_html=True)
        else: st.error("Nenhum QR Code encontrado.")

elif st.session_state.menu_atual == "Estoque":
    st.subheader("🍷 Estoque Completo")
    st.dataframe(pd.DataFrame(st.session_state.estoque), use_container_width=True)

elif st.session_state.menu_atual == "Cadastrar":
    st.subheader("➕ Cadastrar Novo Vinho")
    with st.form("cad"):
        nome = st.text_input("Nome").strip()
        tipo = st.text_input("Tipo").strip()
        safra = st.text_input("Safra", "2024").strip()
        cor = st.selectbox("Corredor", LISTA_CORREDORES)
        pal = st.selectbox("Pallet", LISTA_PALLETS)
        lado = st.selectbox("Lado", LISTA_LADOS)
        caixa = st.selectbox("Caixa", OPCOES_CAIXA)
        if st.form_submit_button("Salvar"):
            st.session_state.estoque.append({"nome": nome, "tipo": tipo, "safra": safra, "pallet": f"{cor} - {pal}", "lado": lado, "caixa": caixa})
            salvar_dados(st.session_state.estoque)
            registrar_log(st.session_state.usuario_logado['nome'], "Cadastro", nome)
            st.success("Cadastrado com sucesso!")
            st.rerun()

elif st.session_state.menu_atual == "GerarQR":
    st.subheader("📱 Gerar QR Code")
    c = st.selectbox("Corredor", LISTA_CORREDORES)
    p = st.selectbox("Pallet", LISTA_PALLETS)
    if st.button("Gerar"): st.image(gerar_qr_code_api(f"{c} - {p}"))

elif st.session_state.menu_atual == "Historico":
    st.subheader("📋 Histórico")
    for l in carregar_logs():
        st.write(f"[{l.get('data_hora')}] {l.get('usuario')} - {l.get('acao')}: {l.get('detalhes')}")

elif st.session_state.menu_atual == "Editar":
    st.subheader("✏️ Editar Vinho")
    nomes = [f"{v.get('nome')} ({v.get('safra', '')})" for v in st.session_state.estoque]
    if nomes:
        esc = st.selectbox("Selecione", nomes)
        idx = nomes.index(esc)
        v = st.session_state.estoque[idx]
        with st.form("edit"):
            nn = st.text_input("Nome", v.get('nome'))
            if st.form_submit_button("Atualizar"):
                st.session_state.estoque[idx]['nome'] = nn
                salvar_dados(st.session_state.estoque)
                st.success("Atualizado!")
                st.rerun()

elif st.session_state.menu_atual == "Excluir":
    st.subheader("🗑️ Excluir Vinho")
    nomes = [f"{v.get('nome')} ({v.get('safra', '')})" for v in st.session_state.estoque]
    if nomes:
        esc = st.selectbox("Selecione", nomes)
        idx = nomes.index(esc)
        if st.button("Excluir Definitivamente"):
            st.session_state.estoque.pop(idx)
            salvar_dados(st.session_state.estoque)
            st.success("Excluído!")
            st.rerun()

elif st.session_state.menu_atual == "GerenciarUsuarios":
    st.subheader("⚙️ Gerenciamento de Contas e Usuários")
    
    if not st.session_state.usuarios:
        st.info("Nenhum usuário cadastrado.")
    else:
        df_usuarios = pd.DataFrame(st.session_state.usuarios)[["nome", "cargo"]]
        st.dataframe(df_usuarios, use_container_width=True)
        
        st.markdown("---")
        
        nomes_usuarios = [u["nome"] for u in st.session_state.usuarios]
        usuario_selecionado = st.selectbox("Selecione o usuário para gerenciar:", nomes_usuarios)
        
        idx_u = next(i for i, u in enumerate(st.session_state.usuarios) if u["nome"] == usuario_selecionado)
        user_obj = st.session_state.usuarios[idx_u]
        
        with st.form("form_gerenciar_usuario"):
            antecessor_cargo = user_obj.get("cargo", "Operador")
            novo_cargo = st.selectbox("Alterar Cargo", ["Operador", "Conferente", "Administrador"], index=["Operador", "Conferente", "Administrador"].index(antecessor_cargo) if antecessor_cargo in ["Operador", "Conferente", "Administrador"] else 0)
            nova_senha = st.text_input("Nova Senha (deixe em branco para manter a atual)", type="password").strip()
            
            col_btn1, col_btn2 = st.columns(2)
            atualizar_usuario = col_btn1.form_submit_button("💾 Salvar Alterações", use_container_width=True)
            excluir_usuario = col_btn2.form_submit_button("🗑️ Excluir Conta", use_container_width=True)
            
            if atualizar_usuario:
                st.session_state.usuarios[idx_u]["cargo"] = novo_cargo
                if nova_senha:
                    st.session_state.usuarios[idx_u]["senha"] = nova_senha
                salvar_usuarios(st.session_state.usuarios)
                registrar_log(st.session_state.usuario_logado['nome'], "Gerenciamento de Conta", f"Atualizou o usuário: {usuario_selecionado}")
                st.success(f"Usuário {usuario_selecionado} atualizado com sucesso!")
                st.rerun()
                
            if excluir_usuario:
                if len(st.session_state.usuarios) <= 1:
                    st.error("Não é possível excluir o último usuário restante do sistema.")
                else:
                    removido = st.session_state.usuarios.pop(idx_u)
                    salvar_usuarios(st.session_state.usuarios)
                    registrar_log(st.session_state.usuario_logado['nome'], "Exclusão de Conta", f"Removeu o usuário: {removido['nome']}")
                    st.success(f"Conta de {usuario_selecionado} excluída com sucesso!")
                    st.rerun()
