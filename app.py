import json
import os
import shutil
from datetime import datetime, timezone, timedelta
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import urllib.parse
import openpyxl
from docx import Document

try:
    import cv2
    import numpy as np
    OPENCV_DISPONIVEL = True
except ImportError:
    OPENCV_DISPONIVEL = False

st.set_page_config(
    page_title="Premium Wines - Galpão",
    page_icon="imagem premium.jpeg",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(135deg, #F8F9FA 0%, #E9ECEF 100%); color: #1A1A1A; font-family: 'Poppins', sans-serif; overscroll-behavior-y: none; }
    [data-testid="stSidebar"] { display: none; }
    
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    [data-testid="stStatusWidget"] {display: none;}
    
    label { color: #7A1C2E !important; font-weight: 700 !important; font-size: 0.95rem !important; }
    .wine-card { background-color: #FFFFFF; color: #1A1A1A; border-radius: 14px; padding: 16px; margin-bottom: 12px; border: 1px solid #E9ECEF; box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.03); }
    .wine-title { color: #7A1C2E; font-size: 1.1rem; font-weight: 700; margin-bottom: 4px; }
    .badge-pallet-grande { background-color: #7A1C2E; color: #FFFFFF; padding: 6px 14px; border-radius: 8px; font-weight: 700; font-size: 1rem; display: inline-block; }
    .stButton button { background-color: #7A1C2E !important; color: #FFFFFF !important; border-radius: 12px !important; font-weight: 600 !important; border: none !important; padding: 10px 16px !important; width: 100%; white-space: pre-wrap; }
    </style>
""", unsafe_allow_html=True,
)

NOME_ARQUIVO = "estoque_galpao_pro.json"
ARQUIVO_USUARIOS = "usuarios_galpao.json"
ARQUIVO_LOGS = "logs_auditoria.json"
PASTA_BACKUP = "backups_estoque"
PASTA_FOTOS = "fotos_vinhos"
SENHA_DEV = "1980"

if not os.path.exists(PASTA_BACKUP):
    os.makedirs(PASTA_BACKUP)
if not os.path.exists(PASTA_FOTOS):
    os.makedirs(PASTA_FOTOS)

LISTA_CORREDORES = [f"Corredor {i:02d}" for i in range(1, 26)]
LISTA_LOCAIS_TIPO = ["Pallet", "Prateleira"]
LISTA_NUMEROS_LOCAL = [f"Item {i:02d}" for i in range(1, 26)]
LISTA_LADOS = ["Direito", "Esquerdo", "Centro / Único"]
OPCOES_CAIXA = ["Caixa com 12 garrafas", "Caixa com 6 garrafas", "Caixa com 3 garrafas", "Caixa com 2 garrafas", "Garrafa Avulsa (1 un)", "Outra quantidade"]

def obter_saudacao():
    fuso = timezone(timedelta(hours=-3))
    hora = datetime.now(fuso).hour
    if 0 <= hora < 12: return "Bom dia"
    elif 12 <= hora < 18: return "Boa tarde"
    else: return "Boa noite"

def realizar_backup(nome):
    if os.path.exists(nome):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy(nome, os.path.join(PASTA_BACKUP, f"backup_{ts}_{nome}"))

def carregar_dados():
    if os.path.exists(NOME_ARQUIVO):
        try:
            with open(NOME_ARQUIVO, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return [{"nome": "Château Margaux", "tipo": "Tinto", "safra": "2015", "localizacao": "Corredor 01 - Pallet Item 01", "lado": "Direito", "caixa": "Caixa com 12 garrafas", "foto": ""}]

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

def extrair_linhas_de_arquivo(arq):
    linhas = []
    ext = arq.name.split('.')[-1].lower()
    try:
        if ext in ['xlsx', 'xls']:
            df = pd.read_excel(arq)
            for c in df.columns:
                for v in df[c].dropna():
                    if str(v).strip(): linhas.append(str(v).strip().title())
        elif ext == 'docx':
            doc = Document(arq)
            for p in doc.paragraphs:
                if p.text.strip(): linhas.append(p.text.strip().title())
            for t in doc.tables:
                for row in t.rows:
                    for cell in row.cells:
                        if cell.text.strip(): linhas.append(cell.text.strip().title())
        elif ext == 'txt':
            linhas = [l.strip().title() for l in arq.getvalue().decode("utf-8").split("\n") if l.strip()]
    except: pass
    return linhas

if "estoque" not in st.session_state: st.session_state.estoque = carregar_dados()
if "usuarios" not in st.session_state: st.session_state.usuarios = carregar_usuarios()
if "menu_atual" not in st.session_state: st.session_state.menu_atual = "🏠 Home"
if "termo_busca" not in st.session_state: st.session_state.termo_busca = ""

qp = st.query_params
user_url = qp.get("user", None)
cargo_url = qp.get("cargo", "Operador")

if "usuario_logado" not in st.session_state or st.session_state.usuario_logado is None:
    if user_url: st.session_state.usuario_logado = {"nome": user_url, "cargo": cargo_url}
    else: st.session_state.usuario_logado = None

if st.session_state.usuario_logado is None:
    st.write("")
    _, cc, _ = st.columns([1, 1.3, 1])
    with cc:
        if os.path.exists("imagem premium.jpeg"):
            _, ci, _ = st.columns([1, 1.8, 1])
            with ci: st.image("imagem premium.jpeg", width=190)
        st.markdown("<h1 style='text-align: center; color: #7A1C2E; font-size: 1.6rem;'>PREMIUM WINES GALPÃO</h1>", unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["🔑 Entrar", "👤 Criar Conta", "⚙️ Dev"])
        with tab1:
            with st.form("l_form"):
                u = st.text_input("Usuário").strip().title()
                p = st.text_input("Senha", type="password").strip()
                if st.form_submit_button("ENTRAR", use_container_width=True):
                    user = next((x for x in st.session_state.usuarios if x['nome'].lower() == u.lower() and x['senha'] == p), None)
                    if user:
                        st.session_state.usuario_logado = user
                        st.query_params["user"] = user['nome']
                        st.query_params["cargo"] = user.get('cargo', 'Operador')
                        st.rerun()
                    else: st.error("Dados incorretos.")
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
                        st.query_params["user"] = novo['nome']
                        st.query_params["cargo"] = novo['cargo']
                        st.rerun()
                    else: st.error("Preencha tudo.")
        with tab3:
            with st.form("d_form"):
                sp = st.text_input("Senha Mestra", type="password")
                if st.form_submit_button("DEV", use_container_width=True):
                    if sp == SENHA_DEV:
                        st.session_state.usuario_logado = {"nome": "Dev", "cargo": "Desenvolvedor"}
                        st.query_params["user"] = "Dev"
                        st.query_params["cargo"] = "Desenvolvedor"
                        st.rerun()
                    else: st.error("Senha incorreta.")
    st.stop()

ct1, ct2, ct3 = st.columns([3, 2, 1])
with ct1: st.markdown(f"🍷 <b>PREMIUM WINES</b> | Usuário: {st.session_state.usuario_logado['nome']}", unsafe_allow_html=True)
with ct2:
    if st.session_state.menu_atual != "🏠 Home":
        if st.button("⬅️ Voltar ao Menu", use_container_width=True): st.session_state.menu_atual = "🏠 Home"; st.rerun()
with ct3:
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.usuario_logado = None
        st.query_params.clear()
        st.session_state.menu_atual = "🏠 Home"
        st.rerun()

st.markdown("---")

if st.session_state.menu_atual == "🏠 Home":
    st.markdown(f"<p style='text-align: center; color: #666; margin-bottom: 0px;'>{obter_saudacao()},</p>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align: center; color: #7A1C2E; margin-top: 0px;'>{st.session_state.usuario_logado['nome']}! 👋</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #444; font-size: 0.95rem; margin-bottom: 25px;'>Escolha abaixo a opção desejada para gerenciar o galpão:</p>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🔍 Buscar / Filtros", use_container_width=True): st.session_state.menu_atual = "Filtros"; st.rerun()
    with c2:
        if st.button("🗺️ Mapa de Separação", use_container_width=True): st.session_state.menu_atual = "MapaSeparacao"; st.rerun()
    with c3:
        if st.button("🍷 Estoque Completo", use_container_width=True): st.session_state.menu_atual = "Estoque"; st.rerun()
    
    st.write("")
    c4, c5, c6 = st.columns(3)
    with c4:
        if st.button("➕ Cadastrar Vinho", use_container_width=True): st.session_state.menu_atual = "Cadastrar"; st.rerun()
    with c5:
        if st.button("📱 Gerar QR Code", use_container_width=True): st.session_state.menu_atual = "GerarQR"; st.rerun()
    with c6:
        if st.button("📋 Histórico", use_container_width=True): st.session_state.menu_atual = "Historico"; st.rerun()
    
    st.write("")
    c7, c8, c9 = st.columns(3)
    with c7:
        if st.button("📷 Escanear Local", use_container_width=True): st.session_state.menu_atual = "Scanner"; st.rerun()
    with c8:
        if st.button("✏️ Editar Vinho", use_container_width=True): st.session_state.menu_atual = "Editar"; st.rerun()
    with c9:
        if st.button("🗑️ Excluir Vinho", use_container_width=True): st.session_state.menu_atual = "Excluir"; st.rerun()
        
    if st.session_state.usuario_logado.get('cargo') == "Desenvolvedor":
        st.write("")
        if st.button("⚙️ Gerenciar Contas", use_container_width=True):
            st.session_state.menu_atual = "GerenciarUsuarios"
            st.rerun()

elif st.session_state.menu_atual == "Filtros":
    st.subheader("🔍 Busca por Local ou Nome")
    termo_digitado = st.text_input("Filtrar por nome ou corredor/pallet:", value=st.session_state.termo_busca)
    termo = termo_digitado.strip().title()
    
    tp = termo.lower() if termo else st.session_state.termo_busca.lower()
    if tp:
        res = [v for v in st.session_state.estoque if tp in v.get("nome", "").lower() or tp in v.get("localizacao", "").lower() or tp in v.get("lado", "").lower()]
        if res:
            for v in res:
                img_tag = f"<br><img src='app/static/{v.get('foto')}' width='100' style='border-radius: 8px; margin-top: 8px;'>" if v.get('foto') and os.path.exists(os.path.join(PASTA_FOTOS, v.get('foto'))) else ""
                st.markdown(f"<div class='wine-card'><div class='wine-title'>🍷 {v.get('nome')} ({v.get('safra')})</div><p>Tipo: <b>{v.get('tipo', 'N/A')}</b> | Caixa: <b>{v.get('caixa', 'N/A')}</b><br><span class='badge-pallet-grande'>📍 {v.get('localizacao')} - Lado: {v.get('lado', 'N/A')}</span>{img_tag}</p></div>", unsafe_allow_html=True)
        else:
            st.warning("Nenhum vinho encontrado para este filtro/local.")

elif st.session_state.menu_atual == "MapaSeparacao":
    st.subheader("🗺️ Mapa de Separação (Leitura de Arquivo TXT ou Excel)")
    arq = st.file_uploader("Envie o arquivo com a lista de vinhos", type=["xlsx", "xls", "txt"])
    txt_man_input = st.text_area("Ou cole a lista de vinhos manualmente aqui:")
    txt_man = txt_man_input.title() if txt_man_input else ""
    
    if st.button("Gerar Rota / Mapa"):
        linhas = extrair_linhas_de_arquivo(arq) if arq else []
        if txt_man.strip():
            linhas.extend([l.strip().title() for l in txt_man.split("\n") if l.strip()])
            
        if linhas:
            encontrados = []
            for v in st.session_state.estoque:
                nome_vinho = v.get("nome", "").lower().strip()
                if any(l.lower().strip() in nome_vinho or nome_vinho in l.lower().strip() for l in linhas if len(l.strip()) > 2):
                    if v not in encontrados:
                        encontrados.append(v)
            
            if encontrados:
                st.success(f"Foram encontrados {len(encontrados)} vinhos para separação:")
                for v in encontrados:
                    st.markdown(f"<div class='wine-card'><div class='wine-title'>🍷 {v.get('nome')} ({v.get('safra', 'N/A')})</div><p>Tipo: <b>{v.get('tipo', 'N/A')}</b> | Caixa: <b>{v.get('caixa', 'N/A')}</b><br><span class='badge-pallet-grande'>📍 {v.get('localizacao', 'N/A')} - Lado: {v.get('lado', 'N/A')}</span></p></div>", unsafe_allow_html=True)
            else:
                st.warning("Nenhum vinho do arquivo corresponde aos cadastrados no estoque. Verifique se os nomes batem com o cadastro.")
        else:
            st.error("Envie um arquivo ou digite pelo menos um nome na caixa de texto.")

elif st.session_state.menu_atual == "Scanner":
    st.subheader("📷 Escanear QR Code do Local")
    foto = st.camera_input("Capturar Foto do QR Code do Pallet/Prateleira")
    if foto and OPENCV_DISPONIVEL:
        img = cv2.imdecode(np.frombuffer(foto.getvalue(), np.uint8), cv2.IMREAD_COLOR)
        val, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
        if val:
            termo_lido = val.strip().lower()
            st.success(f"Local Identificado: {val}")
            st.markdown("### 🍷 Vinhos neste local:")
            resultados = [v for v in st.session_state.estoque if termo_lido in (str(v.get('localizacao', '')).strip().lower() + " - lado: " + str(v.get('lado', '')).strip().lower())]
            if resultados:
                for v in resultados:
                    st.markdown(f"<div class='wine-card'><div class='wine-title'>🍷 {v.get('nome')} ({v.get('safra', 'N/A')})</div><p>Tipo: <b>{v.get('tipo', 'N/A')}</b> | Caixa: <b>{v.get('caixa', 'N/A')}</b><br>📍 Local: <b>{v.get('localizacao', 'N/A')}</b> (Lado: <b>{v.get('lado', 'N/A')}</b>)</p></div>", unsafe_allow_html=True)
            else: st.warning("Nenhum vinho encontrado neste local.")
        else: st.error("QR Code não detectado. Tente novamente.")

elif st.session_state.menu_atual == "Estoque":
    st.subheader("🍷 Estoque Completo")
    for v in st.session_state.estoque:
        st.markdown(f"<div class='wine-card'><div class='wine-title'>🍷 {v.get('nome')} ({v.get('safra')})</div><p>📍 <b>{v.get('localizacao')}</b> - Lado: <b>{v.get('lado', 'N/A')}</b></p></div>", unsafe_allow_html=True)

elif st.session_state.menu_atual == "Cadastrar":
    st.subheader("➕ Cadastrar Vinho (Individual ou em Lote)")
    
    modo_cadastro = st.radio("Escolha o modo de cadastro:", ["Cadastro Individual", "Importar Lote (Excel ou TXT)"])
    
    if modo_cadastro == "Cadastro Individual":
        with st.form("cad"):
            nome = st.text_input("Nome").strip().title()
            tipo = st.selectbox("Tipo", ["Tinto", "Branco", "Rosé", "Espumante"])
            safra = st.text_input("Safra").strip()
            corredor = st.selectbox("Corredor", LISTA_CORREDORES)
            tipo_loc = st.selectbox("Tipo Local", LISTA_LOCAIS_TIPO)
            numero = st.selectbox("Número", LISTA_NUMEROS_LOCAL)
            lado = st.selectbox("Lado", LISTA_LADOS)
            caixa = st.selectbox("Caixa", OPCOES_CAIXA)
            foto_vinho = st.file_uploader("Foto da Garrafa / Rótulo (Opcional)", type=["jpg", "jpeg", "png"])
            
            if st.form_submit_button("Salvar"):
                if nome:
                    nome_foto = ""
                    if foto_vinho is not None:
                        nome_foto = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{foto_vinho.name}"
                        caminho_foto = os.path.join(PASTA_FOTOS, nome_foto)
                        with open(caminho_foto, "wb") as f:
                            f.write(foto_vinho.getbuffer())
                    
                    st.session_state.estoque.append({
                        "nome": nome, 
                        "tipo": tipo, 
                        "safra": safra, 
                        "localizacao": f"{corredor} - {tipo_loc} {numero}", 
                        "lado": lado, 
                        "caixa": caixa, 
                        "foto": nome_foto
                    })
                    salvar_dados(st.session_state.estoque)
                    registrar_log(st.session_state.usuario_logado['nome'], "Cadastrar Vinho", nome)
                    st.success("Vinho cadastrado com sucesso!")
                    st.session_state.menu_atual = "🏠 Home"
                    st.rerun()
                else:
                    st.error("Informe o nome do vinho.")
    else:
        st.info("Envie uma planilha Excel (.xlsx) com a coluna **Nome** ou um arquivo de texto (.txt) com um nome de vinho por linha.")
        arq_lote = st.file_uploader("Escolha o arquivo", type=["xlsx", "xls", "txt"])
        
        if arq_lote and st.button("Processar Importação em Lote"):
            importados = 0
            ext = arq_lote.name.split('.')[-1].lower()
            
            if ext in ['xlsx', 'xls']:
                df = pd.read_excel(arq_lote)
                for _, row in df.iterrows():
                    nome_v = str(row.get('Nome', '')).strip().title()
                    if nome_v and nome_v != 'Nan':
                        st.session_state.estoque.append({
                            "nome": nome_v,
                            "tipo": str(row.get('Tipo', 'Tinto')).strip().title(),
                            "safra": str(row.get('Safra', '')).strip(),
                            "localizacao": str(row.get('Localizacao', 'Corredor 01 - Pallet Item 01')).strip(),
                            "lado": str(row.get('Lado', 'Direito')).strip(),
                            "caixa": str(row.get('Caixa', 'Caixa com 12 garrafas')).strip(),
                            "foto": ""
                        })
                        importados += 1
                        
            elif ext == 'txt':
                linhas = [l.strip().title() for l in arq_lote.getvalue().decode("utf-8").split("\n") if l.strip()]
                for linha in linhas:
                    st.session_state.estoque.append({
                        "nome": linha,
                        "tipo": "Tinto",
                        "safra": "",
                        "localizacao": "Corredor 01 - Pallet Item 01",
                        "lado": "Direito",
                        "caixa": "Caixa com 12 garrafas",
                        "foto": ""
                    })
                    importados += 1
            
            if importados > 0:
                salvar_dados(st.session_state.estoque)
                registrar_log(st.session_state.usuario_logado['nome'], "Importação em Lote", f"{importados} vinhos importados via {ext.upper()}")
                st.success(f"{importados} vinhos importados com sucesso!")
                st.session_state.menu_atual = "🏠 Home"
                st.rerun()
            else:
                st.warning("O arquivo parece estar vazio ou sem dados válidos.")

elif st.session_state.menu_atual == "GerarQR":
    st.subheader("📱 Gerar QR Code de Localização")
    
    aba_qr1, aba_qr2 = st.tabs(["Gerar Individual", "Gerar Lote para Impressão (Vários por Página)"])
    
    with aba_qr1:
        c_corredor = st.selectbox("Corredor", LISTA_CORREDORES, key="ind_corredor")
        c_tipo = st.selectbox("Tipo de Local", LISTA_LOCAIS_TIPO, key="ind_tipo")
        c_numero = st.selectbox("Número do Item", LISTA_NUMEROS_LOCAL, key="ind_numero")
        c_lado = st.selectbox("Lado", LISTA_LADOS, key="ind_lado")
        
        local_etiqueta = f"{c_corredor} - {c_tipo} {c_numero} - Lado: {c_lado}"
        
        if st.button("Gerar Etiqueta Individual"):
            url_qr = gerar_qr_code_api(local_etiqueta)
            st.image(url_qr, width=240, caption=local_etiqueta)
            st.markdown(f"""
                <div style="margin-top: 10px;">
                    <a href="{url_qr}" target="_blank" download="qrcode_{local_etiqueta}.png" style="background-color: #7A1C2E; color: white; padding: 10px 16px; border-radius: 12px; text-decoration: none; font-weight: 600; text-align: center; display: inline-block;">📥 Baixar Imagem do QR Code</a>
                </div>
            """, unsafe_allow_html=True)

    with aba_qr2:
        st.markdown("### 🖨️ Gerador de Lote de Etiquetas")
        st.markdown("Selecione o intervalo para gerar uma página organizada com vários QR Codes prontos para impressão em grade.")
        
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            qtd_corredores = st.slider("Até qual corredor?", 1, 16, 16)
        with col_l2:
            qtd_itens = st.slider("Quantos pallets/itens por corredor?", 1, 25, 11)
            
        lados_lote = st.multiselect("Lados a incluir:", LISTA_LADOS, default=["Direito", "Esquerdo"])
        
        if st.button("Gerar Grade de Etiquetas para Impressão"):
            lista_etiquetas = []
            for c in range(1, qtd_corredores + 1):
                corr_str = f"Corredor {c:02d}"
                for i in range(1, qtd_itens + 1):
                    item_str = f"Item {i:02d}"
                    for lado in lados_lote:
                        texto_loc = f"{corr_str} - Pallet {item_str} - Lado: {lado}"
                        lista_etiquetas.append(texto_loc)
            
            st.session_state.lista_etiquetas_cache = lista_etiquetas
            st.success(f"Foram geradas {len(lista_etiquetas)} etiquetas com base nos seus parâmetros!")

        if "lista_etiquetas_cache" in st.session_state and st.session_state.lista_etiquetas_cache:
            lista_etiquetas = st.session_state.lista_etiquetas_cache
            
            st.markdown("---")
            st.markdown("#### 👁️ Impressão e Pré-visualização")
            
            html_grade_completo = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Impressão de Etiquetas - Premium Wines</title>
                <style>
                    body { font-family: sans-serif; background: white; margin: 20px; }
                    .grid-container { display: flex; flex-wrap: wrap; gap: 15px; justify-content: center; }
                    .etiqueta-card { border: 2px dashed #7A1C2E; border-radius: 8px; padding: 10px; width: 180px; text-align: center; background: white; page-break-inside: avoid; margin-bottom: 10px; }
                    .etiqueta-card img { display: block; margin: 0 auto; width: 120px; }
                    .etiqueta-texto { font-size: 10px; font-weight: bold; color: #1A1A1A; margin-top: 6px; line-height: 1.2; }
                    .btn-imprimir { position: fixed; top: 20px; right: 20px; background-color: #7A1C2E; color: white; padding: 12px 20px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; z-index: 1000; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
                    .btn-imprimir:hover { background-color: #5c1322; }
                    @media print { .btn-imprimir { display: none; } }
                </style>
            </head>
            <body>
                <button class="btn-imprimir" onclick="window.print()">🖨️ Imprimir / Salvar PDF</button>
                <div class="grid-container">
            """
            
            for etiqueta in lista_etiquetas:
                api_url = gerar_qr_code_api(etiqueta)
                html_grade_completo += f"""
                    <div class="etiqueta-card">
                        <img src="{api_url}">
                        <div class="etiqueta-texto">{etiqueta}</div>
                    </div>
                """
            html_grade_completo += """
                </div>
            </body>
            </html>
            """
            
            st.download_button(
                label="📥 Baixar Página de Etiquetas Pronta para Impressão (.html)",
                data=html_grade_completo,
                file_name="grade_etiquetas_galpao.html",
                mime="text/html",
                use_container_width=True
            )
            
            st.markdown("Dica: Clique no botão acima para baixar o arquivo **grade_etiquetas_galpao.html**. Dê um duplo clique nele para abri-lo no seu navegador e clique no botão vermelho **🖨️ Imprimir / Salvar PDF** no canto superior direito.")
            
            html_preview = "<div style='display: flex; flex-wrap: wrap; gap: 15px; justify-content: center; font-family: sans-serif;'>"
            for etiqueta in lista_etiquetas:
                api_url = gerar_qr_code_api(etiqueta)
                html_preview += f"""
                    <div style="border: 2px dashed #7A1C2E; border-radius: 8px; padding: 10px; width: 180px; text-align: center; background: white; margin-bottom: 10px;">
                        <img src="{api_url}" width="120" style="display: block; margin: 0 auto;">
                        <div style="font-size: 10px; font-weight: bold; color: #1A1A1A; margin-top: 6px; line-height: 1.2;">{etiqueta}</div>
                    </div>
                """
            html_preview += "</div>"
            components.html(html_preview, height=500, scrolling=True)

elif st.session_state.menu_atual == "Historico":
    st.subheader("📋 Histórico")
    for l in carregar_logs():
        st.markdown(f"- **{l['data_hora']}** | {l['usuario']} | {l['acao']}")

elif st.session_state.menu_atual == "GerenciarUsuarios":
    if st.session_state.usuario_logado.get('cargo') != "Desenvolvedor":
        st.error("Acesso negado. Esta área é restrita ao Desenvolvedor.")
        st.stop()
        
    st.subheader("⚙️ Gerenciar Usuários")
    for u in st.session_state.usuarios:
        st.write(f"👤 **{u['nome']}** (Cargo: {u.get('cargo', 'Operador')}) | Senha: `{u['senha']}`")

elif st.session_state.menu_atual == "Editar":
    st.subheader("✏️ Editar Vinho / Mudar de Pallet")
    nomes_vinhos = [f"{v.get('nome')} (Safra: {v.get('safra', 'N/A')} - Loc: {v.get('localizacao', 'N/A')})" for v in st.session_state.estoque]
    if nomes_vinhos:
        vinho_sel = st.selectbox("Selecione o vinho para editar:", nomes_vinhos)
        idx = nomes_vinhos.index(vinho_sel)
        v_atual = st.session_state.estoque[idx]
        
        with st.form("edit_form"):
            n = st.text_input("Nome do Vinho", value=v_atual.get('nome', '')).strip().title()
            
            tipos_disp = ["Tinto", "Branco", "Rosé", "Espumante"]
            idx_tipo = tipos_disp.index(v_atual.get('tipo')) if v_atual.get('tipo') in tipos_disp else 0
            t = st.selectbox("Tipo", tipos_disp, index=idx_tipo)
            
            s = st.text_input("Safra", value=v_atual.get('safra', ''))
            
            st.markdown("---")
            st.markdown("📍 **Atualizar Localização Física (Pallet / Prateleira)**")
            corredor = st.selectbox("Corredor", LISTA_CORREDORES)
            tipo_loc = st.selectbox("Tipo Local", LISTA_LOCAIS_TIPO)
            numero = st.selectbox("Número", LISTA_NUMEROS_LOCAL)
            
            idx_lado = LISTA_LADOS.index(v_atual.get('lado')) if v_atual.get('lado') in LISTA_LADOS else 0
            lado = st.selectbox("Lado", LISTA_LADOS, index=idx_lado)
            
            idx_caixa = OPCOES_CAIXA.index(v_atual.get('caixa')) if v_atual.get('caixa') in OPCOES_CAIXA else 0
            caixa = st.selectbox("Caixa", OPCOES_CAIXA, index=idx_caixa)
            
            foto_vinho = st.file_uploader("Alterar Foto (Opcional)", type=["jpg", "jpeg", "png"])
            
            if st.form_submit_button("Salvar Alterações"):
                if n.strip():
                    nome_foto = v_atual.get('foto', '')
                    if foto_vinho is not None:
                        nome_foto = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{foto_vinho.name}"
                        caminho_foto = os.path.join(PASTA_FOTOS, nome_foto)
                        with open(caminho_foto, "wb") as f:
                            f.write(foto_vinho.getbuffer())
                    
                    st.session_state.estoque[idx] = {
                        "nome": n.strip(),
                        "tipo": t,
                        "safra": s.strip(),
                        "localizacao": f"{corredor} - {tipo_loc} {numero}",
                        "lado": lado,
                        "caixa": caixa,
                        "foto": nome_foto
                    }
                    salvar_dados(st.session_state.estoque)
                    registrar_log(st.session_state.usuario_logado['nome'], "Editar Vinho", f"Atualizado/Movido: {n}")
                    st.success("Vinho atualizado e reposicionado com sucesso!")
                    st.session_state.menu_atual = "🏠 Home"
                    st.rerun()
                else:
                    st.error("O nome do vinho não pode ficar vazio.")
    else:
        st.info("Nenhum vinho para editar.")

elif st.session_state.menu_atual == "Excluir":
    st.subheader("🗑️ Excluir Vinho")
    nomes_vinhos = [f"{v.get('nome')} ({v.get('safra')})" for v in st.session_state.estoque]
    if nomes_vinhos:
        vinho_sel = st.selectbox("Selecione para excluir:", nomes_vinhos)
        if st.button("Confirmar Exclusão"):
            idx = nomes_vinhos.index(vinho_sel)
            removido = st.session_state.estoque.pop(idx)
            salvar_dados(st.session_state.estoque)
            registrar_log(st.session_state.usuario_logado['nome'], "Excluir Vinho", f"Removido: {removido.get('nome')}")
            st.success("Vinho excluído com sucesso!")
            st.session_state.menu_atual = "🏠 Home"
            st.rerun()
    else:
        st.info("Nenhum vinho para excluir.")
