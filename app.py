import json
import os
import shutil
from datetime import datetime, timezone, timedelta
import pandas as pd
import streamlit as st
import urllib.parse
import re
import streamlit.components.v1 as components

try:
    import cv2
    import numpy as np
    OPENCV_DISPONIVEL = True
except ImportError:
    OPENCV_DISPONIVEL = False


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Premium Wines - Galpão",
    page_icon="imagem premium.jpeg",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #F8F9FA 0%, #E9ECEF 100%);
        color: #1A1A1A;
        font-family: 'Poppins', sans-serif;
        overscroll-behavior-y: none;
    }

    [data-testid="stSidebar"] {
        display: none;
    }

    footer {
        visibility: hidden;
    }

    #MainMenu {
        visibility: hidden;
    }

    [data-testid="stStatusWidget"] {
        display: none;
    }

    label {
        color: #7A1C2E !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
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

    .stButton button {
        background-color: #7A1C2E !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 10px 16px !important;
        width: 100%;
        white-space: pre-wrap;
    }

    .foto-vinho {
        border-radius: 12px;
        border: 1px solid #E9ECEF;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# ARQUIVOS E PASTAS
# ============================================================

NOME_ARQUIVO = "estoque_galpao_pro.json"
ARQUIVO_USUARIOS = "usuarios_galpao.json"
ARQUIVO_LOGS = "logs_auditoria.json"
ARQUIVO_PEDIDOS = "pedidos_matriz.json"

PASTA_BACKUP = "backups_estoque"
PASTA_FOTOS = "fotos_vinhos"

SENHA_DEV = "1980"
SENHA_DIVERGENCIA = "2026"

os.makedirs(PASTA_BACKUP, exist_ok=True)
os.makedirs(PASTA_FOTOS, exist_ok=True)


# ============================================================
# LISTAS
# ============================================================

LISTA_CORREDORES = [
    f"Corredor {i:02d}"
    for i in range(1, 26)
]

LISTA_LOCAIS_TIPO = [
    "Pallet",
    "Prateleira"
]

LISTA_NUMEROS_LOCAL = [
    f"Item {i:02d}"
    for i in range(1, 26)
]

LISTA_LADOS = [
    "Direito",
    "Esquerdo",
    "Centro / Único"
]

OPCOES_CAIXA = [
    "Caixa com 12 garrafas",
    "Caixa com 6 garrafas",
    "Caixa com 3 garrafas",
    "Caixa com 2 garrafas",
    "Garrafa Avulsa (1 un)",
    "Outra quantidade"
]

TIPOS_VINHO = [
    "Tinto",
    "Branco",
    "Rosé",
    "Espumante",
    "Fortificado"
]


# ============================================================
# FUNÇÕES DE DATA / HORA
# ============================================================

def obter_horario_brasilia():
    fuso_brasilia = timezone(timedelta(hours=-3))
    return datetime.now(fuso_brasilia)


def obter_saudacao():
    hora = obter_horario_brasilia().hour
    if 0 <= hora < 12:
        return "Bom dia"
    elif 12 <= hora < 18:
        return "Boa tarde"
    else:
        return "Boa noite"


# ============================================================
# FUNÇÕES DE BACKUP
# ============================================================

def realizar_backup(nome):
    if os.path.exists(nome):
        try:
            ts = obter_horario_brasilia().strftime("%Y%m%d_%H%M%S")
            shutil.copy(
                nome,
                os.path.join(
                    PASTA_BACKUP,
                    f"backup_{ts}_{os.path.basename(nome)}"
                )
            )
        except Exception:
            pass


# ============================================================
# FUNÇÕES DE FOTO
# ============================================================

def nome_seguro_arquivo(nome):
    nome = re.sub(r"[^a-zA-Z0-9_-]", "_", nome)
    nome = re.sub(r"_+", "_", nome)
    return nome.strip("_") or "vinho"


def salvar_foto_vinho(arquivo, nome_vinho):
    if arquivo is None:
        return ""
    try:
        extensao = os.path.splitext(arquivo.name)[1].lower()
        if extensao not in [".jpg", ".jpeg", ".png", ".webp"]:
            return ""

        nome_seguro = nome_seguro_arquivo(nome_vinho)
        timestamp = obter_horario_brasilia().strftime("%Y%m%d_%H%M%S_%f")
        nome_arquivo = f"{nome_seguro}_{timestamp}{extensao}"
        caminho = os.path.join(PASTA_FOTOS, nome_arquivo)

        with open(caminho, "wb") as f:
            f.write(arquivo.getbuffer())

        return caminho
    except Exception:
        return ""


def excluir_foto(caminho):
    if caminho and os.path.exists(caminho):
        try:
            os.remove(caminho)
        except Exception:
            pass


def foto_existe(vinho):
    caminho = vinho.get("foto", "")
    return bool(caminho and os.path.exists(caminho))


# ============================================================
# ESTOQUE
# ============================================================

def carregar_dados():
    estoque = []
    if os.path.exists(NOME_ARQUIVO):
        try:
            with open(NOME_ARQUIVO, "r", encoding="utf-8") as f:
                estoque = json.load(f)
        except Exception:
            estoque = []

    if not estoque:
        estoque = [
            {
                "nome": "Campana Merlot",
                "tipo": "Tinto",
                "safra": "2024",
                "localizacao": "Corredor 01 - Pallet Item 01",
                "lado": "Direito",
                "caixa": "Caixa com 12 garrafas",
                "codigo_barras": "7891008116632",
                "foto": ""
            }
        ]

    for vinho in estoque:
        vinho.setdefault("nome", "")
        vinho.setdefault("tipo", "Tinto")
        vinho.setdefault("safra", "")
        vinho.setdefault("localizacao", "Corredor 01 - Pallet Item 01")
        vinho.setdefault("lado", "Centro / Único")
        vinho.setdefault("caixa", "Caixa com 12 garrafas")
        vinho.setdefault("codigo_barras", "")
        vinho.setdefault("foto", "")

    return sorted(estoque, key=lambda x: x.get("nome", "").lower())


def salvar_dados(estoque):
    estoque_ordenado = sorted(estoque, key=lambda x: x.get("nome", "").lower())
    with open(NOME_ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(estoque_ordenado, f, ensure_ascii=False, indent=4)
    realizar_backup(NOME_ARQUIVO)
    st.session_state.estoque = estoque_ordenado


# ============================================================
# SINCRONIZAÇÃO ESTOQUE / PEDIDOS
# ============================================================

def sincronizar_estoque_com_pedidos(pedidos, estoque):
    nomes_existentes = {v["nome"].lower() for v in estoque}
    alterado = False

    for p in pedidos:
        for item in p.get("itens", []):
            nome_item = item.get("nome", "").strip()
            if nome_item and nome_item.lower() not in nomes_existentes:
                novo_v = {
                    "nome": nome_item.title(),
                    "safra": item.get("safra", ""),
                    "tipo": "Tinto",
                    "localizacao": "Corredor 01 - Pallet Item 01",
                    "lado": "Centro / Único",
                    "caixa": "Caixa com 12 garrafas",
                    "codigo_barras": "",
                    "foto": ""
                }
                estoque.append(novo_v)
                nomes_existentes.add(nome_item.lower())
                alterado = True

    if alterado:
        salvar_dados(estoque)


# ============================================================
# USUÁRIOS
# ============================================================

def carregar_usuarios():
    if os.path.exists(ARQUIVO_USUARIOS):
        try:
            with open(ARQUIVO_USUARIOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return [
        {
            "nome": "Vagner Souza",
            "cargo": "Administrador",
            "senha": "1980"
        }
    ]


def salvar_usuarios(usuarios):
    with open(ARQUIVO_USUARIOS, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, ensure_ascii=False, indent=4)


# ============================================================
# LOGS
# ============================================================

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
    logs.insert(
        0,
        {
            "data_hora": obter_horario_brasilia().strftime("%d/%m/%Y %H:%M:%S"),
            "usuario": usuario,
            "acao": acao,
            "detalhes": detalhes
        }
    )
    with open(ARQUIVO_LOGS, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)


# ============================================================
# PEDIDOS
# ============================================================

def carregar_pedidos():
    pedidos = []
    if os.path.exists(ARQUIVO_PEDIDOS):
        try:
            with open(ARQUIVO_PEDIDOS, "r", encoding="utf-8") as f:
                pedidos = json.load(f)
        except Exception:
            pass

    for p in pedidos:
        if "itens" in p:
            for item in p["itens"]:
                item.setdefault("qtd_separada", 0)
                item.setdefault("divergencia", 0)
                item.setdefault("autorizado_divergencia", False)
                item.setdefault("separado", False)

    return pedidos


def salvar_pedidos(pedidos):
    with open(ARQUIVO_PEDIDOS, "w", encoding="utf-8") as f:
        json.dump(pedidos, f, ensure_ascii=False, indent=4)


# ============================================================
# INTERPRETAÇÃO DE PEDIDOS
# ============================================================

def interpretar_linha_pedido(texto_linha):
    texto = texto_linha.strip()
    safra = ""
    quantidade = 1

    anos = re.findall(r"\b(20\d{2})\b", texto)
    if anos:
        safra = anos[0]
        texto_limpo = texto.replace(safra, "")
    else:
        texto_limpo = texto

    match_qtd = re.search(r"(?:/|\bcaixas?|\bqt[d]?\.?)\s*(\d+)", texto_limpo, re.IGNORECASE)
    if match_qtd:
        quantidade = int(match_qtd.group(1))
        texto_limpo = texto_limpo.replace(match_qtd.group(0), "")
    else:
        numeros_soltos = re.findall(r"\b(\d+)\b", texto_limpo)
        if numeros_soltos:
            quantidade = int(numeros_soltos[-1])
            texto_limpo = texto_limpo.replace(numeros_soltos[-1], "")

    texto_limpo = re.sub(r"\bcaixas?\b", "", texto_limpo, flags=re.IGNORECASE)
    nome = re.sub(r"[/\|\-\–]+", "", texto_limpo).strip().title()

    return {
        "nome": nome,
        "safra": safra,
        "quantidade": quantidade,
        "separado": False,
        "qtd_separada": 0,
        "divergencia": 0,
        "autorizado_divergencia": False
    }


def extrair_pedidos_de_arquivo(arq):
    itens = []
    ext = arq.name.split(".")[-1].lower()
    try:
        if ext in ["xlsx", "xls"]:
            df = pd.read_excel(arq)
            for _, row in df.iterrows():
                nome_bruto = str(row.get("Nome", row.iloc[0] if len(row) > 0 else "")).strip()
                if nome_bruto and nome_bruto != "Nan":
                    safra_col = str(row.get("Safra", row.iloc[1] if len(row) > 1 else "")).strip()
                    qtd_col = row.get("Quantidade", row.iloc[2] if len(row) > 2 else 1)
                    try:
                        qtd = int(qtd_col) if pd.notnull(qtd_col) else 1
                    except Exception:
                        qtd = 1

                    itens.append({
                        "nome": nome_bruto.title(),
                        "safra": safra_col if safra_col != "Nan" else "",
                        "quantidade": qtd,
                        "separado": False,
                        "qtd_separada": 0,
                        "divergencia": 0,
                        "autorizado_divergencia": False
                    })
        elif ext == "txt":
            linhas = [l.strip() for l in arq.getvalue().decode("utf-8").split("\n") if l.strip()]
            for l in linhas:
                itens.append(interpretar_linha_pedido(l))
    except Exception:
        pass
    return itens


# ============================================================
# LEITOR DE CÓDIGO DE BARRAS
# ============================================================

def componente_leitor_barcode(chave_sessao):
    html_code = f"""
    <div style="
        text-align: center;
        background: #FFF;
        padding: 10px;
        border-radius: 12px;
        border: 1px solid #E9ECEF;
    ">
        <div id="reader_{chave_sessao}" style="
            width: 100%;
            max-width: 350px;
            margin: auto;
            border-radius: 8px;
            overflow: hidden;
        "></div>
        <p id="resultado_{chave_sessao}" style="
            font-weight: bold;
            color: #7A1C2E;
            margin-top: 8px;
            font-size: 0.9rem;
        "></p>
    </div>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <script>
    function onScanSuccess(decodedText, decodedResult) {{
        document.getElementById("resultado_{chave_sessao}").innerText = "✅ Lido: " + decodedText;
        const url = new URL(window.parent.location.href);
        url.searchParams.set('scanned_{chave_sessao}', decodedText);
        window.parent.history.replaceState({{}}, '', url);
        if (window.html5QrCode_{chave_sessao}) {{
            window.html5QrCode_{chave_sessao}.stop().catch(err => {{}});
        }}
    }}
    try {{
        const html5QrCode = new Html5Qrcode("reader_{chave_sessao}");
        window.html5QrCode_{chave_sessao} = html5QrCode;
        html5QrCode.start(
            {{ facingMode: "environment" }},
            {{ fps: 10, qrbox: {{ width: 250, height: 120 }} }},
            onScanSuccess
        ).catch(err => {{}});
    }} catch (e) {{}}
    </script>
    """
    components.html(html_code, height=260)


# ============================================================
# SESSION STATE
# ============================================================

if "usuarios" not in st.session_state:
    st.session_state.usuarios = carregar_usuarios()

st.session_state.estoque = carregar_dados()
st.session_state.pedidos = carregar_pedidos()

sincronizar_estoque_com_pedidos(st.session_state.pedidos, st.session_state.estoque)

if "menu_atual" not in st.session_state:
    st.session_state.menu_atual = "🏠 Home"

if "termo_busca" not in st.session_state:
    st.session_state.termo_busca = ""


# ============================================================
# QUERY PARAMS - LEITOR
# ============================================================

qp = st.query_params

for key, val in list(qp.items()):
    if key.startswith("scanned_"):
        sess_key = key.replace("scanned_", "")
        valor_limpo = str(val).strip()
        if sess_key == "checkout_camera":
            st.session_state.codigo_bipado_checkout = valor_limpo
        del st.query_params[key]
        st.rerun()


# ============================================================
# LOGIN
# ============================================================

user_url = qp.get("user", None)
cargo_url = qp.get("cargo", "Operador")

if "usuario_logado" not in st.session_state or st.session_state.usuario_logado is None:
    if user_url:
        st.session_state.usuario_logado = {
            "nome": user_url,
            "cargo": cargo_url
        }
    else:
        st.session_state.usuario_logado = None

if st.session_state.usuario_logado is None:
    st.write("")
    _, cc, _ = st.columns([1, 1.3, 1])

    with cc:
        if os.path.exists("imagem premium.jpeg"):
            _, ci, _ = st.columns([1, 1.8, 1])
            with ci:
                st.image("imagem premium.jpeg", width=190)

        st.markdown(
            """
            <h1 style="
                text-align: center;
                color: #7A1C2E;
                font-size: 1.6rem;
            ">
                SEPARAÇÃO DE VINHO GALPÃO
            </h1>
            """,
            unsafe_allow_html=True
        )

        tab1, tab2, tab3 = st.tabs(["🔑 Entrar", "👤 Criar Conta", "⚙️ Dev"])

        with tab1:
            with st.form("l_form"):
                u = st.text_input("Usuário").strip().title()
                p = st.text_input("Senha", type="password").strip()

                if st.form_submit_button("ENTRAR", use_container_width=True):
                    user = next(
                        (x for x in st.session_state.usuarios if x["nome"].lower() == u.lower() and x["senha"] == p),
                        None
                    )
                    if user:
                        st.session_state.usuario_logado = user
                        st.query_params["user"] = user["nome"]
                        st.query_params["cargo"] = user.get("cargo", "Operador")
                        st.rerun()
                    else:
                        st.error("Dados incorretos.")

        with tab2:
            with st.form("c_form"):
                n = st.text_input("Nome").strip().title()
                s = st.text_input("Senha", type="password").strip()

                if st.form_submit_button("CADASTRAR", use_container_width=True):
                    if n and s:
                        novo = {"nome": n, "cargo": "Operador", "senha": s}
                        st.session_state.usuarios.append(novo)
                        salvar_usuarios(st.session_state.usuarios)
                        st.session_state.usuario_logado = novo
                        st.query_params["user"] = novo["nome"]
                        st.query_params["cargo"] = novo["cargo"]
                        st.rerun()
                    else:
                        st.error("Preencha tudo.")

        with tab3:
            with st.form("d_form"):
                sp = st.text_input("Senha Mestra", type="password")

                if st.form_submit_button("DEV", use_container_width=True):
                    if sp == SENHA_DEV:
                        dev_user = {"nome": "Dev", "cargo": "Desenvolvedor"}
                        st.session_state.usuario_logado = dev_user
                        st.query_params["user"] = "Dev"
                        st.query_params["cargo"] = "Desenvolvedor"
                        st.rerun()
                    else:
                        st.error("Senha incorreta.")

    st.stop()


# ============================================================
# TOPO
# ============================================================

ct1, ct2, ct3 = st.columns([3, 2, 1])

with ct1:
    st.markdown(
        f"""
        🍷 <b>PREMIUM WINES</b> | Usuário: {st.session_state.usuario_logado['nome']} ({st.session_state.usuario_logado.get('cargo', 'Operador')})
        """,
        unsafe_allow_html=True
    )

with ct2:
    if st.session_state.menu_atual != "🏠 Home":
        if st.button("⬅️ Voltar ao Menu", use_container_width=True):
            st.session_state.menu_atual = "🏠 Home"
            st.rerun()

with ct3:
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.usuario_logado = None
        st.query_params.clear()
        st.session_state.menu_atual = "🏠 Home"
        st.rerun()

st.markdown("---")


# ============================================================
# HOME
# ============================================================

if st.session_state.menu_atual == "🏠 Home":
    st.markdown(f'<p style="text-align: center; color: #666; margin-bottom: 0px;">{obter_saudacao()},</p>', unsafe_allow_html=True)
    st.markdown(f'<h1 style="text-align: center; color: #7A1C2E; margin-top: 0px;">{st.session_state.usuario_logado["nome"]}! 👋</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #444; font-size: 0.95rem; margin-bottom: 25px;">Separação de Vinho Galpão - Escolha a opção abaixo:</p>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📦 Checkout de Expedição", use_container_width=True):
            st.session_state.menu_atual = "PedidosMatriz"
            st.rerun()
    with c2:
        if st.button("🏢 Painel da Matriz", use_container_width=True):
            st.session_state.menu_atual = "PainelMatriz"
            st.rerun()
    with c3:
        if st.button("🔍 Buscar / Filtros", use_container_width=True):
            st.session_state.menu_atual = "Filtros"
            st.rerun()

    st.write("")
    c4, c5, c6 = st.columns(3)
    with c4:
        if st.button("🗺️ Mapa de Separação", use_container_width=True):
            st.session_state.menu_atual = "MapaSeparacao"
            st.rerun()
    with c5:
        if st.button("🍷 Estoque Completo", use_container_width=True):
            st.session_state.menu_atual = "Estoque"
            st.rerun()
    with c6:
        if st.button("➕ Cadastrar Vinho", use_container_width=True):
            st.session_state.menu_atual = "Cadastrar"
            st.rerun()

    st.write("")
    c7, c8, c9 = st.columns(3)
    with c7:
        if st.button("✏️ Editar Vinho", use_container_width=True):
            st.session_state.menu_atual = "Editar"
            st.rerun()
    with c8:
        if st.button("📋 Histórico", use_container_width=True):
            st.session_state.menu_atual = "Historico"
            st.rerun()
    with c9:
        if st.session_state.usuario_logado.get("cargo") == "Desenvolvedor":
            if st.button("⚙️ Gerenciar Contas", use_container_width=True):
                st.session_state.menu_atual = "GerenciarUsuarios"
                st.rerun()


# ============================================================
# CHECKOUT DE EXPEDIÇÃO / PEDIDOS MATRIZ
# ============================================================

elif st.session_state.menu_atual == "PedidosMatriz":
    st.subheader("📦 Checkout e Pedidos da Matriz")
    
    # Importação de novos pedidos
    with st.expander("📥 Importar Novo Pedido / Lista (Excel ou TXT)"):
        arq_sub = st.file_uploader("Selecione o arquivo", type=["xlsx", "xls", "txt"])
        if arq_sub and st.button("Processar e Salvar Pedido"):
            itens_extraidos = extrair_pedidos_de_arquivo(arq_sub)
            if itens_extraidos:
                novo_pedido = {
                    "id": len(st.session_state.pedidos) + 1,
                    "data": obter_horario_brasilia().strftime("%d/%m/%Y %H:%M"),
                    "status": "Pendente",
                    "itens": itens_extraidos
                }
                st.session_state.pedidos.append(novo_pedido)
                salvar_pedidos(st.session_state.pedidos)
                sincronizar_estoque_com_pedidos(st.session_state.pedidos, st.session_state.estoque)
                registrar_log(st.session_state.usuario_logado["nome"], "Importar Pedido", f"Pedido #{novo_pedido['id']}")
                st.success("Pedido importado com sucesso!")
                st.rerun()
            else:
                st.error("Não foi possível extrair itens do arquivo.")

    if not st.session_state.pedidos:
        st.info("Nenhum pedido ativo no momento.")
    else:
        for idx, pedido in enumerate(st.session_state.pedidos):
            with st.container():
                st.markdown(
                    f"""
                    <div style="background:#FFF; padding:15px; border-radius:12px; border:1px solid #E9ECEF; margin-bottom:15px;">
                        <h4>Pedido #{pedido.get('id', idx+1)} - Status: {pedido.get('status', 'Pendente')}</h4>
                        <p>Data: {pedido.get('data', 'N/D')}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                for i_idx, item in enumerate(pedido.get("itens", [])):
                    c_i1, c_i2, c_i3 = st.columns([3, 1, 1])
                    with c_i1:
                        st.markdown(f"**{item.get('nome')}** (Safra: {item.get('safra', 'N/D')}) | Qtd Pedida: **{item.get('quantidade')}**")
                    with c_i2:
                        sep = st.checkbox("Separado", value=item.get("separado", False), key=f"sep_{idx}_{i_idx}")
                        if sep != item.get("separado", False):
                            item["separado"] = sep
                            salvar_pedidos(st.session_state.pedidos)
                    with c_i3:
                        qtd_sep = st.number_input("Qtd Sep.", value=int(item.get("qtd_separada", item.get("quantidade"))), min_value=0, key=f"qtd_s_{idx}_{i_idx}")
                        if qtd_sep != item.get("qtd_separada", 0):
                            item["qtd_separada"] = qtd_sep
                            salvar_pedidos(st.session_state.pedidos)


# ============================================================
# PAINEL DA MATRIZ
# ============================================================

elif st.session_state.menu_atual == "PainelMatriz":
    st.subheader("🏢 Painel da Matriz - Acompanhamento de Pedidos")
    st.markdown("""
        Aqui a Matriz visualiza em tempo real todos os pedidos salvos, finalizados 
        e as divergências de quantidade registradas pelo galpão.
    """)

    if not st.session_state.pedidos:
        st.info("Nenhum pedido registrado no sistema.")
    else:
        for p in st.session_state.pedidos:
            status_col = (
                "#2E7D32"
                if p.get("status") == "Concluído / Expedido"
                else "#7A1C2E"
            )

            st.markdown(
                f"""
                <div style="
                    background: #FFF;
                    padding: 15px;
                    border-radius: 12px;
                    border: 1px solid #E9ECEF;
                    margin-bottom: 15px;
                    box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.03);
                ">
                    <h4 style="color: {status_col}; margin-top: 0px;">
                        Pedido / Mapa Nº {p.get('id', 'N/D')} - Status: {p.get('status', 'Pendente')}
                    </h4>
                    <p><b>Data:</b> {p.get('data', 'N/D')}</p>
                </div>
                """,
                unsafe_allow_html=True
            )


# ============================================================
# FILTROS / BUSCA
# ============================================================

elif st.session_state.menu_atual == "Filtros":
    st.subheader("🔍 Buscar e Filtrar Vinhos no Galpão")
    termo = st.text_input("Digite o nome do vinho ou código de barras:", value=st.session_state.termo_busca)
    st.session_state.termo_busca = termo

    resultados = [
        v for v in st.session_state.estoque
        if termo.lower() in v.get("nome", "").lower() or termo in v.get("codigo_barras", "")
    ] if termo else st.session_state.estoque

    st.write(f"Encontrados: {len(resultados)} vinhos.")
    for vinho in resultados:
        with st.container():
            st.markdown(
                f"""
                <div class="wine-card">
                    <div class="wine-title">{vinho.get('nome')} ({vinho.get('safra', 'NV')})</div>
                    <p><b>Tipo:</b> {vinho.get('tipo')} | <b>Local:</b> {vinho.get('localizacao')} ({vinho.get('lado')})</p>
                    <p><b>Caixa:</b> {vinho.get('caixa')} | <b>Código de Barras:</b> {vinho.get('codigo_barras', 'N/D')}</p>
                </div>
                """,
                unsafe_allow_html=True
            )


# ============================================================
# MAPA DE SEPARAÇÃO
# ============================================================

elif st.session_state.menu_atual == "MapaSeparacao":
    st.subheader("🗺️ Mapa de Separação por Corredor")
    corredor_escolhido = st.selectbox("Selecione o Corredor:", LISTA_CORREDORES)
    
    vinhos_corredor = [
        v for v in st.session_state.estoque
        if corredor_escolhido.lower() in v.get("localizacao", "").lower()
    ]
    
    st.write(f"Vinhos no {corredor_escolhido}: {len(vinhos_corredor)}")
    for vinho in vinhos_corredor:
        st.markdown(
            f"""
            <div class="wine-card">
                <div class="wine-title">{vinho.get('nome')} ({vinho.get('safra', 'NV')})</div>
                <p><b>Localização:</b> {vinho.get('localizacao')} - Lado: {vinho.get('lado')}</p>
            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# ESTOQUE COMPLETO
# ============================================================

elif st.session_state.menu_atual == "Estoque":
    st.subheader("🍷 Estoque Completo do Galpão")
    if not st.session_state.estoque:
        st.info("Estoque vazio.")
    else:
        df_est = pd.DataFrame(st.session_state.estoque)
        st.dataframe(df_est, use_container_width=True)


# ============================================================
# CADASTRAR VINHO
# ============================================================

elif st.session_state.menu_atual == "Cadastrar":
    st.subheader("➕ Cadastrar Novo Vinho no Estoque")
    with st.form("form_cad"):
        nome_c = st.text_input("Nome do Vinho").strip().title()
        tipo_c = st.selectbox("Tipo", TIPOS_VINHO)
        safra_c = st.text_input("Safra (ex: 2023)").strip()
        corredor_c = st.selectbox("Corredor", LISTA_CORREDORES)
        tipo_local_c = st.selectbox("Tipo de Local", LISTA_LOCAIS_TIPO)
        num_local_c = st.selectbox("Número do Local", LISTA_NUMEROS_LOCAL)
        lado_c = st.selectbox("Lado", LISTA_LADOS)
        caixa_c = st.selectbox("Embalagem", OPCOES_CAIXA)
        codigo_c = st.text_input("Código de Barras").strip()
        foto_c = st.file_uploader("Foto do Vinho", type=["jpg", "jpeg", "png", "webp"])

        if st.form_submit_button("Salvar Cadastro"):
            if nome_c:
                caminho_foto = salvar_foto_vinho(foto_c, nome_c)
                novo_vinho = {
                    "nome": nome_c,
                    "tipo": tipo_c,
                    "safra": safra_c,
                    "localizacao": f"{corredor_c} - {tipo_local_c} {num_local_c}",
                    "lado": lado_c,
                    "caixa": caixa_c,
                    "codigo_barras": codigo_c,
                    "foto": caminho_foto
                }
                st.session_state.estoque.append(novo_vinho)
                salvar_dados(st.session_state.estoque)
                registrar_log(st.session_state.usuario_logado["nome"], "Cadastrar Vinho", nome_c)
                st.success("Vinho cadastrado com sucesso!")
                st.rerun()
            else:
                st.error("Informe o nome do vinho.")


# ============================================================
# EDITAR VINHO
# ============================================================

elif st.session_state.menu_atual == "Editar":
    st.subheader("✏️ Editar ou Excluir Vinho")
    nomes_vinhos = [v["nome"] for v in st.session_state.estoque]
    if not nomes_vinhos:
        st.info("Nenhum vinho para editar.")
    else:
        vinho_selecionado = st.selectbox("Selecione o Vinho", nomes_vinhos)
        v_obj = next((v for v in st.session_state.estoque if v["nome"] == vinho_selecionado), None)

        if v_obj:
            with st.form("form_edit"):
                novo_nome = st.text_input("Nome", value=v_obj.get("nome", "")).strip().title()
                nova_safra = st.text_input("Safra", value=v_obj.get("safra", "")).strip()
                novo_codigo = st.text_input("Código de Barras", value=v_obj.get("codigo_barras", "")).strip()

                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    if st.form_submit_button("Salvar Alterações"):
                        v_obj["nome"] = novo_nome
                        v_obj["safra"] = nova_safra
                        v_obj["codigo_barras"] = novo_codigo
                        salvar_dados(st.session_state.estoque)
                        registrar_log(st.session_state.usuario_logado["nome"], "Editar Vinho", novo_nome)
                        st.success("Alterações salvas!")
                        st.rerun()
                with col_e2:
                    if st.form_submit_button("🗑️ Excluir Vinho"):
                        excluir_foto(v_obj.get("foto", ""))
                        st.session_state.estoque.remove(v_obj)
                        salvar_dados(st.session_state.estoque)
                        registrar_log(st.session_state.usuario_logado["nome"], "Excluir Vinho", v_obj.get("nome"))
                        st.success("Vinho excluído!")
                        st.rerun()


# ============================================================
# HISTÓRICO DE LOGS
# ============================================================

elif st.session_state.menu_atual == "Historico":
    st.subheader("📋 Histórico de Auditoria e Ações")
    logs = carregar_logs()
    if not logs:
        st.info("Nenhum registro no histórico.")
    else:
        for l in logs:
            st.markdown(
                f"""
                <div style="background:#FFF; padding:10px; border-radius:8px; border:1px solid #E9ECEF; margin-bottom:8px; font-size:0.9rem;">
                    <b>{l.get('data_hora')}</b> - <b>{l.get('usuario')}</b> executou <b>{l.get('acao')}</b>: {l.get('detalhes')}
                </div>
                """,
                unsafe_allow_html=True
            )


# ============================================================
# GERENCIAR USUÁRIOS (DEV)
# ============================================================

elif st.session_state.menu_atual == "GerenciarUsuarios":
    st.subheader("⚙️ Gerenciamento de Contas e Usuários")
    if st.session_state.usuario_logado.get("cargo") != "Desenvolvedor":
        st.error("Acesso restrito a Desenvolvedores.")
    else:
        for idx, u_acc in enumerate(st.session_state.usuarios):
            st.write(f"👤 **{u_acc.get('nome')}** ({u_acc.get('cargo', 'Operador')})")
