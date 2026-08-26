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
SENHA_DIVERGENCIA = "2026"

if not os.path.exists(PASTA_BACKUP):
    os.makedirs(PASTA_BACKUP)
if not os.path.exists(PASTA_FOTOS):
    os.makedirs(PASTA_FOTOS)

LISTA_CORREDORES = [f"Corredor {i:02d}" for i in range(1, 26)]
LISTA_LOCAIS_TIPO = ["Pallet", "Prateleira"]
LISTA_NUMEROS_LOCAL = [f"Item {i:02d}" for i in range(1, 26)]
LISTA_LADOS = ["Direito", "Esquerdo", "Centro / Único"]
OPCOES_CAIXA = ["Caixa com 12 garrafas", "Caixa com 6 garrafas", "Caixa com 3 garrafas", "Caixa com 2 garrafas", "Garrafa Avulsa (1 un)", "Outra quantidade"]

def obter_horario_brasilia():
    fuso_brasilia = timezone(timedelta(hours=-3))
    return datetime.now(fuso_brasilia)

def obter_saudacao():
    hora = obter_horario_brasilia().hour
    if 0 <= hora < 12: return "Bom dia"
    elif 12 <= hora < 18: return "Boa tarde"
    else: return "Boa noite"

def realizar_backup(nome):
    if os.path.exists(nome):
        ts = obter_horario_brasilia().strftime("%Y%m%d_%H%M%S")
        shutil.copy(nome, os.path.join(PASTA_BACKUP, f"backup_{ts}_{nome}"))

def carregar_dados():
    estoque = []
    if os.path.exists(NOME_ARQUIVO):
        try:
            with open(NOME_ARQUIVO, "r", encoding="utf-8") as f: 
                estoque = json.load(f)
        except: 
            pass
    if not estoque:
        estoque = [{
            "id": "1", 
            "nome": "Campana Merlot", 
            "tipo": "Tinto", 
            "safra": "2024", 
            "localizacao": "Corredor 01 - Pallet Item 01", 
            "lado": "Direito", 
            "caixa": "Caixa com 12 garrafas", 
            "codigo_barras": "7891008116632", 
            "foto": ""
        }]
    
    alterado = False
    for idx, item in enumerate(estoque):
        if "id" not in item or not item["id"]:
            item["id"] = f"vinho_{idx}_{int(obter_horario_brasilia().timestamp())}"
            alterado = True
    if alterado:
        salvar_dados(estoque)

    return sorted(estoque, key=lambda x: x.get("nome", "").lower())

def salvar_dados(estoque):
    estoque_ordenado = sorted(estoque, key=lambda x: x.get("nome", "").lower())
    with open(NOME_ARQUIVO, "w", encoding="utf-8") as f: 
        json.dump(estoque_ordenado, f, ensure_ascii=False, indent=4)
    realizar_backup(NOME_ARQUIVO)
    st.session_state.estoque = estoque_ordenado

def sincronizar_estoque_com_pedidos(pedidos, estoque):
    nomes_existentes = {v['nome'].lower() for v in estoque}
    alterado = False
    for p in pedidos:
        for item in p.get('itens', []):
            nome_item = item.get('nome', '').strip()
            if nome_item and nome_item.lower() not in nomes_existentes:
                novo_id = f"vinho_sinc_{len(estoque)}_{int(obter_horario_brasilia().timestamp())}"
                novo_v = {
                    "id": novo_id,
                    "nome": nome_item.title(),
                    "safra": item.get('safra', ''),
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
    logs.insert(0, {"data_hora": obter_horario_brasilia().strftime("%d/%m/%Y %H:%M:%S"), "usuario": usuario, "acao": acao, "detalhes": detalhes})
    with open(ARQUIVO_LOGS, "w", encoding="utf-8") as f: json.dump(logs, f, ensure_ascii=False, indent=4)

def carregar_pedidos():
    pedidos = []
    if os.path.exists(ARQUIVO_PEDIDOS):
        try:
            with open(ARQUIVO_PEDIDOS, "r", encoding="utf-8") as f: 
                pedidos = json.load(f)
        except: 
            pass
    for p in pedidos:
        if "itens" in p:
            for item in p["itens"]:
                if "qtd_separada" not in item:
                    item["qtd_separada"] = 0
                if "divergencia" not in item:
                    item["divergencia"] = 0
                if "autorizado_divergencia" not in item:
                    item["autorizado_divergencia"] = False
                if "separado" not in item:
                    item["separado"] = False
    return pedidos

def salvar_pedidos(pedidos):
    with open(ARQUIVO_PEDIDOS, "w", encoding="utf-8") as f: json.dump(pedidos, f, ensure_ascii=False, indent=4)

def interpretar_linha_pedido(texto_linha):
    texto = texto_linha.strip()
    safra = ""
    quantidade = 1
    
    partes = re.split(r'[/\|–\-]', texto)
    partes = [p.strip() for p in partes if p.strip()]
    
    nome = ""
    if len(partes) >= 3:
        nome = partes[0]
        safra_candidata = partes[1]
        if re.match(r'^(20\d{2})$', safra_candidata):
            safra = safra_candidata
        
        nums_qtd = re.findall(r'\d+', partes[2])
        if nums_qtd:
            quantidade = int(nums_qtd[0])
            
    elif len(partes) == 2:
        nome = partes[0]
        anos = re.findall(r'\b(20\d{2})\b', partes[1])
        if anos:
            safra = anos[0]
        
        nums = re.findall(r'\d+', partes[1])
        if nums:
            for n in nums:
                if n != safra:
                    quantidade = int(n)
                    break
    else:
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
        nome = re.sub(r'[/\|\-\–]+', '', texto_limpo).strip()

    return {
        "nome": nome.title(), 
        "safra": safra, 
        "quantidade": quantidade, 
        "separado": False, 
        "qtd_separada": 0, 
        "divergencia": 0, 
        "autorizado_divergencia": False
    }

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
                        "qtd_separada": 0,
                        "divergencia": 0,
                        "autorizado_divergencia": False
                    })
        elif ext == 'txt':
            linhas = [l.strip() for l in arq.getvalue().decode("utf-8").split("\n") if l.strip()]
            for l in linhas:
                itens.append(interpretar_linha_pedido(l))
    except: pass
    return itens

def componente_leitor_barcode(chave_sessao):
    html_code = f"""
    <div style="text-align: center; background: #FFF; padding: 10px; border-radius: 12px; border: 1px solid #E9ECEF;">
        <div id="reader_{chave_sessao}" style="width: 100%; max-width: 350px; margin: auto; border-radius: 8px; overflow: hidden;"></div>
        <p id="resultado_{chave_sessao}" style="font-weight: bold; color: #7A1C2E; margin-top: 8px; font-size: 0.9rem;"></p>
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
          html5QrCode.start({{ facingMode: "environment" }}, {{ fps: 10, qrbox: {{ width: 250, height: 120 }} }}, onScanSuccess).catch(err => {{}});
      }} catch (e) {{}}
    </script>
    """
    components.html(html_code, height=260)

if "usuarios" not in st.session_state:
    st.session_state.usuarios = carregar_usuarios()

st.session_state.estoque = carregar_dados()
st.session_state.pedidos = carregar_pedidos()
sincronizar_estoque_com_pedidos(st.session_state.pedidos, st.session_state.estoque)

if "menu_atual" not in st.session_state: st.session_state.menu_atual = "🏠 Home"
if "termo_busca" not in st.session_state: st.session_state.termo_busca = ""

qp = st.query_params

for key, val in list(qp.items()):
    if key.startswith("scanned_"):
        sess_key = key.replace("scanned_", "")
        valor_limpo = str(val).strip()
        if sess_key == "checkout_camera":
            st.session_state.codigo_bipado_checkout = valor_limpo
        elif sess_key == "leitor_geral":
            st.session_state.termo_busca = valor_limpo
            st.session_state.menu_atual = "Filtros"
        del st.query_params[key]
        st.rerun()

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
        st.markdown("<h1 style='text-align: center; color: #7A1C2E; font-size: 1.6rem;'>SEPARAÇÃO DE VINHO GALPÃO</h1>", unsafe_allow_html=True)
        
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
    st.markdown("<p style='text-align: center; color: #444; font-size: 0.95rem; margin-bottom: 25px;'>Separação de Vinho Galpão - Escolha a opção abaixo:</p>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📦 Checkout de Expedição", use_container_width=True): st.session_state.menu_atual = "PedidosMatriz"; st.rerun()
    with c2:
        if st.button("🏢 Painel da Matriz", use_container_width=True): st.session_state.menu_atual = "PainelMatriz"; st.rerun()
    with c3:
        if st.button("🔍 Buscar / Filtros", use_container_width=True): st.session_state.menu_atual = "Filtros"; st.rerun()
    
    st.write("")
    c4, c5, c6 = st.columns(3)
    with c4:
        if st.button("🗺️ Mapa de Separação", use_container_width=True): st.session_state.menu_atual = "MapaSeparacao"; st.rerun()
    with c5:
        if st.button("📷 Leitor / QR Code", use_container_width=True): st.session_state.menu_atual = "LeitorQR"; st.rerun()
    with c6:
        if st.button("🖨️ Gerar QR Codes", use_container_width=True): st.session_state.menu_atual = "GerarQR"; st.rerun()
        
    st.write("")
    c7, c8, c9 = st.columns(3)
    with c7:
        if st.button("🍷 Estoque Completo", use_container_width=True): st.session_state.menu_atual = "Estoque"; st.rerun()
    with c8:
        if st.button("➕ Cadastrar Vinho", use_container_width=True): st.session_state.menu_atual = "Cadastrar"; st.rerun()
    with c9:
        if st.button("✏️ Editar Vinho", use_container_width=True): st.session_state.menu_atual = "Editar"; st.rerun()

    st.write("")
    c10, c11, _ = st.columns(3)
    with c10:
        if st.button("📋 Histórico", use_container_width=True): st.session_state.menu_atual = "Historico"; st.rerun()
    with c11:
        if st.session_state.usuario_logado.get('cargo') == "Desenvolvedor":
            if st.button("⚙️ Gerenciar Contas", use_container_width=True):
                st.session_state.menu_atual = "GerenciarUsuarios"
                st.rerun()

elif st.session_state.menu_atual == "MapaSeparacao":
    st.subheader("🗺️ Mapa de Separação por Localização")
    st.markdown("Visualize os vinhos ordenados por corredor ou pesquise diretamente pelo nome do vinho desejado.")
    
    termo_mapa = st.text_input("🔍 Digite o nome do vinho para buscar no mapa:", value="")
    
    estoque_mapa = st.session_state.estoque
    if termo_mapa.strip():
        estoque_mapa = [v for v in estoque_mapa if termo_mapa.lower() in v['nome'].lower() or termo_mapa.lower() in v.get('localizacao', '').lower()]
    
    if not estoque_mapa:
        st.info("Nenhum vinho encontrado com o termo informado.")
    else:
        estoque_ordenado_local = sorted(estoque_mapa, key=lambda x: (x.get('localizacao', ''), x.get('nome', '')))
        for vinho in estoque_ordenado_local:
            st.markdown(f"""
            <div class='wine-card'>
                <div class='wine-title'>📍 {vinho.get('localizacao', 'Sem Local')} - Lado: {vinho.get('lado', 'N/A')}</div>
                <b>Vinho:</b> {vinho['nome']} ({vinho.get('safra', 'N/A')})<br>
                <b>Tipo:</b> {vinho.get('tipo', 'N/A')} | <b>Embalagem:</b> {vinho.get('caixa', 'N/A')}<br>
                <b>Cód. Barras:</b> {vinho.get('codigo_barras', 'Não cadastrado')}
            </div>
            """, unsafe_allow_html=True)

elif st.session_state.menu_atual == "Filtros":
    st.subheader("🔍 Buscar / Filtros no Estoque")
    busca = st.text_input("Pesquisar por nome ou código de barras:", value=st.session_state.termo_busca)
    st.session_state.termo_busca = ""
    
    vinhos_filtrados = st.session_state.estoque
    if busca.strip():
        vinhos_filtrados = [v for v in vinhos_filtrados if busca.lower() in v['nome'].lower() or busca in v.get('codigo_barras', '')]
    
    st.markdown(f"**Resultados encontrados:** {len(vinhos_filtrados)}")
    for v in vinhos_filtrados:
        st.markdown(f"""
        <div class='wine-card'>
            <div class='wine-title'>🍷 {v['nome']} ({v.get('safra', 'N/A')})</div>
            <b>Tipo:</b> {v.get('tipo', 'N/A')} | <b>Local:</b> {v.get('localizacao', 'N/A')} ({v.get('lado', 'N/A')})<br>
            <b>Caixa:</b> {v.get('caixa', 'N/A')} | <b>Cód. Barras:</b> {v.get('codigo_barras', 'N/A')}
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.menu_atual == "Estoque":
    st.subheader("🍷 Estoque Completo do Galpão")
    if not st.session_state.estoque:
        st.info("Estoque vazio.")
    else:
        df_est = pd.DataFrame(st.session_state.estoque)
        st.dataframe(df_est[['nome', 'tipo', 'safra', 'localizacao', 'lado', 'caixa', 'codigo_barras']], use_container_width=True)

elif st.session_state.menu_atual == "Cadastrar":
    st.subheader("➕ Cadastrar Novo Vinho no Estoque")
    with st.form("form_cadastrar_vinho"):
        nome_c = st.text_input("Nome do Vinho").strip().title()
        tipo_c = st.selectbox("Tipo", ["Tinto", "Branco", "Rosé", "Espumante", "Fortificado"])
        safra_c = st.text_input("Safra (Ano)").strip()
        corredor_c = st.selectbox("Corredor", LISTA_CORREDORES)
        tipo_local_c = st.selectbox("Tipo de Local", LISTA_LOCAIS_TIPO)
        numero_local_c = st.selectbox("Número do Local", LISTA_NUMEROS_LOCAL)
        lado_c = st.selectbox("Lado", LISTA_LADOS)
        caixa_c = st.selectbox("Embalagem / Caixa", OPCOES_CAIXA)
        codigo_barras_c = st.text_input("Código de Barras").strip()
        
        btn_salvar_novo = st.form_submit_button("Salvar Vinho")
        
        if btn_salvar_novo:
            if nome_c:
                localizacao_completa = f"{corredor_c} - {tipo_local_c} {numero_local_c}"
                novo_id = f"vinho_{len(st.session_state.estoque)}_{int(obter_horario_brasilia().timestamp())}"
                novo_vinho = {
                    "id": novo_id,
                    "nome": nome_c,
                    "tipo": tipo_c,
                    "safra": safra_c,
                    "localizacao": localizacao_completa,
                    "lado": lado_c,
                    "caixa": caixa_c,
                    "codigo_barras": codigo_barras_c,
                    "foto": ""
                }
                st.session_state.estoque.append(novo_vinho)
                salvar_dados(st.session_state.estoque)
                registrar_log(st.session_state.usuario_logado['nome'], "Cadastrou Vinho", nome_c)
                st.success(f"Vinho '{nome_c}' cadastrado com sucesso!")
                st.rerun()
            else:
                st.error("Informe o nome do vinho.")

elif st.session_state.menu_atual == "Editar":
    st.subheader("✏️ Editar ou Excluir Vinhos do Estoque")
    
    if not st.session_state.estoque:
        st.info("Nenhum vinho cadastrado para editar.")
    else:
        opcoes_vinhos = {f"{v['nome']} ({v.get('safra', 'S/ Safra')}) - Local: {v.get('localizacao', 'N/A')}": v['id'] for v in st.session_state.estoque}
        
        vinho_selecionado_label = st.selectbox("Selecione o Vinho para Editar:", list(opcoes_vinhos.keys()), key="select_vinho_edicao")
        id_vinho_selecionado = opcoes_vinhos[vinho_selecionado_label]
        
        vinho_obj = next((v for v in st.session_state.estoque if v['id'] == id_vinho_selecionado), None)
        
        if vinho_obj:
            with st.form("form_editar_vinho_completo"):
                st.markdown("#### Altere os campos desejados:")
                novo_nome = st.text_input("Nome do Vinho", value=vinho_obj.get('nome', '')).strip().title()
                
                tipos_disp = ["Tinto", "Branco", "Rosé", "Espumante", "Fortificado"]
                idx_tipo = tipos_disp.index(vinho_obj.get('tipo', 'Tinto')) if vinho_obj.get('tipo', 'Tinto') in tipos_disp else 0
                novo_tipo = st.selectbox("Tipo", tipos_disp, index=idx_tipo)
                
                nova_safra = st.text_input("Safra", value=vinho_obj.get('safra', '')).strip()
                nova_localizacao = st.text_input("Localização (Ex: Corredor 01 - Pallet Item 01)", value=vinho_obj.get('localizacao', '')).strip()
                
                lados_disp = LISTA_LADOS
                idx_lado = lados_disp.index(vinho_obj.get('lado', 'Centro / Único')) if vinho_obj.get('lado', 'Centro / Único') in lados_disp else 0
                novo_lado = st.selectbox("Lado", lados_disp, index=idx_lado)
                
                caixas_disp = OPCOES_CAIXA
                idx_caixa = caixas_disp.index(vinho_obj.get('caixa', 'Caixa com 12 garrafas')) if vinho_obj.get('caixa', 'Caixa com 12 garrafas') in caixas_disp else 0
                nova_caixa = st.selectbox("Embalagem / Caixa", caixas_disp, index=idx_caixa)
                
                novo_codigo_barras = st.text_input("Código de Barras", value=vinho_obj.get('codigo_barras', '')).strip()
                
                btn_atualizar_vinho = st.form_submit_button("💾 Salvar Alterações")
                
                if btn_atualizar_vinho:
                    if novo_nome:
                        vinho_obj['nome'] = novo_nome
                        vinho_obj['tipo'] = novo_tipo
                        vinho_obj['safra'] = nova_safra
                        vinho_obj['localizacao'] = nova_localizacao
                        vinho_obj['lado'] = novo_lado
                        vinho_obj['caixa'] = nova_caixa
                        vinho_obj['codigo_barras'] = novo_codigo_barras
                        
                        salvar_dados(st.session_state.estoque)
                        registrar_log(st.session_state.usuario_logado['nome'], "Editou Vinho", novo_nome)
                        st.success(f"Vinho '{novo_nome}' atualizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("O nome do vinho não pode ficar em branco.")

            st.markdown("---")
            st.markdown("#### 🗑️ Exclusão Individual de Vinho")
            if st.button(f"🗑️ Excluir permanentemente este vinho selecionado"):
                st.session_state.estoque = [v for v in st.session_state.estoque if v['id'] != id_vinho_selecionado]
                salvar_dados(st.session_state.estoque)
                registrar_log(st.session_state.usuario_logado['nome'], "Excluiu Vinho ID", id_vinho_selecionado)
                st.success("Vinho excluído com sucesso!")
                st.rerun()

elif st.session_state.menu_atual == "Historico":
    st.subheader("📋 Histórico de Auditoria e Logs")
    logs = carregar_logs()
    if not logs:
        st.info("Nenhum registro no histórico.")
    else:
        for l in logs:
            st.markdown(f"**[{l['data_hora']}] {l['usuario']}** - Ação: *{l['acao']}* | Detalhes: {l['detalhes']}")

elif st.session_state.menu_atual == "LeitorQR":
    st.subheader("📷 Leitor de Códigos de Barras / QR Code")
    componente_leitor_barcode("leitor_geral")

elif st.session_state.menu_atual == "GerenciarUsuarios":
    st.subheader("⚙️ Gerenciamento de Contas e Usuários")
    for u_item in st.session_state.usuarios:
        st.markdown(f"- **{u_item['nome']}** ({u_item.get('cargo', 'Operador')})")

elif st.session_state.menu_atual == "GerarQR":
    st.subheader("🖨️ Gerar QR Codes para Localizações")
    st.markdown("Selecione os corredores para gerar etiquetas de QR Code e código de barras.")
    corredor_gerar = st.selectbox("Escolha o Corredor:", LISTA_CORREDORES)
    if st.button("Gerar Etiquetas"):
        st.success(f"Gerando etiquetas para o {corredor_gerar}...")

elif st.session_state.menu_atual == "PainelMatriz":
    st.subheader("🏢 Painel da Matriz - Acompanhamento de Pedidos")
    st.markdown("Selecione abaixo o número do pedido que deseja visualizar:")
    
    if not st.session_state.pedidos:
        st.info("Nenhum pedido registrado no sistema.")
    else:
        mapas_disponiveis = [p['id'] for p in st.session_state.pedidos]
        
        c_sel1, _ = st.columns([2, 2])
        with c_sel1:
            pedido_selecionado_id = st.selectbox("🔍 Selecionar Pedido / Mapa:", mapas_disponiveis, key="select_painel_matriz")
            
        p = next((item for item in st.session_state.pedidos if item['id'] == pedido_selecionado_id), None)
        
        if p:
            status_col = "#2E7D32" if p.get('status') == "Concluído / Expedido" else "#7A1C2E"
            st.markdown(f"""
            <div style='background: #FFF; padding: 15px; border-radius: 10px; border: 1px solid #E9ECEF; margin-top: 15px; margin-bottom: 15px;'>
                <b>Mapa / Pedido Nº {p['id']}</b> | Data: {p['data']} | Status: <b style='color: {status_col};'>{p.get('status', 'Pendente')}</b>
            </div>
            """, unsafe_allow_html=True)
            
            df_itens = []
            for item in p['itens']:
                dif = item.get('divergencia', 0)
                if dif > 0: dif_str = f"({dif:+d}) ⚠️ Excedente"
                elif dif < 0: dif_str = f"({dif}) ⚠️ Falta"
                else: dif_str = "(0) Correto"
                    
                df_itens.append({
                    "Produto": item['nome'],
                    "Safra": item.get('safra', 'N/A'),
                    "Qtd Pedida": item['quantidade'],
                    "Qtd Separada": item.get('qtd_separada', 0),
                    "Divergência": dif_str
                })
            st.dataframe(pd.DataFrame(df_itens), use_container_width=True)

elif st.session_state.menu_atual == "PedidosMatriz":
    st.subheader("📦 Gestão de Pedidos - Separação de Vinho Galpão")
    
    aba_ped1, aba_ped2 = st.tabs(["📋 Enviar / Cadastrar / Excluir Pedidos", "🔍 Conferência (Checkout de Expedição)"])
    
    with aba_ped1:
        st.markdown("Cadastre o mapa de separação. Escolha abaixo se deseja usar o leitor de código de barras ou a digitação/arquivo para as caixas que não possuem código.")
        proximo_numero = len(st.session_state.pedidos) + 1
        id_sugerido = f"123{proximo_numero:03d}"
        
        if "itens_novo_pedido_temp" not in st.session_state:
            st.session_state.itens_novo_pedido_temp = []

        id_pedido = st.text_input("Código de Barras do Mapa (Ex: 1234552)", value=id_sugerido)
        
        st.markdown("---")
        # ADICIONADO: Seletor para ligar ou desligar o leitor de código de barras conforme a necessidade
        modo_adicao = st.radio(
            "Como deseja adicionar os itens neste pedido?",
            ["📷 Usar Leitor de Código de Barras (Câmera)", "📝 Digitação Manual / Arquivo (Caixas sem código)"],
            horizontal=True
        )

        if "📷" in modo_adicao:
            st.markdown("##### 📷 Leitor Ativo para Caminhar pelo Corredor")
            componente_leitor_barcode("cadastro_pedido_camera")
            
            codigo_lido_cadastro = st.session_state.get("codigo_bipado_cadastro_pedido_camera", "")
            if "scanned_cadastro_pedido_camera" in st.query_params:
                codigo_lido_cadastro = st.query_params["scanned_cadastro_pedido_camera"]
                del st.query_params["scanned_cadastro_pedido_camera"]

            if codigo_lido_cadastro:
                cod_limpo = str(codigo_lido_cadastro).strip()
                vinho_cad = next((v for v in st.session_state.estoque if str(v.get('codigo_barras', '')).strip() == cod_limpo), None)
                if vinho_cad:
                    encontrado_temp = False
                    for it in st.session_state.itens_novo_pedido_temp:
                        if it['nome'].lower() == vinho_cad['nome'].lower():
                            it['quantidade'] += 1
                            encontrado_temp = True
                            break
                    if not encontrado_temp:
                        st.session_state.itens_novo_pedido_temp.append({
                            "nome": vinho_cad['nome'],
                            "safra": vinho_cad.get('safra', ''),
                            "quantidade": 1,
                            "separado": False,
                            "qtd_separada": 0,
                            "divergencia": 0,
                            "autorizado_divergencia": False
                        })
                    st.success(f"✅ Adicionado à lista: **{vinho_cad['nome']}** (Local: {vinho_cad.get('localizacao')})")
                else:
                    st.error(f"❌ Código de barras '{cod_limpo}' não encontrado no estoque do galpão!")
        else:
            st.markdown("##### 📝 Inclusão Manual ou por Arquivo")
            arq_pedido = st.file_uploader("Envie Arquivo de Pedido (Excel ou TXT)", type=["xlsx", "xls", "txt"])
            texto_manual_pedido = st.text_area("Ou digite um item por linha (Nome / Safra / Qtd):", value="")

            if st.button("➕ Adicionar Linhas Digitadas à Lista"):
                if texto_manual_pedido.strip():
                    for linha in texto_manual_pedido.split("\n"):
                        if linha.strip():
                            st.session_state.itens_novo_pedido_temp.append(interpretar_linha_pedido(linha))
                    st.success("Itens adicionados com sucesso!")
                    st.rerun()

        st.markdown("---")
        if st.session_state.itens_novo_pedido_temp:
            st.markdown("##### 🛒 Itens na Lista do Novo Pedido:")
            for idx_t, it_t in enumerate(st.session_state.itens_novo_pedido_temp):
                st.write(f"- **{it_t['nome']}** (Safra: {it_t.get('safra', 'N/A')}) - Qtd: {it_t['quantidade']}")
            if st.button("🧹 Limpar Lista Temporária"):
                st.session_state.itens_novo_pedido_temp = []
                st.rerun()

        if st.button("💾 Salvar Pedido Completo no Sistema", use_container_width=True):
            itens_finais = list(st.session_state.itens_novo_pedido_temp)
            if 'arq_pedido' in locals() and arq_pedido is not None:
                itens_finais.extend(extrair_pedidos_de_arquivo(arq_pedido))

            if itens_finais:
                novo_registro_pedido = {
                    "id": str(id_pedido).strip(),
                    "data": obter_horario_brasilia().strftime("%d/%m/%Y %H:%M"),
                    "itens": itens_finais,
                    "status": "Pendente"
                }
                st.session_state.pedidos.append(novo_registro_pedido)
                salvar_pedidos(st.session_state.pedidos)
                sincronizar_estoque_com_pedidos(st.session_state.pedidos, st.session_state.estoque)
                registrar_log(st.session_state.usuario_logado['nome'], "Cadastrou Pedido", str(id_pedido))
                st.session_state.itens_novo_pedido_temp = []
                st.success(f"Pedido {id_pedido} salvo com sucesso!")
                st.rerun()
            else:
                st.error("Adicione itens à lista antes de salvar.")

        st.markdown("---")
        st.markdown("#### 🗑️ Excluir Pedidos Registrados")
        if st.session_state.pedidos:
            ids_pedidos_existentes = [p['id'] for p in st.session_state.pedidos]
            pedido_a_excluir = st.selectbox("Selecione o Pedido para Excluir:", ids_pedidos_existentes, key="select_excluir_pedido")
            if st.button("🗑️ Excluir Pedido Selecionado"):
                st.session_state.pedidos = [p for p in st.session_state.pedidos if p['id'] != pedido_a_excluir]
                salvar_pedidos(st.session_state.pedidos)
                registrar_log(st.session_state.usuario_logado['nome'], "Excluiu Pedido", str(pedido_a_excluir))
                st.success(f"Pedido {pedido_a_excluir} excluído com sucesso!")
                st.rerun()
        else:
            st.info("Nenhum pedido para excluir.")

    with aba_ped2:
        st.markdown("Faça a conferência bipando ou conferindo os itens para liberação da expedição.")
        if not st.session_state.pedidos:
            st.info("Nenhum pedido ativo para conferência.")
        else:
            ids_ativos = [p['id'] for p in st.session_state.pedidos if p.get('status') != "Concluído / Expedido"]
            if not ids_ativos:
                st.success("Todos os pedidos cadastrados já foram concluídos e expedidos!")
            else:
                pedido_conf_id = st.selectbox("Selecione o Pedido para Conferência:", ids_ativos, key="select_conf_pedido")
                pedido_obj = next((p for p in st.session_state.pedidos if p['id'] == pedido_conf_id), None)

                if pedido_obj:
                    st.markdown(f"**Status Atual:** {pedido_obj.get('status', 'Pendente')}")
                    
                    st.markdown("##### 📷 Leitor Câmera (Checkout)")
                    componente_leitor_barcode("checkout_camera")

                    codigo_bipado = st.session_state.get("codigo_bipado_checkout", "")
                    if "scanned_checkout_camera" in st.query_params:
                        codigo_bipado = st.query_params["scanned_checkout_camera"]
                        del st.query_params["scanned_checkout_camera"]

                    if codigo_bipado:
                        st.info(f"Último código capturado: {codigo_bipado}")
                        st.session_state.codigo_bipado_checkout = ""

                    st.markdown("---")
                    st.markdown("##### 📋 Itens do Pedido:")
                    
                    for idx, item in enumerate(pedido_obj['itens']):
                        col_i1, col_i2, col_i3 = st.columns([3, 1, 1])
                        with col_i1:
                            st.markdown(f"**{item['nome']}** (Safra: {item.get('safra', 'N/A')})<br>Qtd Pedida: <b>{item['quantidade']}</b>", unsafe_allow_html=True)
                        with col_i2:
                            qtd_sep = st.number_input(f"Qtd Sep. #{idx}", min_value=0, max_value=100, value=item.get('qtd_separada', item['quantidade']), key=f"qtd_sep_{pedido_conf_id}_{idx}")
                            item['qtd_separada'] = qtd_sep
                            item['divergencia'] = qtd_sep - item['quantidade']
                        with col_i3:
                            st.write("")
                            st.write("")
                            if item['divergencia'] != 0 and not item.get('autorizado_divergencia', False):
                                senha_div = st.text_input(f"Senha Diverg. #{idx}", type="password", key=f"pwd_div_{pedido_conf_id}_{idx}")
                                if st.button(f"Liberar #{idx}", key=f"btn_div_{pedido_conf_id}_{idx}"):
                                    if senha_div == SENHA_DIVERGENCIA:
                                        item['autorizado_divergencia'] = True
                                        st.success("Liberado!")
                                        st.rerun()
                                    else:
                                        st.error("Senha incorreta.")
                            else:
                                st.markdown("✅ OK")
                        st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)

                    if st.button("🚀 Finalizar e Expedir Pedido", use_container_width=True):
                        bloqueio = False
                        for it in pedido_obj['itens']:
                            if it['divergencia'] != 0 and not it.get('autorizado_divergencia', False):
                                bloqueio = True
                                break
                        
                        if bloqueio:
                            st.error("Existem itens com divergência não autorizados pela gerência (Senha 2026).")
                        else:
                            pedido_obj['status'] = "Concluído / Expedido"
                            salvar_pedidos(st.session_state.pedidos)
                            registrar_log(st.session_state.usuario_logado['nome'], "Expediu Pedido", str(pedido_conf_id))
                            st.success(f"Pedido {pedido_conf_id} expedido com sucesso!")
                            st.rerun()
