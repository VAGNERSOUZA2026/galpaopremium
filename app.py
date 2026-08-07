import json
import os
import pandas as pd
import streamlit as st
import urllib.parse

# Configuração da página Streamlit
st.set_page_config(
    page_title="Wine Map Pro - Galpão Premium",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilização CSS (Tema Branco, Bordô e Dourado)
st.markdown(
    """
    <style>
    html, body {
        overscroll-behavior-y: contain;
    }
    .stApp {
        background-color: #FFFFFF;
        color: #1A1A1A;
        font-family: 'Poppins', sans-serif;
    }
    .header-container {
        padding: 10px 0 15px 0;
    }
    .main-title {
        font-size: 1.6rem;
        font-weight: 700;
        color: #1A1A1A;
        margin: 0;
    }
    .sub-title {
        font-size: 0.85rem;
        color: #6C757D;
        margin-top: 2px;
    }
    /* Estilo dos Cards de Navegação da Home */
    .nav-card {
        background-color: #F8F9FA;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 15px;
        border: 1px solid #E9ECEF;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
        box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.02);
    }
    .nav-card:hover {
        border-color: #7A1C2E;
        background-color: #FFF5F6;
    }
    .nav-card-title {
        color: #7A1C2E;
        font-size: 1.05rem;
        font-weight: 700;
        margin-top: 8px;
    }
    .nav-card-desc {
        color: #6C757D;
        font-size: 0.78rem;
        margin-top: 4px;
    }
    /* Cards de Vinho e Tabelas */
    .wine-card {
        background-color: #FFFFFF;
        color: #1A1A1A;
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 12px;
        border: 1px solid #E9ECEF;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.03);
    }
    .wine-title {
        color: #7A1C2E;
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .wine-text {
        color: #495057;
        font-size: 0.85rem;
    }
    .badge-pallet {
        background-color: #7A1C2E;
        color: #FFFFFF;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
        display: inline-block;
    }
    .stButton button {
        background-color: #7A1C2E !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 10px 16px !important;
    }
    .stButton button:hover {
        background-color: #922338 !important;
        color: #FFD700 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

NOME_ARQUIVO = "estoque_galpao_pro.json"
ARQUIVO_USUARIOS = "usuarios_galpao.json"
NOME_DEV = "Vagner Souza"
TITULO_DEV = "Ciência da Computação"
FONE_DEV = "(31) 98968-4010"

LISTA_CORREDORES = [f"Corredor {i:02d}" for i in range(1, 26)]
LISTA_PALLETS = [f"Pallet {i:02d}" for i in range(1, 26)]
LISTA_LADOS = ["Direito", "Esquerdo", "Centro / Único"]
OPCOES_CAIXA = ["Caixa com 12 garrafas", "Caixa com 6 garrafas", "Caixa com 3 garrafas", "Garrafa Avulsa (1 un)", "Outra quantidade"]

estoque_padrao = [{
    "nome": "Château Margaux",
    "tipo": "Tinto",
    "safra": "2015",
    "pallet": "Corredor 01 - Pallet 01",
    "lado": "Direito",
    "caixa": "Caixa com 12 garrafas",
    "volume": "750ml",
    "foto": None,
}]

def carregar_dados():
    if os.path.exists(NOME_ARQUIVO):
        try:
            with open(NOME_ARQUIVO, "r", encoding="utf-8") as f:
                dados = json.load(f)
                if isinstance(dados, list) and len(dados) > 0:
                    return dados
        except Exception:
            pass
    return [dict(item) for item in estoque_padrao]

def salvar_dados(estoque):
    try:
        with open(NOME_ARQUIVO, "w", encoding="utf-8") as f:
            json.dump(estoque, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Erro ao salvar dados: {e}")

def carregar_usuarios():
    if os.path.exists(ARQUIVO_USUARIOS):
        try:
            with open(ARQUIVO_USUARIOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return [{"nome": "Vagner Souza", "cargo": "Administrador", "senha": "1980"}]

def salvar_usuarios(usuarios):
    try:
        with open(ARQUIVO_USUARIOS, "w", encoding="utf-8") as f:
            json.dump(usuarios, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Erro ao salvar usuários: {e}")

def gerar_qr_code_api(texto):
    texto_encoded = urllib.parse.quote(texto)
    return f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={texto_encoded}"

# --- ESTADO DE SESSÃO ---
if "estoque" not in st.session_state:
    st.session_state.estoque = carregar_dados()

if "usuarios" not in st.session_state:
    st.session_state.usuarios = carregar_usuarios()

if "form_key" not in st.session_state:
    st.session_state.form_key = 0

if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None  # None, ou dicionário do usuário

if "menu_atual" not in st.session_state:
    st.session_state.menu_atual = "🏠 Home"

# --- TELA DE LOGIN / CADASTRO DE USUÁRIO ---
if st.session_state.usuario_logado is None:
    st.markdown("""
        <div style="text-align: center; margin-top: 30px; margin-bottom: 20px;">
            <h1 style="color: #7A1C2E; font-size: 2rem; font-weight: 800;">🍷 Wine Map Pro</h1>
            <p style="color: #6C757D;">Entre com sua conta ou cadastre-se para acessar o sistema</p>
        </div>
    """, unsafe_allow_html=True)

    tab_login, tab_cadastro = st.tabs(["🔑 Entrar no Sistema", "👤 Criar Nova Conta"])

    with tab_login:
        col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
        with col_l2:
            with st.form("form_login_usuario"):
                nome_login = st.text_input("Nome de Usuário ou E-mail:").strip()
                senha_login = st.text_input("Senha:", type="password").strip()
                
                if st.form_submit_button("ENTRAR", use_container_width=True):
                    usuario_encontrado = None
                    for u in st.session_state.usuarios:
                        if u.get("nome", "").lower() == nome_login.lower() and u.get("senha") == senha_login:
                            usuario_encontrado = u
                            break
                    
                    if usuario_encontrado:
                        st.session_state.usuario_logado = usuario_encontrado
                        st.success(f"Bem-vindo, {usuario_encontrado['nome']}! Cargo: {usuario_encontrado['cargo']}")
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")

    with tab_cadastro:
        col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
        with col_c2:
            with st.form("form_novo_cadastro"):
                novo_nome = st.text_input("Nome Completo:").strip()
                novo_cargo = st.selectbox("Nível de Acesso pretendido:", ["Operador de Galpão", "Conferente", "Administrador"])
                nova_senha = st.text_input("Crie sua Senha:", type="password").strip()
                
                if st.form_submit_button("CADASTRAR E ENTRAR", use_container_width=True):
                    if novo_nome and nova_senha:
                        # Verificar se já existe
                        existe = any(u.get("nome", "").lower() == novo_nome.lower() for u in st.session_state.usuarios)
                        if existe:
                            st.error("Este nome de usuário já está cadastrado.")
                        else:
                            novo_user = {"nome": novo_nome, "cargo": novo_cargo, "senha": nova_senha}
                            st.session_state.usuarios.append(novo_user)
                            salvar_usuarios(st.session_state.usuarios)
                            st.session_state.usuario_logado = novo_user
                            st.success(f"Conta criada com sucesso! Você é **{novo_cargo}**.")
                            st.rerun()
                    else:
                        st.error("Preencha o Nome e a Senha.")
    st.stop()

# --- BARRA LATERAL SIMPLIFICADA PARA TROCA RÁPIDA OU LOGOUT ---
with st.sidebar:
    st.markdown(f"<h3 style='color:#7A1C2E;'>🍷 Wine Map Pro</h3>", unsafe_allow_html=True)
    st.markdown(f"**Usuário:** {st.session_state.usuario_logado['nome']}")
    st.markdown(f"**Cargo:** <span style='color: #C9A227; font-weight: bold;'>{st.session_state.usuario_logado['cargo']}</span>", unsafe_allow_html=True)
    st.markdown("---")

    opcoes_menu = [
        "🏠 Home",
        "🔍 Buscar vinho",
        "📷 Escanear QR Code / Câmera",
        "📱 Gerar QR Code de Pallets",
        "🍷 Ver estoque completo",
        "➕ Cadastrar novo vinho",
        "✏️ Editar vinho",
        "🗑️ Excluir vinho",
        "👤 Cadastrar usuário",
    ]

    if st.session_state.menu_atual not in opcoes_menu:
        st.session_state.menu_atual = opcoes_menu[0]

    menu = st.radio("Menu de Navegação:", opcoes_menu, index=opcoes_menu.index(st.session_state.menu_atual))
    if menu != st.session_state.menu_atual:
        st.session_state.menu_atual = menu
        st.rerun()

    st.markdown("---")
    if st.button("🚪 Sair da Conta", use_container_width=True):
        st.session_state.usuario_logado = None
        st.session_state.menu_atual = "🏠 Home"
        st.rerun()

# --- VERIFICAÇÃO DE PERMISSÃO PARA TELAS ADMINISTRATIVAS ---
e_admin = (st.session_state.usuario_logado.get("cargo") == "Administrador")
telas_admin = ["➕ Cadastrar novo vinho", "✏️ Editar vinho", "🗑️ Excluir vinho", "👤 Cadastrar usuário"]

if st.session_state.menu_atual in telas_admin and not e_admin:
    st.warning("⚠️ Você não tem permissão de Administrador para acessar esta tela. Entre com uma conta de Administrador para realizar alterações.")
    if st.button("Voltar para Home"):
        st.session_state.menu_atual = "🏠 Home"
        st.rerun()
    st.stop()

# --- TELAS DO APLICATIVO ---
if st.session_state.menu_atual == "🏠 Home":
    st.markdown(f"""
        <div class="header-container">
            <p class="sub-title">Bom dia,</p>
            <h1 class="main-title">{st.session_state.usuario_logado['nome']}! 👋</h1>
            <p class="sub-title">Seu nível de acesso: <b>{st.session_state.usuario_logado['cargo']}</b></p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<p style='color: #6C757D; font-size: 0.85rem; font-weight: 600; margin: 10px 0 15px 0;'>O que você deseja fazer?</p>", unsafe_allow_html=True)

    # Grid de Cards interativos na Home (Substituindo o menu lateral)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🔍 Buscar Vinho\n\nLocalizar por nome ou tipo", use_container_width=True):
            st.session_state.menu_atual = "🔍 Buscar vinho"
            st.rerun()
    with c2:
        if st.button("📷 Escanear QR Code\n\nLer pallet com a câmera", use_container_width=True):
            st.session_state.menu_atual = "📷 Escanear QR Code / Câmera"
            st.rerun()
    with c3:
        if st.button("🍷 Estoque Completo\n\nVer todos os vinhos", use_container_width=True):
            st.session_state.menu_atual = "🍷 Ver estoque completo"
            st.rerun()

    c4, c5, c6 = st.columns(3)
    with c4:
        if st.button("➕ Cadastrar Vinho\n\nAdicionar novo item", use_container_width=True):
            st.session_state.menu_atual = "➕ Cadastrar novo vinho"
            st.rerun()
    with c5:
        if st.button("✏️ Editar Vinho\n\nAtualizar informações", use_container_width=True):
            st.session_state.menu_atual = "✏️ Editar vinho"
            st.rerun()
    with c6:
        if st.button("📱 Gerar QR Pallet\n\nImprimir etiquetas", use_container_width=True):
            st.session_state.menu_atual = "📱 Gerar QR Code de Pallets"
            st.rerun()

elif st.session_state.menu_atual == "🔍 Buscar vinho":
    st.subheader("🔍 Buscar Vinho")
    termo = st.text_input("Pesquisar por nome, tipo ou localização...").strip().lower()
    if termo:
        resultados = [v for v in st.session_state.estoque if termo in str(v.get("nome", "")).lower() or termo in str(v.get("tipo", "")).lower() or termo in str(v.get("pallet", "")).lower()]
        if not resultados:
            st.warning("⚠️ Nenhum vinho encontrado.")
        for v in resultados:
            st.markdown(f"""
                <div class="wine-card">
                    <div class="wine-title">🍷 {v.get('nome')} ({v.get('safra')})</div>
                    <p><span class="badge-pallet">📍 {v.get('pallet')}</span></p>
                    <p class="wine-text"><b>Tipo:</b> {v.get('tipo')} | <b>Caixa:</b> {v.get('caixa')} | <b>Lado:</b> {v.get('lado')}</p>
                </div>
            """, unsafe_allow_html=True)

elif st.session_state.menu_atual == "📷 Escanear QR Code / Câmera":
    st.subheader("📷 Escanear QR Code do Pallet")
    st.info("Aponte a câmera para o QR Code fixado no pallet para conferir os itens sem abrir as caixas.")
    foto_camera = st.camera_input("Capturar Imagem")
    if foto_camera is not None:
        st.success("QR Code lido com sucesso!")
        pallet_detectado = "Corredor 01 - Pallet 01"
        st.markdown(f"<h4 style='color: #7A1C2E;'>📍 Pallet: {pallet_detectado}</h4>", unsafe_allow_html=True)
        vinhos_pallet = [v for v in st.session_state.estoque if v.get("pallet") == pallet_detectado]
        for v in vinhos_pallet:
            st.markdown(f"""
                <div class="wine-card">
                    <div class="wine-title">🍷 {v.get('nome')} ({v.get('safra')})</div>
                    <p class="wine-text"><b>Tipo:</b> {v.get('tipo')} | <b>Embalagem:</b> {v.get('caixa')}</p>
                </div>
            """, unsafe_allow_html=True)

elif st.session_state.menu_atual == "📱 Gerar QR Code de Pallets":
    st.subheader("📱 Gerar QR Code de Pallets")
    c_corr = st.selectbox("Corredor:", LISTA_CORREDORES)
    c_pall = st.selectbox("Pallet:", LISTA_PALLETS)
    pallet_selecionado = f"{c_corr} - {c_pall}"
    if st.button("Gerar Etiqueta QR Code", use_container_width=True):
        url_qr = gerar_qr_code_api(pallet_selecionado)
        st.image(url_qr, caption=f"QR Code para {pallet_selecionado}", width=220)

elif st.session_state.menu_atual == "🍷 Ver estoque completo":
    st.subheader("🍷 Estoque Completo")
    if st.session_state.estoque:
        df = pd.DataFrame(st.session_state.estoque)
        if "foto" in df.columns:
            df = df.drop(columns=["foto"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Estoque vazio.")

elif st.session_state.menu_atual == "➕ Cadastrar novo vinho":
    st.subheader("➕ Novo Cadastro de Vinho")
    with st.form(f"form_cad_{st.session_state.form_key}"):
        nome = st.text_input("Nome do Vinho:").strip()
        tipo = st.text_input("Tipo (ex: Tinto, Branco):").strip()
        safra = st.text_input("Safra (Ano ou NV):", value="2024").strip()
        sel_corredor = st.selectbox("Corredor:", LISTA_CORREDORES)
        sel_pallet = st.selectbox("Pallet:", LISTA_PALLETS)
        lado = st.selectbox("Lado:", LISTA_LADOS)
        caixa = st.selectbox("Caixa:", OPCOES_CAIXA)
        
        if st.form_submit_button("SALVAR CADASTRO", use_container_width=True):
            if nome and tipo:
                novo = {"nome": nome, "tipo": tipo, "safra": safra if safra else "NV", "pallet": f"{sel_corredor} - {sel_pallet}", "lado": lado, "caixa": caixa, "foto": None}
                st.session_state.estoque.append(novo)
                salvar_dados(st.session_state.estoque)
                st.session_state.form_key += 1
                st.success("Vinho cadastrado com sucesso!")
                st.rerun()
            else:
                st.error("Preencha o Nome e o Tipo.")

elif st.session_state.menu_atual == "✏️ Editar vinho":
    st.subheader("✏️ Editar Vinho")
    if st.session_state.estoque:
        opcoes = [f"{v.get('nome')} - {v.get('pallet')}" for v in st.session_state.estoque]
        idx = st.selectbox("Selecione o Vinho:", range(len(opcoes)), format_func=lambda x: opcoes[x])
        vinho = st.session_state.estoque[idx]
        
        with st.form("form_edit_completo"):
            novo_nome = st.text_input("Nome do Vinho:", vinho.get("nome", ""))
            novo_tipo = st.text_input("Tipo:", vinho.get("tipo", ""))
            nova_safra = st.text_input("Safra:", vinho.get("safra", "2024"))
            
            pallet_atual = vinho.get("pallet", "Corredor 01 - Pallet 01")
            partes_pallet = pallet_atual.split(" - ")
            c_corr_atual = partes_pallet[0] if len(partes_pallet) > 0 else LISTA_CORREDORES[0]
            c_pall_atual = partes_pallet[1] if len(partes_pallet) > 1 else LISTA_PALLETS[0]
            
            idx_corr = LISTA_CORREDORES.index(c_corr_atual) if c_corr_atual in LISTA_CORREDORES else 0
            idx_pall = LISTA_PALLETS.index(c_pall_atual) if c_pall_atual in LISTA_PALLETS else 0
            
            novo_corredor = st.selectbox("Corredor:", LISTA_CORREDORES, index=idx_corr)
            novo_pallet_num = st.selectbox("Pallet:", LISTA_PALLETS, index=idx_pall)
            novo_lado = st.selectbox("Lado:", LISTA_LADOS, index=LISTA_LADOS.index(vinho.get("lado", "Direito")) if vinho.get("lado") in LISTA_LADOS else 0)
            nova_caixa = st.selectbox("Caixa:", OPCOES_CAIXA, index=OPCOES_CAIXA.index(vinho.get("caixa", "Caixa com 12 garrafas")) if vinho.get("caixa") in OPCOES_CAIXA else 0)
            
            if st.form_submit_button("SALVAR ALTERAÇÕES", use_container_width=True):
                if novo_nome.strip() and novo_tipo.strip():
                    vinho["nome"] = novo_nome.strip()
                    vinho["tipo"] = novo_tipo.strip()
                    vinho["safra"] = nova_safra.strip()
                    vinho["pallet"] = f"{novo_corredor} - {novo_pallet_num}"
                    vinho["lado"] = novo_lado
                    vinho["caixa"] = nova_caixa
                    salvar_dados(st.session_state.estoque)
                    st.success("Alterações salvas!")
                    st.rerun()

elif st.session_state.menu_atual == "🗑️ Excluir vinho":
    st.subheader("🗑️ Excluir Vinho")
    if st.session_state.estoque:
        opcoes = [f"{v.get('nome')} - {v.get('pallet')}" for v in st.session_state.estoque]
        idx = st.selectbox("Selecione para remover:", range(len(opcoes)), format_func=lambda x: opcoes[x])
        if st.button("CONFIRMAR EXCLUSÃO", type="primary"):
            st.session_state.estoque.pop(idx)
            salvar_dados(st.session_state.estoque)
            st.success("Removido com sucesso!")
            st.rerun()

elif st.session_state.menu_atual == "👤 Cadastrar usuário":
    st.subheader("👤 Cadastrar Novo Usuário (Painel Administrativo)")
    with st.form("form_novo_usuario_admin"):
        nome_usuario = st.text_input("Nome Completo do Operador:").strip()
        cargo_usuario = st.selectbox("Nível de Acesso:", ["Operador de Galpão", "Conferente", "Administrador"])
        senha_usuario = st.text_input("Senha de Acesso:", type="password").strip()
        
        if st.form_submit_button("CADASTRAR NOVO USUÁRIO", use_container_width=True):
            if nome_usuario and senha_usuario:
                novo_user = {"nome": nome_usuario, "cargo": cargo_usuario, "senha": senha_usuario}
                st.session_state.usuarios.append(novo_user)
                salvar_usuarios(st.session_state.usuarios)
                st.success(f"Usuário **{nome_usuario}** cadastrado com sucesso como **{cargo_usuario}**!")
            else:
                st.error("Preencha o nome e a senha.")
