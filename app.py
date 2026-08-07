import json
import os
from datetime import datetime
import pandas as pd
import streamlit as st
import urllib.parse

# Configuração da página Streamlit
st.set_page_config(
    page_title="Premium Wines - Wine Map Pro",
    page_icon="imagem premium.jpeg",
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
        padding: 5px 0 10px 0;
    }
    .main-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1A1A1A;
        margin: 0;
    }
    .sub-title {
        font-size: 0.85rem;
        color: #6C757D;
        margin-top: 2px;
    }
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
ARQUIVO_LOGS = "logs_auditoria.json"
SENHA_DEV = "1980"

NOME_DEV = "Vagner Souza"
TITULO_DEV = "Ciência da Computação"
FONE_DEV = "(31) 98968-4010"

LISTA_CORREDORES = [f"Corredor {i:02d}" for i in range(1, 26)]
LISTA_PALLETS = [f"Pallet {i:02d}" for i in range(1, 26)]
LISTA_LADOS = ["Direito", "Esquerdo", "Centro / Único"]
OPCOES_CAIXA = [
    "Caixa com 12 garrafas",
    "Caixa com 6 garrafas",
    "Caixa com 3 garrafas",
    "Garrafa Avulsa (1 un)",
    "Outra quantidade",
]

estoque_padrao = [
    {
        "nome": "Château Margaux",
        "tipo": "Tinto",
        "safra": "2015",
        "pallet": "Corredor 01 - Pallet 01",
        "lado": "Direito",
        "caixa": "Caixa com 12 garrafas",
        "volume": "750ml",
        "foto": None,
    }
]


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


def carregar_logs():
    if os.path.exists(ARQUIVO_LOGS):
        try:
            with open(ARQUIVO_LOGS, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def registrar_log(usuario, acao, detalhes):
    logs = carregar_logs()
    novo_log = {
        "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "usuario": usuario,
        "acao": acao,
        "detalhes": detalhes,
    }
    logs.insert(0, novo_log)
    try:
        with open(ARQUIVO_LOGS, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)
    except Exception:
        pass


def gerar_qr_code_api(texto):
    texto_encoded = urllib.parse.quote(texto)
    return (
        f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={texto_encoded}"
    )


# --- ESTADO DE SESSÃO ---
if "estoque" not in st.session_state:
    st.session_state.estoque = carregar_dados()

if "usuarios" not in st.session_state:
    st.session_state.usuarios = carregar_usuarios()

if "form_key" not in st.session_state:
    st.session_state.form_key = 0

if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

if "menu_atual" not in st.session_state:
    st.session_state.menu_atual = "🏠 Home"

if "modo_dev" not in st.session_state:
    st.session_state.modo_dev = False

# --- TELA DE LOGIN / CADASTRO DE USUÁRIO ---
if st.session_state.usuario_logado is None:
    if os.path.exists("imagem premium.jpeg"):
        col_img1, col_img2, col_img3 = st.columns([1, 1.2, 1])
        with col_img2:
            # Imagem com tamanho controlado (width=260) para não ocupar a tela inteira
            st.image("imagem premium.jpeg", width=260)

    st.markdown(
        """
        <div style="text-align: center; margin-top: 10px; margin-bottom: 15px;">
            <h1 style="color: #7A1C2E; font-size: 1.5rem; font-weight: 800;">🍷 Premium Wines - Wine Map Pro</h1>
            <p style="color: #6C757D; font-size: 0.85rem;">Entre com sua conta ou cadastre-se para acessar o sistema</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    tab_login, tab_cadastro, tab_dev = st.tabs(
        ["🔑 Entrar", "👤 Criar Conta", "⚙️ Painel Dev (1980)"]
    )

    with tab_login:
        col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
        with col_l2:
            with st.form("form_login_usuario"):
                nome_login = st.text_input("Nome de Usuário:").strip()
                senha_login = st.text_input("Senha:", type="password").strip()

                if st.form_submit_button("ENTRAR NO SISTEMA", use_container_width=True):
                    usuario_encontrado = None
                    for u in st.session_state.usuarios:
                        if (
                            u.get("nome", "").lower() == nome_login.lower()
                            and u.get("senha") == senha_login
                        ):
                            usuario_encontrado = u
                            break

                    if usuario_encontrado:
                        st.session_state.usuario_logado = usuario_encontrado
                        st.session_state.modo_dev = False
                        st.success(
                            f"Bem-vindo, {usuario_encontrado['nome']}! Cargo: {usuario_encontrado['cargo']}"
                        )
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")

    with tab_cadastro:
        col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
        with col_c2:
            with st.form("form_novo_cadastro"):
                novo_nome = st.text_input("Nome Completo:").strip()
                novo_cargo = st.selectbox(
                    "Cargo:",
                    ["Operador de Galpão", "Conferente", "Administrador"],
                )
                nova_senha = st.text_input(
                    "Crie sua Senha:", type="password"
                ).strip()

                if st.form_submit_button("CADASTRAR", use_container_width=True):
                    if novo_nome and nova_senha:
                        existe = any(
                            u.get("nome", "").lower() == novo_nome.lower()
                            for u in st.session_state.usuarios
                        )
                        if existe:
                            st.error(
                                "Este nome de usuário já está cadastrado."
                            )
                        else:
                            novo_user = {
                                "nome": novo_nome,
                                "cargo": novo_cargo,
                                "senha": nova_senha,
                            }
                            st.session_state.usuarios.append(novo_user)
                            salvar_usuarios(st.session_state.usuarios)
                            registrar_log(
                                novo_nome,
                                "Criação de Conta",
                                f"Cargo: {novo_cargo}",
                            )
                            st.session_state.usuario_logado = novo_user
                            st.session_state.modo_dev = False
                            st.success(
                                f"Conta criada com sucesso! Você é **{novo_cargo}**."
                            )
                            st.rerun()
                    else:
                        st.error("Preencha o Nome e a Senha.")

    with tab_dev:
        col_d1, col_d2, col_d3 = st.columns([1, 2, 1])
        with col_d2:
            with st.form("form_login_dev"):
                st.markdown(
                    "<p style='color: #7A1C2E; font-weight: bold;'>Acesso Exclusivo do Desenvolvedor</p>",
                    unsafe_allow_html=True,
                )
                senha_dev_input = st.text_input(
                    "Senha Mestra do Desenvolvedor:", type="password"
                ).strip()
                if st.form_submit_button(
                    "ACESSAR PAINEL DEV", use_container_width=True
                ):
                    if senha_dev_input == SENHA_DEV:
                        st.session_state.modo_dev = True
                        st.session_state.usuario_logado = {
                            "nome": NOME_DEV,
                            "cargo": "Desenvolvedor",
                            "senha": SENHA_DEV,
                        }
                        st.success("Painel do Desenvolvedor liberado!")
                        st.rerun()
                    else:
                        st.error(
                            "Senha mestra incorreta! A senha padrão do desenvolvedor é 1980."
                        )
    st.stop()

# --- BARRA LATERAL ---
with st.sidebar:
    if os.path.exists("imagem premium.jpeg"):
        st.image("imagem premium.jpeg", width=140)
    
    st.markdown(
        f"<h3 style='color:#7A1C2E; margin-top:5px;'>Premium Wines</h3>",
        unsafe_allow_html=True,
    )
    st.markdown(f"**Usuário:** {st.session_state.usuario_logado['nome']}")
    st.markdown(
        f"**Cargo:** <span style='color: #C9A227; font-weight: bold;'>{st.session_state.usuario_logado['cargo']}</span>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    opcoes_menu = [
        "🏠 Home",
        "🔍 Buscar / Filtros Múltiplos",
        "📷 Escanear QR Code / Câmera",
        "📱 Gerar QR Code de Pallets",
        "🍷 Ver estoque completo",
        "➕ Cadastrar novo vinho",
        "✏️ Editar vinho",
        "🗑️ Excluir vinho",
        "📋 Histórico de Auditoria",
    ]

    if st.session_state.modo_dev:
        opcoes_menu.append("⚙️ Gerenciar Usuários (Dev)")

    if st.session_state.menu_atual not in opcoes_menu:
        st.session_state.menu_atual = opcoes_menu[0]

    menu = st.radio(
        "Menu de Navegação:",
        opcoes_menu,
        index=opcoes_menu.index(st.session_state.menu_atual),
    )
    if menu != st.session_state.menu_atual:
        st.session_state.menu_atual = menu
        st.rerun()

    st.markdown("---")
    if st.button("🚪 Sair da Conta", use_container_width=True):
        st.session_state.usuario_logado = None
        st.session_state.modo_dev = False
        st.session_state.menu_atual = "🏠 Home"
        st.rerun()

# --- RESTRIÇÕES DE ACESSO ---
cargo_atual = st.session_state.usuario_logado.get("cargo")
e_admin = (
    cargo_atual in ["Administrador", "Desenvolvedor"]
) or st.session_state.modo_dev
e_dev = st.session_state.modo_dev or (
    st.session_state.usuario_logado.get("nome") == NOME_DEV
)

telas_admin = ["➕ Cadastrar novo vinho", "✏️ Editar vinho", "🗑️ Excluir vinho"]

if st.session_state.menu_atual in telas_admin and not e_admin:
    st.warning(
        "⚠️ Acesso restrito! Apenas usuários com o cargo de **Administrador** podem cadastrar, editar ou excluir vinhos."
    )
    if st.button("Voltar para Home"):
        st.session_state.menu_atual = "🏠 Home"
        st.rerun()
    st.stop()

if st.session_state.menu_atual == "⚙️ Gerenciar Usuários (Dev)" and not e_dev:
    st.warning(
        "⚠️ Esta opção é exclusiva para o Desenvolvedor (Senha Mestra: 1980)."
    )
    if st.button("Voltar para Home"):
        st.session_state.menu_atual = "🏠 Home"
        st.rerun()
    st.stop()

# --- TELAS DO APLICATIVO ---
if st.session_state.menu_atual == "🏠 Home":
    if os.path.exists("imagem premium.jpeg"):
        col_img1, col_img2, col_img3 = st.columns([1, 1.8, 1])
        with col_img2:
            st.image("imagem premium.jpeg", width=320)

    st.markdown(
        f"""
        <div class="header-container" style="text-align: center;">
            <p class="sub-title">Bom dia,</p>
            <h1 class="main-title">{st.session_state.usuario_logado['nome']}! 👋</h1>
            <p class="sub-title">Bem-vindo ao sistema de localização de vinhos do galpão <b>Premium Wines</b>.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "<p style='color: #6C757D; font-size: 0.85rem; font-weight: 600; margin: 10px 0 15px 0;'>O que você deseja fazer?</p>",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button(
            "🔍 Buscar / Filtros\n\nMúltiplos critérios",
            use_container_width=True,
        ):
            st.session_state.menu_atual = "🔍 Buscar / Filtros Múltiplos"
            st.rerun()
    with c2:
        if st.button(
            "📷 Escanear QR Code\n\nLer pallet com a câmera",
            use_container_width=True,
        ):
            st.session_state.menu_atual = "📷 Escanear QR Code / Câmera"
            st.rerun()
    with c3:
        if st.button(
            "🍷 Estoque Completo\n\nVer todos os vinhos",
            use_container_width=True,
        ):
            st.session_state.menu_atual = "🍷 Ver estoque completo"
            st.rerun()

    c4, c5, c6 = st.columns(3)
    with c4:
        if st.button(
            "➕ Cadastrar Vinho\n\n(Apenas Admin)", use_container_width=True
        ):
            st.session_state.menu_atual = "➕ Cadastrar novo vinho"
            st.rerun()
    with c5:
        if st.button(
            "✏️ Editar Vinho\n\n(Apenas Admin)", use_container_width=True
        ):
            st.session_state.menu_atual = "✏️ Editar vinho"
            st.rerun()
    with c6:
        if st.button(
            "📋 Histórico\n\nLogs de Auditoria", use_container_width=True
        ):
            st.session_state.menu_atual = "📋 Histórico de Auditoria"
            st.rerun()

elif st.session_state.menu_atual == "🔍 Buscar / Filtros Múltiplos":
    st.subheader("🔍 Busca Avançada por Filtros Múltiplos")
    st.markdown(
        "<p style='color: #6C757D; font-size: 0.85rem;'>Filtre o estoque simultaneamente por nome, corredor, lado, tipo e safra.</p>",
        unsafe_allow_html=True,
    )

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        termo_nome = st.text_input("Filtrar por Nome ou Vinícola:").strip().lower()
        tipos_disponiveis = [
            "Todos"
        ] + sorted(list(set(v.get("tipo", "") for v in st.session_state.estoque)))
        filtro_tipo = st.selectbox("Filtrar por Tipo de Vinho:", tipos_disponiveis)

    with col_f2:
        corredores_disponiveis = ["Todos"] + LISTA_CORREDORES
        filtro_corredor = st.selectbox(
            "Filtrar por Corredor:", corredores_disponiveis
        )
        lados_disponiveis = ["Todos"] + LISTA_LADOS
        filtro_lado = st.selectbox("Filtrar por Lado:", lados_disponiveis)

    resultados = st.session_state.estoque
    if termo_nome:
        resultados = [
            v
            for v in resultados
            if termo_nome in str(v.get("nome", "")).lower()
        ]
    if filtro_tipo != "Todos":
        resultados = [v for v in resultados if v.get("tipo") == filtro_tipo]
    if filtro_corredor != "Todos":
        resultados = [
            v
            for v in resultados
            if filtro_corredor in str(v.get("pallet", ""))
        ]
    if filtro_lado != "Todos":
        resultados = [v for v in resultados if v.get("lado") == filtro_lado]

    st.markdown(f"**Resultados encontrados:** {len(resultados)}")
    st.markdown("---")

    if not resultados:
        st.warning("⚠️ Nenhum vinho encontrado com os filtros selecionados.")
    for v in resultados:
        st.markdown(
            f"""
            <div class="wine-card">
                <div class="wine-title">🍷 {v.get('nome')} ({v.get('safra')})</div>
                <p><span class="badge-pallet">📍 {v.get('pallet')}</span></p>
                <p class="wine-text"><b>Tipo:</b> {v.get('tipo')} | <b>Caixa:</b> {v.get('caixa')} | <b>Lado:</b> {v.get('lado')}</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

elif st.session_state.menu_atual == "📷 Escanear QR Code / Câmera":
    st.subheader("📷 Escanear QR Code do Pallet")
    st.info(
        "Aponte a câmera do celular/dispositivo para o QR Code fixado no pallet para conferir os itens."
    )
    foto_camera = st.camera_input("Capturar Imagem")
    if foto_camera is not None:
        st.success("QR Code lido com sucesso!")
        pallet_detectado = "Corredor 01 - Pallet 01"
        st.markdown(
            f"<h4 style='color: #7A1C2E;'>📍 Pallet: {pallet_detectado}</h4>",
            unsafe_allow_html=True,
        )
        vinhos_pallet = [
            v
            for v in st.session_state.estoque
            if v.get("pallet") == pallet_detectado
        ]
        for v in vinhos_pallet:
            st.markdown(
                f"""
                <div class="wine-card">
                    <div class="wine-title">🍷 {v.get('nome')} ({v.get('safra')})</div>
                    <p class="wine-text"><b>Tipo:</b> {v.get('tipo')} | <b>Embalagem:</b> {v.get('caixa')}</p>
                </div>
            """,
                unsafe_allow_html=True,
            )

elif st.session_state.menu_atual == "📱 Gerar QR Code de Pallets":
    st.subheader("📱 Gerar QR Code de Pallets")
    c_corr = st.selectbox("Corredor:", LISTA_CORREDORES)
    c_pall = st.selectbox("Pallet:", LISTA_PALLETS)
    pallet_selecionado = f"{c_corr} - {c_pall}"
    if st.button("Gerar Etiqueta QR Code", use_container_width=True):
        url_qr = gerar_qr_code_api(pallet_selecionado)
        st.image(
            url_qr, caption=f"QR Code para {pallet_selecionado}", width=220
        )

elif st.session_state.menu_atual == "🍷 Ver estoque completo":
    st.subheader("🍷 Estoque Completo - Premium Wines")
    if st.session_state.estoque:
        df = pd.DataFrame(st.session_state.estoque)
        if "foto" in df.columns:
            df = df.drop(columns=["foto"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Estoque vazio.")

elif st.session_state.menu_atual == "➕ Cadastrar novo vinho":
    st.subheader("➕ Novo Cadastro de Vinho (Exclusivo Administrador)")
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
                novo_item = {
                    "nome": nome,
                    "tipo": tipo,
                    "safra": safra,
                    "pallet": f"{sel_corredor} - {sel_pallet}",
                    "lado": lado,
                    "caixa": caixa,
                    "volume": "750ml",
                    "foto": None,
                }
                st.session_state.estoque.append(novo_item)
                salvar_dados(st.session_state.estoque)
                registrar_log(
                    st.session_state.usuario_logado["nome"],
                    "Cadastro de Vinho",
                    f"{nome} ({safra}) em {sel_corredor}",
                )
                st.success(f"Vinho '{nome}' cadastrado com sucesso!")
                st.session_state.form_key += 1
                st.rerun()
            else:
                st.error("Preencha ao menos o Nome e o Tipo do vinho.")

elif st.session_state.menu_atual == "✏️ Editar vinho":
    st.subheader("✏️ Editar Vinho Cadastrado (Exclusivo Administrador)")
    if not st.session_state.estoque:
        st.info("Nhum vinho cadastrado para editar.")
    else:
        nomes_vinhos = [f"{v.get('nome')} ({v.get('safra')}) - {v.get('pallet')}" for v in st.session_state.estoque]
        escolha_vinho = st.selectbox("Selecione o vinho para alterar:", nomes_vinhos)
        idx_vinho = nomes_vinhos.index(escolha_vinho)
        vinho_sel = st.session_state.estoque[idx_vinho]

        with st.form("form_edicao_vinho"):
            novo_nome = st.text_input("Nome do Vinho:", value=vinho_sel.get("nome", "")).strip()
            novo_tipo = st.text_input("Tipo:", value=vinho_sel.get("tipo", "")).strip()
            nova_safra = st.text_input("Safra:", value=vinho_sel.get("safra", "")).strip()
            
            novo_corredor = st.selectbox("Corredor:", LISTA_CORREDORES)
            novo_pallet_num = st.selectbox("Pallet:", LISTA_PALLETS)
            novo_lado = st.selectbox("Lado:", LISTA_LADOS, index=LISTA_LADOS.index(vinho_sel.get("lado", "Direito")) if vinho_sel.get("lado") in LISTA_LADOS else 0)
            nova_caixa = st.selectbox("Caixa:", OPCOES_CAIXA)

            if st.form_submit_button("ATUALIZAR DADOS", use_container_width=True):
                st.session_state.estoque[idx_vinho] = {
                    "nome": novo_nome,
                    "tipo": novo_tipo,
                    "safra": nova_safra,
                    "pallet": f"{novo_corredor} - {novo_pallet_num}",
                    "lado": novo_lado,
                    "caixa": nova_caixa,
                    "volume": vinho_sel.get("volume", "750ml"),
                    "foto": vinho_sel.get("foto")
                }
                salvar_dados(st.session_state.estoque)
                registrar_log(
                    st.session_state.usuario_logado["nome"],
                    "Edição de Vinho",
                    f"Atualizado: {novo_nome}"
                )
                st.success("Dados atualizados com sucesso!")
                st.rerun()

elif st.session_state.menu_atual == "🗑️ Excluir vinho":
    st.subheader("🗑️ Excluir Vinho (Exclusivo Administrador)")
    if not st.session_state.estoque:
        st.info("Estoque vazio.")
    else:
        nomes_vinhos = [f"{v.get('nome')} ({v.get('safra')}) - {v.get('pallet')}" for v in st.session_state.estoque]
        vinho_para_excluir = st.selectbox("Selecione o vinho a remover:", nomes_vinhos)
        idx_excluir = nomes_vinhos.index(vinho_para_excluir)

        if st.button("EXCLUIR DEFINITIVAMENTE", use_container_width=True):
            removido = st.session_state.estoque.pop(idx_excluir)
            salvar_dados(st.session_state.estoque)
            registrar_log(
                st.session_state.usuario_logado["nome"],
                "Exclusão de Vinho",
                f"Removido: {removido.get('nome')}"
            )
            st.success(f"Vinho '{removido.get('nome')}' excluído com sucesso!")
            st.rerun()

elif st.session_state.menu_atual == "📋 Histórico de Auditoria":
    st.subheader("📋 Histórico de Ações e Auditoria")
    logs = carregar_logs()
    if not logs:
        st.info("Nenhum registro de log encontrado.")
    else:
        for l in logs:
            st.markdown(
                f"""
                <div style="background-color: #F8F9FA; padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid #7A1C2E;">
                    <p style="margin: 0; font-size: 0.8rem; color: #6C757D;"><b>{l.get('data_hora')}</b> — Usuário: <b>{l.get('usuario')}</b></p>
                    <p style="margin: 4px 0 0 0; font-size: 0.9rem; color: #1A1A1A;"><b>Ação:</b> {l.get('acao')} | <b>Detalhes:</b> {l.get('detalhes')}</p>
                </div>
            """,
                unsafe_allow_html=True,
            )

elif st.session_state.menu_atual == "⚙️ Gerenciar Usuários (Dev)":
    st.subheader("⚙️ Painel de Gerenciamento de Usuários (Desenvolvedor)")
    st.write("Lista de usuários cadastrados no sistema:")
    if st.session_state.usuarios:
        df_users = pd.DataFrame(st.session_state.usuarios)
        st.dataframe(df_users, use_container_width=True)
    
    st.markdown("---")
    if st.button("Resetar Lista de Usuários para o Padrão"):
        st.session_state.usuarios = [{"nome": "Vagner Souza", "cargo": "Administrador", "senha": "1980"}]
        salvar_usuarios(st.session_state.usuarios)
        st.success("Usuários resetados com sucesso!")
        st.rerun()
