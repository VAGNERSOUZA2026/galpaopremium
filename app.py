import json
import os
import shutil
from datetime import datetime, timezone, timedelta
import pandas as pd
import streamlit as st
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
    label { color: #7A1C2E !important; font-weight: 700 !important; font-size: 0.95rem !important; }
    .wine-card { background-color: #FFFFFF; color: #1A1A1A; border-radius: 14px; padding: 16px; margin-bottom: 12px; border: 1px solid #E9ECEF; box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.03); }
    .wine-title { color: #7A1C2E; font-size: 1.1rem; font-weight: 700; margin-bottom: 4px; }
    .badge-pallet-grande { background-color: #7A1C2E; color: #FFFFFF; padding: 6px 14px; border-radius: 8px; font-weight: 700; font-size: 1rem; display: inline-block; }
    .badge-caixa-grande { background-color: #343A40; color: #FFFFFF; padding: 6px 14px; border-radius: 8px; font-weight: 700; font-size: 1rem; display: inline-block; }
    .stButton button { background-color: #7A1C2E !important; color: #FFFFFF !important; border-radius: 12px !important; font-weight: 600 !important; border: none !important; padding: 10px 16px !important; width: 100%; white-space: pre-wrap; }
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

def buscar_por_voz():
    js = """
    window.SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new SpeechRecognition();
    rec.lang = 'pt-BR';
    rec.start();
    return new Promise((resolve) => {
        rec.onresult = (e) => { resolve(e.results[0][0].transcript); };
        rec.onerror = (e) => { resolve(""); };
    });
    """
    return st_javascript(js)

def extrair_linhas_de_arquivo(arq):
    linhas = []
    ext = arq.name.split('.')[-1].lower()
    try:
        if ext in ['xlsx', 'xls']:
            df = pd.read_excel(arq)
            for c in df.columns:
                for v in df[c].dropna():
                    if str(v).strip(): linhas.append(str(v).strip())
        elif ext == 'docx':
            doc = Document(arq)
            for p in doc.paragraphs:
                if p.text.strip(): linhas.append(p.text.strip())
        elif ext == 'txt':
            linhas = [l.strip() for l in arq.getvalue().decode("utf-8").split("\n") if l.strip()]
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
                u = st.text_input("Usuário").strip()
                p = st.text_input("Senha", type="password").strip()
                if st.form_submit_button("ENTRAR", use_container_width=True):
                    user = next((x for x in st.session_state.usuarios if x['nome'].lower() == u.lower() and x['senha'] == p), None)
                    if user:
                        st.session_state.usuario_logado = user
                        st.query_params["user"] = user['nome']
                        st.query_params["cargo"] = user['cargo']
                        st.rerun()
                    else: st.error("Dados incorretos.")
        with tab2:
            with st.form("c_form"):
                n = st.text_input("Nome").strip()
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
        if st.button("🔍 Buscar / Filtros\n\nMúltiplos critérios", use_container_width=True): st.session_state.menu_atual = "Filtros"; st.rerun()
    with c2:
        if st.button("🗺️ Mapa de Separação\n\nEnviar arquivo ou lista", use_container_width=True): st.session_state.menu_atual = "MapaSeparacao"; st.rerun()
    with c3:
        if st.button("🍷 Estoque Completo\n\nVer todos os vinhos", use_container_width=True): st.session_state.menu_atual = "Estoque"; st.rerun()
    
    st.write("")
    c4, c5, c6 = st.columns(3)
    with c4:
        if st.button("➕ Cadastrar Vinho\n\nAdicionar ao sistema", use_container_width=True): st.session_state.menu_atual = "Cadastrar"; st.rerun()
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
        
    st.write("")
    if st.button("⚙️ Gerenciar Contas Cadastradas (Ver Logins e Senhas)", use_container_width=True):
        st.session_state.menu_atual = "GerenciarUsuarios"
        st.rerun()

elif st.session_state.menu_atual == "Filtros":
    st.subheader("🔍 Busca por Nome ou Voz")
    ct, cv = st.columns([4, 1])
    with ct: termo = st.text_input("Filtrar:", value=st.session_state.termo_busca).strip()
    with cv:
        st.write("<br>", unsafe_allow_html=True)
        if st.button("🎙️ Voz"):
            res_voz = buscar_por_voz()
            if res_voz: st.session_state.termo_busca = res_voz; st.rerun()
    
    tp = termo.lower() if termo else st.session_state.termo_busca.lower()
    if tp:
        res = [v for v in st.session_state.estoque if tp in v.get("nome", "").lower()]
        for v in res:
            st.markdown(f"<div class='wine-card'><div class='wine-title'>🍷 {v.get('nome')} ({v.get('safra')})</div><p><span class='badge-pallet-grande'>📍 {v.get('localizacao')} - Lado: {v.get('lado', 'N/A')}</span></p></div>", unsafe_allow_html=True)

elif st.session_state.menu_atual == "MapaSeparacao":
    st.subheader("🗺️ Mapa de Separação")
    arq = st.file_uploader("Arquivo (Excel/Word/TXT)", type=["xlsx", "xls", "docx", "txt"])
    txt_man = st.text_area("Ou cole a lista:")
    if st.button("Gerar Rota"):
        linhas = extrair_linhas_de_arquivo(arq) if arq else [l.strip() for l in txt_man.split("\n") if l.strip()]
        encontrados = [v for v in st.session_state.estoque if any(l.lower() in v.get("nome", "").lower() for l in linhas)]
        for v in encontrados:
            st.markdown(f"<div class='wine-card'><div class='wine-title'>🍷 {v.get('nome')}</div><p><span class='badge-pallet-grande'>📍 {v.get('localizacao')} - Lado: {v.get('lado', 'N/A')}</span></p></div>", unsafe_allow_html=True)

elif st.session_state.menu_atual == "Scanner":
    st.subheader("📷 Escanear QR Code do Local")
    foto = st.camera_input("Capturar Foto do QR Code do Pallet/Prateleira")
    if foto and OPENCV_DISPONIVEL:
        img = cv2.imdecode(np.frombuffer(foto.getvalue(), np.uint8), cv2.IMREAD_COLOR)
        val, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
        if val:
            termo_lido = val.strip().lower()
            st.success(f"Local Identificado: {val}")
            st.markdown("### 🍷 Vinhos armazenados neste local:")
            
            resultados = []
            for v in st.session_state.estoque:
                loc_cadastrada = str(v.get('localizacao', '')).strip().lower()
                lado_cadastrado = str(v.get('lado', '')).strip().lower()
                
                # Monta a string completa do local para comparar perfeitamente com o QR code da etiqueta do pallet
                string_completa_local = f"{loc_cadastrada} - lado: {lado_cadastrado}"
                
                # Se o QR code lido corresponder ao local e lado do vinho
                if termo_lido in string_completa_local or termo_lido == loc_cadastrada or loc_cadastrada in termo_lido:
                    resultados.append(v)
                    
            if resultados:
                for v in resultados:
                    st.markdown(f"<div class='wine-card'><div class='wine-title'>🍷 {v.get('nome')} ({v.get('safra', 'N/A')})</div><p>Tipo: <b>{v.get('tipo', 'N/A')}</b> | Caixa: <b>{v.get('caixa', 'N/A')}</b><br>📍 Local: <b>{v.get('localizacao', 'N/A')}</b> (Lado: <b>{v.get('lado', 'N/A')}</b>)</p></div>", unsafe_allow_html=True)
            else: 
                st.warning("Nenhum vinho cadastrado exatamente neste local e lado no momento.")
        else: 
            st.error("QR Code não detectado. Tente aproximar mais a câmera.")

elif st.session_state.menu_atual == "Estoque":
    st.subheader("🍷 Estoque Completo")
    if not st.session_state.estoque:
        st.info("O estoque está vazio.")
    for v in st.session_state.estoque:
        st.markdown(f"<div class='wine-card'><div class='wine-title'>🍷 {v.get('nome')} ({v.get('safra')})</div><p>📍 <b>{v.get('localizacao')}</b> - Lado: <b>{v.get('lado', 'N/A')}</b></p></div>", unsafe_allow_html=True)

elif st.session_state.menu_atual == "Cadastrar":
    st.subheader("➕ Cadastrar Vinho")
    with st.form("cad"):
        nome = st.text_input("Nome").strip()
        tipo = st.selectbox("Tipo", ["Tinto", "Branco", "Rosé", "Espumante"])
        safra = st.text_input("Safra").strip()
        corredor = st.selectbox("Corredor", LISTA_CORREDORES)
        tipo_loc = st.selectbox("Tipo Local", LISTA_LOCAIS_TIPO)
        numero = st.selectbox("Número", LISTA_NUMEROS_LOCAL)
        lado = st.selectbox("Lado", LISTA_LADOS)
        caixa = st.selectbox("Caixa", OPCOES_CAIXA)
        if st.form_submit_button("Salvar"):
            if nome:
                st.session_state.estoque.append({"nome": nome, "tipo": tipo, "safra": safra, "localizacao": f"{corredor} - {tipo_loc} {numero}", "lado": lado, "caixa": caixa, "foto": ""})
                salvar_dados(st.session_state.estoque)
                registrar_log(st.session_state.usuario_logado['nome'], "Cadastrar Vinho", f"Cadastrado: {nome}")
                st.success("Salvo!")
                st.session_state.menu_atual = "🏠 Home"
                st.rerun()

elif st.session_state.menu_atual == "GerarQR":
    st.subheader("📱 Gerar QR Code do Local (Pallet / Prateleira)")
    st.write("Selecione abaixo o endereço físico do galpão para gerar a etiqueta do pallet/prateleira:")
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        c_corredor = st.selectbox("Corredor", LISTA_CORREDORES, key="qr_corredor")
        c_tipo = st.selectbox("Tipo de Local", LISTA_LOCAIS_TIPO, key="qr_tipo")
    with col_g2:
        c_numero = st.selectbox("Número do Item", LISTA_NUMEROS_LOCAL, key="qr_numero")
        c_lado = st.selectbox("Lado", LISTA_LADOS, key="qr_lado")
        
    # Monta a identificação única daquele pallet/prateleira exato
    local_etiqueta = f"{c_corredor} - {c_tipo} {c_numero} - Lado: {c_lado}"
    
    st.write("")
    if st.button("Gerar Etiqueta do Local", use_container_width=True):
        _, cq, _ = st.columns([1, 2, 1])
        with cq: 
            st.image(gerar_qr_code_api(local_etiqueta), width=240, caption=local_etiqueta)
            st.success(f"QR Code gerado para: {local_etiqueta}")

elif st.session_state.menu_atual == "Historico":
    st.subheader("📋 Histórico")
    logs = carregar_logs()
    if not logs:
        st.info("Nenhum registro encontrado.")
    for l in logs:
        st.markdown(f"- **{l['data_hora']}** | {l['usuario']} | {l['acao']}")

elif st.session_state.menu_atual == "GerenciarUsuarios":
    st.subheader("⚙️ Gerenciar Usuários Cadastrados")
    for u in st.session_state.usuarios:
        st.write(f"👤 **{u['nome']}** | Cargo: {u['cargo']} | Senha: `{u['senha']}`")

elif st.session_state.menu_atual == "Editar":
    st.subheader("✏️ Editar Vinho Cadastrado")
    if not st.session_state.estoque:
        st.info("Não há vinhos cadastrados para editar.")
    else:
        nomes_vinhos = [f"{v.get('nome')} (Safra: {v.get('safra', 'N/A')} - Loc: {v.get('localizacao', 'N/A')})" for v in st.session_state.estoque]
        vinho_selecionado_str = st.selectbox("Selecione o vinho que deseja editar:", nomes_vinhos)
        
        idx_vinho = nomes_vinhos.index(vinho_selecionado_str)
        v_atual = st.session_state.estoque[idx_vinho]
        
        with st.form("form_editar_vinho"):
            novo_nome = st.text_input("Nome do Vinho", value=v_atual.get('nome', '')).strip()
            novo_tipo = st.selectbox("Tipo", ["Tinto", "Branco", "Rosé", "Espumante", "Fortificado"], index=["Tinto", "Branco", "Rosé", "Espumante", "Fortificado"].index(v_atual.get('tipo', 'Tinto')) if v_atual.get('tipo') in ["Tinto", "Branco", "Rosé", "Espumante", "Fortificado"] else 0)
            nova_safra = st.text_input("Safra", value=v_atual.get('safra', '')).strip()
            nova_loc = st.text_input("Localização", value=v_atual.get('localizacao', '')).strip()
            novo_lado = st.selectbox("Lado", LISTA_LADOS, index=LISTA_LADOS.index(v_atual.get('lado', 'Direito')) if v_atual.get('lado') in LISTA_LADOS else 0)
            nova_caixa = st.selectbox("Embalagem / Caixa", OPCOES_CAIXA, index=OPCOES_CAIXA.index(v_atual.get('caixa', 'Caixa com 12 garrafas')) if v_atual.get('caixa') in OPCOES_CAIXA else 0)
            
            if st.form_submit_button("Salvar Alterações"):
                if novo_nome:
                    st.session_state.estoque[idx_vinho] = {
                        "nome": novo_nome,
                        "tipo": novo_tipo,
                        "safra": nova_safra,
                        "localizacao": nova_loc,
                        "lado": novo_lado,
                        "caixa": nova_caixa,
                        "foto": v_atual.get('foto', '')
                    }
                    salvar_dados(st.session_state.estoque)
                    registrar_log(st.session_state.usuario_logado['nome'], "Editar Vinho", f"Atualizado: {novo_nome}")
                    st.success("Vinho atualizado com sucesso!")
                    st.session_state.menu_atual = "🏠 Home"
                    st.rerun()
                else:
                    st.error("O nome do vinho não pode ficar vazio.")

elif st.session_state.menu_atual == "Excluir":
    st.subheader("🗑️ Excluir Vinho do Estoque")
    if not st.session_state.estoque:
        st.info("Não há vinhos cadastrados para excluir.")
    else:
        nomes_vinhos_ex = [f"{v.get('nome')} (Safra: {v.get('safra', 'N/A')} - Loc: {v.get('localizacao', 'N/A')})" for v in st.session_state.estoque]
        vinho_ex_str = st.selectbox("Selecione o vinho que deseja remover:", nomes_vinhos_ex, key="select_excluir")
        
        idx_ex = nomes_vinhos_ex.index(vinho_ex_str)
        vinho_alvo = st.session_state.estoque[idx_ex]
        
        st.warning(f"Tem certeza que deseja excluir permanentemente o vinho: **{vinho_alvo.get('nome')}**?")
        
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("Confirmar Exclusão", use_container_width=True):
                removido = st.session_state.estoque.pop(idx_ex)
                salvar_dados(st.session_state.estoque)
                registrar_log(st.session_state.usuario_logado['nome'], "Excluir Vinho", f"Removido: {removido.get('nome')}")
                st.success("Vinho excluído com sucesso!")
                st.session_state.menu_atual = "🏠 Home"
                st.rerun()
        with col_b2:
            if st.button("Cancelar", use_container_width=True):
                st.session_state.menu_atual = "🏠 Home"
                st.rerun()
