import json
import os
import shutil
from datetime import datetime, timezone, timedelta
import pandas as pd
import streamlit as st
import urllib.parse
from docx import Document
import re

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
ARQUIVO_PEDIDOS = "pedidos_matriz.json"
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
    estoque = []
    if os.path.exists(NOME_ARQUIVO):
        try:
            with open(NOME_ARQUIVO, "r", encoding="utf-8") as f: estoque = json.load(f)
        except: pass
    if not estoque:
        estoque = [{"nome": "Campana Merlot", "tipo": "Tinto", "safra": "2024", "localizacao": "Corredor 01 - Pallet Item 01", "lado": "Direito", "caixa": "Caixa com 12 garrafas", "codigo_barras": "7891008116632", "foto": ""}]
    return sorted(estoque, key=lambda x: x.get("nome", "").lower())

def salvar_dados(estoque):
    estoque_ordenado = sorted(estoque, key=lambda x: x.get("nome", "").lower())
    with open(NOME_ARQUIVO, "w", encoding="utf-8") as f: json.dump(estoque_ordenado, f, ensure_ascii=False, indent=4)
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

def carregar_pedidos():
    if os.path.exists(ARQUIVO_PEDIDOS):
        try:
            with open(ARQUIVO_PEDIDOS, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return []

def salvar_pedidos(pedidos):
    with open(ARQUIVO_PEDIDOS, "w", encoding="utf-8") as f: json.dump(pedidos, f, ensure_ascii=False, indent=4)

def gerar_qr_code_api(texto):
    return f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={urllib.parse.quote(texto)}"

def interpretar_linha_pedido(texto_linha):
    texto = texto_linha.strip()
    safra = ""
    quantidade = 1
    
    anos = re.findall(r'\b(20\d{2})\b', texto)
    if anos:
        safra = anos[0]
        texto_limpo = texto.replace(safra, "")
    else:
        texto_limpo = texto

    match_qtd = re.search(r'(?:/|\bcaixas?|\bqt[d]?\.?)\s*(\d+)', texto_limpo, re.IGNORECASE)
    if match_qtd:
        quantidade = int(match_qtd.group(1))
        texto_limpo = texto_limpo.replace(match_qtd.group(0), "")
    else:
        numeros_soltos = re.findall(r'\b(\d+)\b', texto_limpo)
        if numeros_soltos and numeros_soltos[-1] != safra:
            quantidade = int(numeros_soltos[-1])
            texto_limpo = texto_limpo.replace(numeros_soltos[-1], "")

    texto_limpo = re.sub(r'\bcaixas?\b', '', texto_limpo, flags=re.IGNORECASE)
    nome = re.sub(r'[/\|\-\–]+', '', texto_limpo).strip().title()
    return {"nome": nome, "safra": safra, "quantidade": quantidade, "separado": False, "qtd_separada": 0}

def extrair_pedidos_de_arquivo(arq):
    itens = []
    ext = arq.name.split('.')[-1].lower()
    try:
        if ext in ['xlsx', 'xls']:
            df = pd.read_excel(arq)
            for _, row in df.iterrows():
                nome_bruto = str(row.get('Nome', row.iloc[0] if len(row) > 0 else '')).strip()
                if nome_bruto and nome_bruto != 'Nan':
                    safra_col = str(row.get('Safra', row.iloc[1] if len(row) > 1 else '')).strip()
                    qtd_col = row.get('Quantidade', row.iloc[2] if len(row) > 2 else 1)
                    try: qtd = int(qtd_col) if pd.notnull(qtd_col) else 1
                    except: qtd = 1
                    
                    itens.append({
                        "nome": nome_bruto.title(), 
                        "safra": safra_col if safra_col != 'Nan' else '', 
                        "quantidade": qtd, 
                        "separado": False, 
                        "qtd_separada": 0
                    })
        elif ext == 'txt':
            linhas = [l.strip() for l in arq.getvalue().decode("utf-8").split("\n") if l.strip()]
            for l in linhas:
                itens.append(interpretar_linha_pedido(l))
    except: pass
    return itens

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

def extrair_numero_corredor(localizacao):
    nums = re.findall(r'\d+', localizacao)
    if nums:
        return int(nums[0])
    return 999

if "usuarios" not in st.session_state:
    st.session_state.usuarios = carregar_usuarios()

st.session_state.estoque = carregar_dados()
st.session_state.pedidos = carregar_pedidos()

if "menu_atual" not in st.session_state: st.session_state.menu_atual = "🏠 Home"
if "termo_busca" not in st.session_state: st.session_state.termo_busca = ""
if "codigo_capturado_cadastro" not in st.session_state: st.session_state.codigo_capturado_cadastro = ""

qp = st.query_params
user_url = qp.get("user", None)
cargo_url = qp.get("cargo", "Operador")

if "usuario_logado" not in st.session_state or st.session_state.usuario_logado is None:
    if user_url:
        st.session_state.usuario_logado = {"nome": user_url, "cargo": cargo_url}
    else:
        st.session_state.usuario_logado = None

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
                        dev_user = {"nome": "Dev", "cargo": "Desenvolvedor"}
                        st.session_state.usuario_logado = dev_user
                        st.query_params["user"] = "Dev"
                        st.query_params["cargo"] = "Desenvolvedor"
                        st.rerun()
                    else: st.error("Senha incorreta.")
    st.stop()

ct1, ct2, ct3 = st.columns([3, 2, 1])
with ct1: st.markdown(f"🍷 <b>PREMIUM WINES</b> | Usuário: {st.session_state.usuario_logado['nome']} ({st.session_state.usuario_logado.get('cargo', 'Operador')})", unsafe_allow_html=True)
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
        if st.button("📦 Lista de Pedidos (Matriz)", use_container_width=True): st.session_state.menu_atual = "PedidosMatriz"; st.rerun()
    with c2:
        if st.button("🔍 Buscar / Filtros", use_container_width=True): st.session_state.menu_atual = "Filtros"; st.rerun()
    with c3:
        if st.button("🗺️ Mapa de Separação", use_container_width=True): st.session_state.menu_atual = "MapaSeparacao"; st.rerun()
    
    st.write("")
    c4, c5, c6 = st.columns(3)
    with c4:
        if st.button("🍷 Estoque Completo", use_container_width=True): st.session_state.menu_atual = "Estoque"; st.rerun()
    with c5:
        if st.button("➕ Cadastrar Vinho", use_container_width=True): st.session_state.menu_atual = "Cadastrar"; st.rerun()
    with c6:
        if st.button("📱 Gerar QR Code", use_container_width=True): st.session_state.menu_atual = "GerarQR"; st.rerun()
        
    st.write("")
    c7, c8, c9 = st.columns(3)
    with c7:
        if st.button("📷 Escanear Local", use_container_width=True): st.session_state.menu_atual = "Scanner"; st.rerun()
    with c8:
        if st.button("✏️ Editar Vinho", use_container_width=True): st.session_state.menu_atual = "Editar"; st.rerun()
    with c9:
        if st.button("📋 Histórico", use_container_width=True): st.session_state.menu_atual = "Historico"; st.rerun()
        
    if st.session_state.usuario_logado.get('cargo') == "Desenvolvedor":
        st.write("")
        if st.button("⚙️ Gerenciar Contas", use_container_width=True):
            st.session_state.menu_atual = "GerenciarUsuarios"
            st.rerun()

elif st.session_state.menu_atual == "PedidosMatriz":
    st.subheader("📦 Gerenciamento de Pedidos e Conferência Antierros")
    
    aba_ped1, aba_ped2 = st.tabs(["📋 Enviar/Novo Pedido", "🔍 Roteiro e Leitor de Caixa (Antierros)"])
    
    with aba_ped1:
        st.markdown("Envie a lista enviada pela matriz (Excel ou TXT) ou digite livremente (ex: *Campana Merlot 2024 /05 Caixas*).")
        
        with st.form("form_novo_pedido"):
            id_pedido = st.text_input("Identificação do Pedido / Loja", value=f"Pedido #{datetime.now().strftime('%d/%m %H:%M')}")
            arq_pedido = st.file_uploader("Arquivo de Pedido (Excel ou TXT)", type=["xlsx", "xls", "txt"])
            
            st.markdown("Ou digite os itens linha a linha (o sistema lê automaticamente a safra e a quantidade):")
            texto_manual_pedido = st.text_area("Ex: Campana Merlot 2024 /05 Caixas", placeholder="Campana Merlot 2024 / 05 Caixas\nLa Consulta Malbec 2023 / 2")
            
            if st.form_submit_button("Cadastrar Pedido para Separação"):
                itens_novos = []
                if arq_pedido is not None:
                    itens_novos = extrair_pedidos_de_arquivo(arq_pedido)
                if texto_manual_pedido.strip():
                    for linha in texto_manual_pedido.split("\n"):
                        if linha.strip():
                            itens_novos.append(interpretar_linha_pedido(linha))
                
                if itens_novos:
                    novo_registro_pedido = {
                        "id": id_pedido,
                        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "itens": itens_novos,
                        "status": "Pendente"
                    }
                    st.session_state.pedidos.append(novo_registro_pedido)
                    salvar_pedidos(st.session_state.pedidos)
                    registrar_log(st.session_state.usuario_logado['nome'], "Novo Pedido Matriz", id_pedido)
                    st.success("Pedido cadastrado com sucesso!")
                    st.rerun()
                else:
                    st.error("Adicione itens por arquivo ou texto.")
                    
    with aba_ped2:
        if not st.session_state.pedidos:
            st.info("Nenhum pedido cadastrado.")
        else:
            pedidos_nomes = [f"{p['id']} ({p['data']}) - {len(p['itens'])} itens" for p in st.session_state.pedidos]
            escolha_ped_str = st.selectbox("Selecione o Pedido:", pedidos_nomes)
            idx_ped = pedidos_nomes.index(escolha_ped_str)
            pedido_atual = st.session_state.pedidos[idx_ped]
            
            col_info_ped, col_del_ped = st.columns([3, 1])
            with col_info_ped:
                st.markdown(f"### Pedido: {pedido_atual['id']}")
            with col_del_ped:
                if st.button("🗑️ Excluir Pedido", use_container_width=True):
                    id_removido = pedido_atual['id']
                    st.session_state.pedidos.pop(idx_ped)
                    salvar_pedidos(st.session_state.pedidos)
                    registrar_log(st.session_state.usuario_logado['nome'], "Excluir Pedido", id_removido)
                    st.success("Pedido excluído com sucesso!")
                    st.rerun()
            
            ordem_separacao = st.radio("Direção da Rota pelos Corredores:", ["Crescente (Corredor 01 ao 25)", "Decrescente (Corredor 25 ao 01)"], horizontal=True)
            reversa = True if "Decrescente" in ordem_separacao else False
            
            itens_com_local = []
            for item in pedido_atual['itens']:
                nome_pedido_limpo = item['nome'].lower()
                safra_pedido = str(item.get('safra', '')).strip()
                
                vinho_encontrado = None
                for v in st.session_state.estoque:
                    v_nome = v.get('nome', '').lower()
                    v_safra = str(v.get('safra', '')).strip()
                    
                    palavras_pedido = [p for p in nome_pedido_limpo.split() if len(p) > 2]
                    match_parcial = any(p in v_nome for p in palavras_pedido) if palavras_pedido else False
                    
                    if v_nome in nome_pedido_limpo or nome_pedido_limpo in v_nome or match_parcial:
                        if safra_pedido and v_safra:
                            if safra_pedido == v_safra:
                                vinho_encontrado = v
                                break
                        else:
                            vinho_encontrado = v
                            break
                            
                if not vinho_encontrado:
                    vinho_encontrado = next((v for v in st.session_state.estoque if v.get('nome', '').lower() in nome_pedido_limpo or nome_pedido_limpo in v.get('nome', '').lower()), None)
                
                loc = vinho_encontrado.get('localizacao', 'Corredor 01 - Pallet Item 01') if vinho_encontrado else 'Não cadastrado'
                corr_num = extrair_numero_corredor(loc)
                
                itens_com_local.append({
                    "item_original": item,
                    "vinho_estoque": vinho_encontrado,
                    "localizacao": loc,
                    "corredor_num": corr_num
                })
                
            itens_ordenados = sorted(itens_com_local, key=lambda x: x['corredor_num'], reverse=reversa)
            
            st.markdown("---")
            st.markdown("#### 🎯 Roteiro e Bipe de Caixas (Antierros)")
            
            todos_separados = True
            for i, obj in enumerate(itens_ordenados):
                item = obj['item_original']
                vinho_est = obj['vinho_estoque']
                loc = obj['localizacao']
                
                status_cor = "🟢" if item.get('separado') else "⏳"
                if not item.get('separado'): todos_separados = False
                
                with st.expander(f"{status_cor} {item['nome']} {item.get('safra', '')} | Qtd: {item['quantidade']} caixas | 📍 {loc}"):
                    if vinho_est:
                        st.markdown(f"**Estoque:** Safra no Galpão: **{vinho_est.get('safra')}** | Local: **{vinho_est.get('localizacao')} - Lado: {vinho_est.get('lado')}** | C. Barras Cadastrado: `{vinho_est.get('codigo_barras', 'Não cadastrado')}`")
                        
                        safra_matriz = str(item.get('safra', '')).strip()
                        safra_galpao = str(vinho_est.get('safra', '')).strip()
                        
                        if safra_matriz and safra_galpao and safra_matriz != safra_galpao:
                            st.warning(f"⚠️ **Alerta de Safra Divergente!** Pedido pediu safra `{safra_matriz}`, mas no galpão é `{safra_galpao}`.")
                        
                        st.markdown("---")
                        st.markdown("📲 **Conferência Física:**")
                        qtd_informada = st.number_input("Quantidade que está levando:", min_value=1, value=item.get('quantidade', 1), key=f"qtd_inf_{idx_ped}_{i}")
                        
                        if qtd_informada != item['quantidade']:
                            st.error(f"❌ **Divergência de Quantidade!** O pedido pedia **{item['quantidade']}**, mas você informou **{qtd_informada}**.")
                        else:
                            st.success("✅ Quantidade confere com o pedido.")
                            
                        bip_caixa = st.text_input("Bipar código de barras da caixa com o leitor / celular:", key=f"bip_{idx_ped}_{i}")
                        
                        if bip_caixa:
                            cb_cadastrado = str(vinho_est.get('codigo_barras', '')).strip()
                            if cb_cadastrado and bip_caixa.strip() == cb_cadastrado:
                                st.success("✅ Código de barras conferido e validado com sucesso!")
                            else:
                                st.error("❌ O código de barras bipado não corresponde a este vinho! Cuidado, produto incorreto.")
                        
                        if st.button(f"✅ Confirmar Separação do Item #{i+1}", key=f"btn_sep_{idx_ped}_{i}"):
                            if qtd_informada != item['quantidade']:
                                st.error("Não é possível concluir: a quantidade informada diverge do pedido.")
                            else:
                                item['separado'] = True
                                item['qtd_separada'] = qtd_informada
                                salvar_pedidos(st.session_state.pedidos)
                                registrar_log(st.session_state.usuario_logado['nome'], "Separar Item Pedido", f"{item['nome']} (Qtd: {qtd_informada})")
                                st.success("Item confirmado e separado!")
                                st.rerun()
                    else:
                        st.error("❌ Vinho não encontrado no estoque do galpão.")

            if todos_separados:
                st.balloons()
                st.success("🎉 Pedido 100% separado e conferido sem divergências!")
                if st.button("Finalizar e Arquivar Pedido"):
                    pedido_atual['status'] = "Concluído"
                    salvar_pedidos(st.session_state.pedidos)
                    st.rerun()

elif st.session_state.menu_atual == "Filtros":
    st.subheader("🔍 Busca por Local ou Nome")
    termo_digitado = st.text_input("Filtrar por nome ou corredor/pallet:", value=st.session_state.termo_busca)
    termo = termo_digitado.strip().title()
    
    tp = termo.lower() if termo else st.session_state.termo_busca.lower()
    if tp:
        res = [v for v in st.session_state.estoque if tp in v.get("nome", "").lower() or tp in v.get("localizacao", "").lower() or tp in v.get("lado", "").lower()]
        if res:
            for v in sorted(res, key=lambda x: x.get("nome", "").lower()):
                img_tag = f"<br><img src='app/static/{v.get('foto')}' width='100' style='border-radius: 8px; margin-top: 8px;'>" if v.get('foto') and os.path.exists(os.path.join(PASTA_FOTOS, v.get('foto'))) else ""
                st.markdown(f"<div class='wine-card'><div class='wine-title'>🍷 {v.get('nome')} ({v.get('safra')})</div><p>Tipo: <b>{v.get('tipo', 'N/A')}</b> | Caixa: <b>{v.get('caixa', 'N/A')}</b><br><span class='badge-pallet-grande'>📍 {v.get('localizacao')} - Lado: {v.get('lado', 'N/A')}</span>{img_tag}</p></div>", unsafe_allow_html=True)
        else:
            st.warning("Nenhum vinho encontrado para este filtro/local.")

elif st.session_state.menu_atual == "MapaSeparacao":
    st.subheader("🗺️ Mapa de Separação")
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
                for v in sorted(encontrados, key=lambda x: x.get("nome", "").lower()):
                    st.markdown(f"<div class='wine-card'><div class='wine-title'>🍷 {v.get('nome')} ({v.get('safra', 'N/A')})</div><p>Tipo: <b>{v.get('tipo', 'N/A')}</b> | Caixa: <b>{v.get('caixa', 'N/A')}</b><br><span class='badge-pallet-grande'>📍 {v.get('localizacao', 'N/A')} - Lado: {v.get('lado', 'N/A')}</span></p></div>", unsafe_allow_html=True)
            else:
                st.warning("Nenhum vinho do arquivo corresponde aos cadastrados no estoque.")
        else:
            st.error("Envie um arquivo ou digite pelo menos um nome.")

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
                for v in sorted(resultados, key=lambda x: x.get("nome", "").lower()):
                    st.markdown(f"<div class='wine-card'><div class='wine-title'>🍷 {v.get('nome')} ({v.get('safra', 'N/A')})</div><p>Tipo: <b>{v.get('tipo', 'N/A')}</b> | Caixa: <b>{v.get('caixa', 'N/A')}</b><br>📍 Local: <b>{v.get('localizacao', 'N/A')}</b> (Lado: <b>{v.get('lado', 'N/A')}</b>)</p></div>", unsafe_allow_html=True)
            else: st.warning("Nenhum vinho encontrado neste local.")
        else: st.error("QR Code não detectado. Tente novamente.")

elif st.session_state.menu_atual == "Estoque":
    st.subheader("🍷 Estoque Completo (Ordem Alfabética)")
    estoque_ordenado = sorted(st.session_state.estoque, key=lambda x: x.get("nome", "").lower())
    for v in estoque_ordenado:
        st.markdown(f"<div class='wine-card'><div class='wine-title'>🍷 {v.get('nome')} ({v.get('safra')})</div><p>📍 <b>{v.get('localizacao')}</b> - Lado: <b>{v.get('lado', 'N/A')}</b> | C. Barras: `{v.get('codigo_barras', 'N/A')}`</p></div>", unsafe_allow_html=True)

elif st.session_state.menu_atual == "Cadastrar":
    st.subheader("➕ Cadastrar Vinho")
    
    modo_cadastro = st.radio("Escolha o modo de cadastro:", ["Cadastro Individual", "Importar Lote (Excel ou TXT)"])
    
    if modo_cadastro == "Cadastro Individual":
        with st.form("cad"):
            nome = st.text_input("Nome").strip().title()
            tipo = st.selectbox("Tipo", ["Tinto", "Branco", "Rosé", "Espumante"])
            safra = st.text_input("Safra").strip()
            codigo_barras = st.text_input("Código de Barras da Caixa/Garrafa", value=st.session_state.codigo_capturado_cadastro).strip()
            corredor = st.selectbox("Corredor", LISTA_CORREDORES)
            tipo_loc = st.selectbox("Tipo Local", LISTA_LOCAIS_TIPO)
            numero = st.selectbox("Número", LISTA_NUMEROS_LOCAL)
            lado = st.selectbox("Lado", LISTA_LADOS)
            caixa = st.selectbox("Caixa", OPCOES_CAIXA)
            foto_vinho = st.file_uploader("Foto da Garrafa / Rótulo (Opcional)", type=["jpg", "jpeg", "png"])
            
            submitted = st.form_submit_button("Salvar")
            if submitted:
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
                        "codigo_barras": codigo_barras,
                        "localizacao": f"{corredor} - {tipo_loc} {numero}", 
                        "lado": lado, 
                        "caixa": caixa, 
                        "foto": nome_foto
                    })
                    salvar_dados(st.session_state.estoque)
                    st.session_state.codigo_capturado_cadastro = ""
                    registrar_log(st.session_state.usuario_logado['nome'], "Cadastrar Vinho", nome)
                    st.success("Vinho cadastrado com sucesso!")
                    st.session_state.menu_atual = "🏠 Home"
                    st.rerun()
                else:
                    st.error("Informe o nome do vinho.")
                    
        st.markdown("---")
        st.markdown("📷 **Ou use a câmera do celular para ler o código de barras da caixa:**")
        foto_cb = st.camera_input("Fotografar código de barras")
        if foto_cb and OPENCV_DISPONIVEL:
            img_cb = cv2.imdecode(np.frombuffer(foto_cb.getvalue(), np.uint8), cv2.IMREAD_COLOR)
            val_cb, _, _ = cv2.QRCodeDetector().detectAndDecode(img_cb)
            if val_cb:
                st.session_state.codigo_capturado_cadastro = val_cb.strip()
                st.success(f"Código capturado com sucesso: {val_cb}. Clique em salvar acima!")
                st.rerun()
            else:
                st.warning("Código de barras não decodificado automaticamente pela foto. Use o leitor USB ou digite no campo.")

    else:
        st.info("Envie uma planilha Excel (.xlsx) com a coluna **Nome**, **Safra**, **Codigo_Barras** ou um arquivo de texto.")
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
                            "codigo_barras": str(row.get('Codigo_Barras', '')).strip(),
                            "localizacao": str(row.get('Localizacao', 'Corredor 01 - Pallet Item 01')).strip(),
                            "lado": str(row.get('Lado', 'Direito')).strip(),
                            "caixa": str(row.get('Caixa', 'Caixa com 12 garrafas')).strip(),
                            "foto": ""
                        })
                        importados += 1
            
            if importados > 0:
                salvar_dados(st.session_state.estoque)
                st.success(f"{importados} vinhos importados com sucesso!")
                st.session_state.menu_atual = "🏠 Home"
                st.rerun()
            else:
                st.warning("O arquivo parece estar vazio ou sem dados válidos.")

elif st.session_state.menu_atual == "GerarQR":
    st.subheader("📱 Gerar QR Code de Localização")
    c_corredor = st.selectbox("Corredor", LISTA_CORREDORES)
    c_tipo = st.selectbox("Tipo de Local", LISTA_LOCAIS_TIPO)
    c_numero = st.selectbox("Número do Item", LISTA_NUMEROS_LOCAL)
    c_lado = st.selectbox("Lado", LISTA_LADOS)
    
    local_etiqueta = f"{c_corredor} - {c_tipo} {c_numero} - Lado: {c_lado}"
    url_qr = gerar_qr_code_api(local_etiqueta)
    st.image(url_qr, width=240, caption=local_etiqueta)

elif st.session_state.menu_atual == "Historico":
    st.subheader("📋 Histórico")
    for l in carregar_logs():
        st.markdown(f"- **{l['data_hora']}** | {l['usuario']} | {l['acao']}")

elif st.session_state.menu_atual == "GerenciarUsuarios":
    if st.session_state.usuario_logado.get('cargo') != "Desenvolvedor":
        st.error("Acesso negado.")
        st.stop()
    st.subheader("⚙️ Gerenciar Usuários")
    for u in st.session_state.usuarios:
        st.write(f"👤 **{u['nome']}** (Cargo: {u.get('cargo', 'Operador')})")

elif st.session_state.menu_atual == "Editar":
    st.subheader("✏️ Editar Vinho")
    estoque_ordenado = sorted(st.session_state.estoque, key=lambda x: x.get("nome", "").lower())
    nomes_vinhos = [f"{v.get('nome')} (Safra: {v.get('safra', 'N/A')} - Loc: {v.get('localizacao', 'N/A')})" for v in estoque_ordenado]
    if nomes_vinhos:
        vinho_sel = st.selectbox("Selecione o vinho:", nomes_vinhos)
        idx_sel = nomes_vinhos.index(vinho_sel)
        v_atual = estoque_ordenado[idx_sel]
        idx_real = st.session_state.estoque.index(v_atual)
        
        with st.form("edit_form"):
            n = st.text_input("Nome", value=v_atual.get('nome', '')).strip().title()
            s = st.text_input("Safra", value=v_atual.get('safra', ''))
            cb = st.text_input("Código de Barras", value=v_atual.get('codigo_barras', '')).strip()
            corredor = st.selectbox("Corredor", LISTA_CORREDORES)
            tipo_loc = st.selectbox("Tipo Local", LISTA_LOCAIS_TIPO)
            numero = st.selectbox("Número", LISTA_NUMEROS_LOCAL)
            lado = st.selectbox("Lado", LISTA_LADOS)
            
            if st.form_submit_button("Salvar Alterações"):
                st.session_state.estoque[idx_real].update({
                    "nome": n,
                    "safra": s,
                    "codigo_barras": cb,
                    "localizacao": f"{corredor} - {tipo_loc} {numero}",
                    "lado": lado
                })
                salvar_dados(st.session_state.estoque)
                st.success("Atualizado com sucesso!")
                st.session_state.menu_atual = "🏠 Home"
                st.rerun()
