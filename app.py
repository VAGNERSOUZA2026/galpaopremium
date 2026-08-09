import json
import os
import shutil
from datetime import datetime
import pandas as pd
import streamlit as st
import urllib.parse
from streamlit_javascript import st_javascript

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

# Estilização CSS limpa e refinada com destaque para os badges
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(135deg, #F8F9FA 0%, #E9ECEF 100%); color: #1A1A1A; font-family: 'Poppins', sans-serif; }
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
    hora = datetime.now().hour
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

# Sessão
if "estoque" not in st.session_state: st.session_state.estoque = carregar_dados()
if "usuarios" not in st.session_state: st.session_state.usuarios = carregar_usuarios()
if "usuario_logado" not in st.session_state: st.session_state.usuario_logado = None
if "menu_atual" not in st.session_state: st.session_state.menu_atual = "🏠 Home"
if "termo_busca" not in st.session_state: st.session_state.termo_busca = ""
if "vinho_para_duplicar" not in st.session_state: st.session_state.vinho_para_duplicar = None

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
                            st.rerun()
                    else: st.error("Preencha todos os campos.")
        
        with tab_dev:
            with st.form("dev_form"):
                sp = st.text_input("Senha Mestra", type="password")
                st.write("")
                if st.form_submit_button("ACESSAR DEV", use_container_width=True):
                    if sp == SENHA_DEV:
                        st.session_state.usuario_logado = {"nome": "Dev", "cargo": "Desenvolvedor"}
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
        if st.button("📷 Escanear Local\n\nSelecionar Corredor", use_container_width=True): st.session_state.menu_atual = "Scanner"; st.rerun()
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
    c7, c8 = st.columns(2)
    with c7:
        if st.button("✏️ Editar Vinho\n\nModificar item", use_container_width=True): st.session_state.menu_atual = "Editar"; st.rerun()
    with c8:
        if st.button("🗑️ Excluir Vinho\n\nRemover item", use_container_width=True): st.session_state.menu_atual = "Excluir"; st.rerun()

    if st.session_state.usuario_logado['cargo'] in ["Administrador", "Desenvolvedor"] or st.session_state.usuario_logado['nome'] == "Dev":
        st.write("")
        if st.button("⚙️ Gerenciar Contas Cadastradas (Ver Logins e Senhas)", use_container_width=True):
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

elif st.session_state.menu_atual == "Scanner":
    st.subheader("📷 Escanear QR Code do Local")
    foto = st.camera_input("Capturar Foto")
    if foto and OPENCV_DISPONIVEL:
        img = cv2.imdecode(np.frombuffer(foto.getvalue(), np.uint8), cv2.IMREAD_COLOR)
        val, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
        if val:
            st.success(f"Localizado: {val}")
            for v in [x for x in st.session_state.estoque if val in x.get('localizacao', '')]:
                st.markdown(f"<div class='wine-card'><div class='wine-title'>🍷 {v.get('nome')}</div></div>", unsafe_allow_html=True)
        else: st.error("Nenhum QR Code encontrado.")

elif st.session_state.menu_atual == "Estoque":
    st.subheader("🍷 Estoque Completo (Ordem Alfabética)")
    
    estoque_ordenado = sorted(st.session_state.estoque, key=lambda x: x.get('nome', '').lower())
    
    if estoque_ordenado:
        st.info("💡 Clique em qualquer vinho abaixo para expandir, ver detalhes ou duplicar o cadastro para uma nova caixa/lote.")
        for idx_estoque, v in enumerate(estoque_ordenado):
            nome_exibicao = f"🍷 {v.get('nome')} ({v.get('safra', '')}) — [{v.get('tipo', 'Geral')}]"
            with st.expander(nome_exibicao):
                col_e1, col_e2 = st.columns([1, 2])
                with col_e1:
                    if v.get("foto") and os.path.exists(v.get("foto")):
                        st.image(v.get("foto"), width=160, caption="Foto do Vinho")
                    else:
                        st.info("Este vinho não possui foto cadastrada.")
                with col_e2:
                    st.markdown(f"<p style='font-size: 1.05rem;'><b>Nome:</b> {v.get('nome')}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='font-size: 1.05rem;'><b>Tipo:</b> {v.get('tipo', 'N/A')}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='font-size: 1.05rem;'><b>Safra:</b> {v.get('safra', 'N/A')}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='font-size: 1.05rem; margin-top: 10px;'><b>Localização:</b><br><span class='badge-pallet-grande'>📍 {v.get('localizacao', 'Não informada')} ({v.get('lado', '')})</span></p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='font-size: 1.05rem; margin-top: 10px;'><b>Embalagem:</b><br><span class='badge-caixa-grande'>📦 {v.get('caixa', 'N/A')}</span></p>", unsafe_allow_html=True)
                    
                    st.write("")
                    if st.button("📋 Duplicar Este Cadastro", key=f"dup_{idx_estoque}"):
                        st.session_state.vinho_para_duplicar = v
                        st.session_state.menu_atual = "Cadastrar"
                        st.rerun()
    else:
        st.info("Nenhum vinho cadastrado no estoque.")

elif st.session_state.menu_atual == "Cadastrar":
    st.subheader("➕ Cadastrar Novo Vinho / Duplicar Cadastro")
    
    # Se veio de uma duplicação, recupera os dados, senão inicia vazio
    dados_padrao = st.session_state.vinho_para_duplicar if st.session_state.vinho_para_duplicar else {}
    
    if st.session_state.vinho_para_duplicar:
        st.info(f"📋 Duplicando dados de: **{dados_padrao.get('nome')} ({dados_padrao.get('safra')})**. Ajuste o que precisar e salve.")
    
    with st.form("cad", clear_on_submit=True):
        nome = st.text_input("Nome do Vinho", value=dados_padrao.get("nome", "")).strip()
        tipo = st.text_input("Tipo (ex: Tinto, Branco)", value=dados_padrao.get("tipo", "")).strip()
        safra = st.text_input("Safra", value=dados_padrao.get("safra", "2024")).strip()
        
        col_loc1, col_loc2, col_loc3 = st.columns(3)
        with col_loc1:
            cor = st.selectbox("Corredor", LISTA_CORREDORES)
        with col_loc2:
            tipo_local = st.selectbox("Tipo de Local", LISTA_LOCAIS_TIPO)
        with col_loc3:
            num_local = st.selectbox("Número", LISTA_NUMEROS_LOCAL)
            
        lado = st.selectbox("Lado", LISTA_LADOS)
        caixa = st.selectbox("Quantidade / Caixa", OPCOES_CAIXA)
        foto_vinho = st.file_uploader("Enviar Foto do Vinho", type=["jpg", "png", "jpeg"])
        
        enviar = st.form_submit_button("Salvar Vinho no Estoque")
        if enviar:
            caminho_foto = dados_padrao.get("foto", "")
            if foto_vinho is not None:
                os.makedirs("fotos_vinhos", exist_ok=True)
                caminho_foto = os.path.join("fotos_vinhos", foto_vinho.name)
                with open(caminho_foto, "wb") as f:
                    f.write(foto_vinho.getbuffer())
            
            nome_formatado = nome.title()
            tipo_formatado = tipo.title()
            
            localizacao_completa = f"{cor} - {tipo_local} {num_local.replace('Item ', '')}"
            st.session_state.estoque.append({
                "nome": nome_formatado, 
                "tipo": tipo_formatado, 
                "safra": safra, 
                "localizacao": localizacao_completa, 
                "lado": lado, 
                "caixa": caixa,
                "foto": caminho_foto
            })
            salvar_dados(st.session_state.estoque)
            registrar_log(st.session_state.usuario_logado['nome'], "Cadastro de Vinho", f"{nome_formatado} em {localizacao_completa}")
            
            # Limpa o estado de duplicação após salvar
            st.session_state.vinho_para_duplicar = None
            st.success("Vinho cadastrado com sucesso! O formulário está pronto para um novo cadastro.")

elif st.session_state.menu_atual == "GerarQR":
    st.subheader("📱 Gerar QR Code de Localização")
    c = st.selectbox("Corredor", LISTA_CORREDORES)
    tl = st.selectbox("Tipo de Local", LISTA_LOCAIS_TIPO)
    nl = st.selectbox("Número", LISTA_NUMEROS_LOCAL)
    texto_qr = f"{c} - {tl} {nl.replace('Item ', '')}"
    if st.button("Gerar Etiqueta QR"): 
        st.image(gerar_qr_code_api(texto_qr))
        st.info(f"QR Code gerado para: **{texto_qr}**")

elif st.session_state.menu_atual == "Historico":
    st.subheader("📋 Histórico de Atividades")
    for l in carregar_logs():
        st.write(f"[{l.get('data_hora')}] {l.get('usuario')} - {l.get('acao')}: {l.get('detalhes')}")

elif st.session_state.menu_atual == "Editar":
    st.subheader("✏️ Editar Vinho (Todos os Dados e Imagem)")
    nomes = [f"{v.get('nome')} ({v.get('safra', '')})" for v in st.session_state.estoque]
    if nomes:
        esc = st.selectbox("Selecione o Vinho para Editar", nomes)
        idx = nomes.index(esc)
        v = st.session_state.estoque[idx]
        
        with st.form("edit_completo"):
            nn = st.text_input("Nome do Vinho", v.get('nome', '')).strip()
            nt = st.text_input("Tipo", v.get('tipo', '')).strip()
            ns = st.text_input("Safra", v.get('safra', '')).strip()
            
            col_loc1, col_loc2, col_loc3 = st.columns(3)
            with col_loc1:
                cor = st.selectbox("Corredor", LISTA_CORREDORES)
            with col_loc2:
                tipo_local = st.selectbox("Tipo de Local", LISTA_LOCAIS_TIPO)
            with col_loc3:
                num_local = st.selectbox("Número", LISTA_NUMEROS_LOCAL)
                
            nlado = st.selectbox("Lado", LISTA_LADOS, index=LISTA_LADOS.index(v.get('lado', 'Direito')) if v.get('lado') in LISTA_LADOS else 0)
            ncaixa = st.selectbox("Quantidade / Caixa", OPCOES_CAIXA, index=OPCOES_CAIXA.index(v.get('caixa', 'Caixa com 12 garrafas')) if v.get('caixa') in OPCOES_CAIXA else 0)
            
            st.write("---")
            if v.get("foto") and os.path.exists(v.get("foto")):
                st.image(v.get("foto"), width=120, caption="Foto atual cadastrada")
            else:
                st.info("Este vinho está sem foto cadastrada atualmente.")
                
            nova_foto_vinho = st.file_uploader("Alterar / Adicionar Foto do Vinho", type=["jpg", "png", "jpeg"])
            
            if st.form_submit_button("💾 Salvar Alterações"):
                caminho_foto = v.get("foto", "")
                if nova_foto_vinho is not None:
                    os.makedirs("fotos_vinhos", exist_ok=True)
                    caminho_foto = os.path.join("fotos_vinhos", nova_foto_vinho.name)
                    with open(caminho_foto, "wb") as f:
                        f.write(nova_foto_vinho.getbuffer())
                
                nome_formatado = nn.title()
                tipo_formatado = nt.title()

                localizacao_completa = f"{cor} - {tipo_local} {num_local.replace('Item ', '')}"
                st.session_state.estoque[idx] = {
                    "nome": nome_formatado,
                    "tipo": tipo_formatado,
                    "safra": ns,
                    "localizacao": localizacao_completa,
                    "lado": nlado,
                    "caixa": ncaixa,
                    "foto": caminho_foto
                }
                salvar_dados(st.session_state.estoque)
                registrar_log(st.session_state.usuario_logado['nome'], "Edição de Vinho", f"Atualizado: {nome_formatado}")
                st.success("Vinho atualizado com sucesso!")
                st.rerun()
    else:
        st.info("Nenhum vinho cadastrado para editar.")

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
    st.subheader("⚙️ Gerenciamento de Contas (Credenciais de Acesso)")
    
    if not st.session_state.usuarios:
        st.info("Nenhum usuário cadastrado.")
    else:
        df_usuarios = pd.DataFrame(st.session_state.usuarios)[["nome", "senha"]]
        df_usuarios.columns = ["Usuário", "Senha"]
        st.markdown("##### Relação de Contas e Senhas:")
        st.dataframe(df_usuarios, use_container_width=True)
        
        st.markdown("---")
        
        nomes_usuarios = [u["nome"] for u in st.session_state.usuarios]
        usuario_selecionado = st.selectbox("Selecione a conta para editar ou excluir:", nomes_usuarios)
        
        idx_u = next(i for i, u in enumerate(st.session_state.usuarios) if u["nome"] == usuario_selecionado)
        user_obj = st.session_state.usuarios[idx_u]
        
        with st.form("form_gerenciar_usuario"):
            novo_nome = st.text_input("Nome / Usuário", user_obj.get("nome", ""))
            nova_senha = st.text_input("Senha", user_obj.get("senha", ""))
            
            col_btn1, col_btn2 = st.columns(2)
            atualizar_usuario = col_btn1.form_submit_button("💾 Salvar Alterações", use_container_width=True)
            excluir_usuario = col_btn2.form_submit_button("🗑️ Excluir Conta", use_container_width=True)
            
            if atualizar_usuario:
                if novo_nome.strip():
                    st.session_state.usuarios[idx_u]["nome"] = novo_nome.strip()
                    st.session_state.usuarios[idx_u]["senha"] = nova_senha.strip()
                    salvar_usuarios(st.session_state.usuarios)
                    registrar_log(st.session_state.usuario_logado['nome'], "Gerenciamento de Conta", f"Atualizou credenciais de: {usuario_selecionado}")
                    st.success(f"Credenciais atualizadas com sucesso!")
                    st.rerun()
                else:
                    st.error("O nome de usuário não pode ficar em branco.")
                
            if excluir_usuario:
                if len(st.session_state.usuarios) <= 1:
                    st.error("Não é possível excluir o último usuário restante do sistema.")
                else:
                    removido = st.session_state.usuarios.pop(idx_u)
                    salvar_usuarios(st.session_state.usuarios)
                    registrar_log(st.session_state.usuario_logado['nome'], "Exclusão de Conta", f"Removeu o usuário: {removido['nome']}")
                    st.success(f"Conta de {usuario_selecionado} excluída com sucesso!")
                    st.rerun()
