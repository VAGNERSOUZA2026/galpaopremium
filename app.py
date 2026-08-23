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
        estoque = [{"nome": "Campana Merlot", "tipo": "Tinto", "safra": "2024", "localizacao": "Corredor 01 - Pallet Item 01", "lado": "Direito", "caixa": "Caixa com 12 garrafas", "codigo_barras": "7891008116632", "foto": ""}]
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
                novo_v = {
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
    return {"nome": nome, "safra": safra, "quantidade": quantidade, "separado": False, "qtd_separada": 0, "divergencia": 0, "autorizado_divergencia": False}

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
        if st.button("🍷 Estoque Completo", use_container_width=True): st.session_state.menu_atual = "Estoque"; st.rerun()
    with c6:
        if st.button("➕ Cadastrar Vinho", use_container_width=True): st.session_state.menu_atual = "Cadastrar"; st.rerun()
        
    st.write("")
    c7, c8, c9 = st.columns(3)
    with c7:
        if st.button("✏️ Editar Vinho", use_container_width=True): st.session_state.menu_atual = "Editar"; st.rerun()
    with c8:
        if st.button("📋 Histórico", use_container_width=True): st.session_state.menu_atual = "Historico"; st.rerun()
    with c9:
        if st.session_state.usuario_logado.get('cargo') == "Desenvolvedor":
            if st.button("⚙️ Gerenciar Contas", use_container_width=True):
                st.session_state.menu_atual = "GerenciarUsuarios"
                st.rerun()

elif st.session_state.menu_atual == "PainelMatriz":
    st.subheader("🏢 Painel da Matriz - Acompanhamento de Pedidos")
    st.markdown("Aqui a Matriz visualiza em tempo real todos os pedidos salvos, finalizados e as divergências de quantidade registradas pelo galpão.")
    
    if not st.session_state.pedidos:
        st.info("Nenhum pedido registrado no sistema.")
    else:
        for p in st.session_state.pedidos:
            status_col = "#2E7D32" if p.get('status') == "Concluído / Expedido" else "#7A1C2E"
            st.markdown(f"""
            <div style='background: #FFF; padding: 15px; border-radius: 10px; border: 1px solid #E9ECEF; margin-bottom: 15px;'>
                <b>Mapa / Pedido Nº {p['id']}</b> | Data: {p['data']} | Status: <b style='color: {status_col};'>{p.get('status', 'Pendente')}</b>
            </div>
            """, unsafe_allow_html=True)
            
            df_itens = []
            for item in p['itens']:
                dif = item.get('divergencia', 0)
                if dif > 0:
                    dif_str = f"({dif:+d}) ⚠️ Excedente"
                elif dif < 0:
                    dif_str = f"({dif}) ⚠️ Falta"
                else:
                    dif_str = "(0) Correto"
                    
                df_itens.append({
                    "Produto": item['nome'],
                    "Safra": item.get('safra', 'N/A'),
                    "Qtd Pedida": item['quantidade'],
                    "Qtd Separada": item.get('qtd_separada', 0),
                    "Divergência": dif_str
                })
            st.dataframe(pd.DataFrame(df_itens), use_container_width=True)
            st.markdown("---")

elif st.session_state.menu_atual == "PedidosMatriz":
    st.subheader("📦 Checkout de Expedição - Separação de Vinho Galpão")
    
    aba_ped1, aba_ped2 = st.tabs(["📋 Enviar / Cadastrar / Excluir Pedidos", "🔍 Conferência (Checkout de Expedição)"])
    
    with aba_ped1:
        st.markdown("Cadastre o mapa de separação enviado pela matriz (via arquivo Excel, TXT ou digitação manual).")
        proximo_numero = len(st.session_state.pedidos) + 1
        id_sugerido = f"123{proximo_numero:03d}"
        
        with st.form("form_novo_pedido"):
            id_pedido = st.text_input("Código de Barras do Mapa (Ex: 1234552)", value=id_sugerido)
            arq_pedido = st.file_uploader("Arquivo de Pedido (Excel ou TXT)", type=["xlsx", "xls", "txt"])
            texto_manual_pedido = st.text_area("Ou digite os itens (Ex: Faleria Pinot Noir Reserva 23 / 1 Caixa)")
            
            if st.form_submit_button("💾 Salvar Pedido no Sistema"):
                itens_novos = []
                if arq_pedido is not None:
                    itens_novos = extrair_pedidos_de_arquivo(arq_pedido)
                if texto_manual_pedido.strip():
                    for linha in texto_manual_pedido.split("\n"):
                        if linha.strip():
                            item_interpretado = interpretar_linha_pedido(linha)
                            itens_novos.append(item_interpretado)

                if itens_novos:
                    novo_registro_pedido = {
                        "id": str(id_pedido).strip(),
                        "data": obter_horario_brasilia().strftime("%d/%m/%Y %H:%M"),
                        "itens": itens_novos,
                        "status": "Pendente"
                    }
                    st.session_state.pedidos.append(novo_registro_pedido)
                    salvar_pedidos(st.session_state.pedidos)
                    sincronizar_estoque_com_pedidos(st.session_state.pedidos, st.session_state.estoque)
                    registrar_log(st.session_state.usuario_logado['nome'], "Novo Pedido Matriz", str(id_pedido))
                    st.success(f"Pedido / Mapa {id_pedido} cadastrado e salvo com sucesso!")
                    st.rerun()
                else:
                    st.error("Adicione ao menos um item ou arquivo válido.")
                    
        st.markdown("---")
        st.markdown("#### 🗑️ Gerenciamento e Exclusão de Pedidos (Limpeza Semanal)")
        if st.session_state.pedidos:
            lista_ids_pedidos = [p['id'] for p in st.session_state.pedidos]
            mapas_para_excluir = st.multiselect("Selecione os pedidos concluídos ou antigos para excluir:", lista_ids_pedidos)
            if st.button("🗑️ Excluir Pedidos Selecionados"):
                st.session_state.pedidos = [p for p in st.session_state.pedidos if p['id'] not in mapas_para_excluir]
                salvar_pedidos(st.session_state.pedidos)
                registrar_log(st.session_state.usuario_logado['nome'], "Exclusão de Pedidos Antigos", str(mapas_para_excluir))
                st.success("Pedidos selecionados excluídos com sucesso!")
                st.rerun()
        else:
            st.info("Nenhum pedido cadastrado no momento.")

    with aba_ped2:
        if not st.session_state.pedidos:
            st.warning("Nenhum pedido cadastrado no sistema. Cadastre na aba anterior.")
        else:
            mapas_disponiveis = [p['id'] for p in st.session_state.pedidos]
            
            c_top1, _ = st.columns([2, 2])
            with c_top1:
                mapa_selecionado_id = st.selectbox("Código de Barras Mapa", mapas_disponiveis)
            
            pedido_ativo = next((p for p in st.session_state.pedidos if p['id'] == mapa_selecionado_id), None)
            
            if pedido_ativo:
                status_atual = pedido_ativo.get('status', 'Pendente')
                cor_status = "#2E7D32" if status_atual == "Concluído / Expedido" else "#7A1C2E"
                
                st.markdown(f"""
                <div style='background: #FFF; padding: 10px; border-radius: 8px; border: 1px solid #E9ECEF; margin-bottom: 15px;'>
                    <b>Conferência do Mapa cod. {pedido_ativo['id']}</b> | Expedição Nº 41542 | Carga(s) Nº 114971<br>
                    Data/Carga: {pedido_ativo['data']} | Status: <b style='color: {cor_status};'>{status_atual}</b>
                </div>
                """, unsafe_allow_html=True)
                
                modo_leitura = st.radio("Forma de Leitura:", ["⌨️ Seleção / Pistola USB", "📷 Câmera do Celular"], horizontal=True)
                
                codigo_capturado = ""
                if modo_leitura == "📷 Câmera do Celular":
                    st.markdown("Aponte a câmera para o código de barras ou QR Code:")
                    componente_leitor_barcode("checkout_camera")
                    codigo_capturado = st.session_state.get("codigo_bipado_checkout", "")
                
                itens_pendentes_lista = [i['nome'] for i in pedido_ativo['itens'] if not i.get('separado', False)]
                
                col_b1, col_b2, col_b3 = st.columns([2, 1, 1])
                with col_b1:
                    if modo_leitura == "📷 Câmera do Celular":
                        cod_barras_input = st.text_input("*Código de Barras ou Nome", value=codigo_capturado, key="input_bipagem_checkout")
                    else:
                        if itens_pendentes_lista:
                            opcao_selecionada_dropdown = st.selectbox("*Selecione o Vinho da Lista ou Digite/Bipe", ["-- Selecione ou Digite --"] + itens_pendentes_lista, key="select_vinho_checkout")
                            if opcao_selecionada_dropdown != "-- Selecione ou Digite --":
                                cod_barras_input = opcao_selecionada_dropdown
                            else:
                                cod_barras_input = st.text_input("*Ou digite/bipe o Código de Barras", value="", key="input_bipagem_checkout")
                        else:
                            cod_barras_input = st.text_input("*Código de Barras ou Nome", value="", key="input_bipagem_checkout")
                with col_b2:
                    if "input_qtd_checkout" not in st.session_state:
                        st.session_state.input_qtd_checkout = 1
                    qtd_input = st.number_input("*Qtd", min_value=1, key="input_qtd_checkout")
                with col_b3:
                    st.write("")
                    btn_conferir = st.button("Conferir", use_container_width=True)
                
                if btn_conferir and cod_barras_input and cod_barras_input != "-- Selecione ou Digite --":
                    encontrou = False
                    qtd_real_informada = int(st.session_state.get("input_qtd_checkout", 1))
                    
                    for item in pedido_ativo['itens']:
                        if item.get('separado', False) and item.get('divergencia', 0) == 0:
                            continue

                        vinho_no_estoque = next((v for v in st.session_state.estoque if v['nome'].lower() in item['nome'].lower() or v.get('codigo_barras') == cod_barras_input), None)
                        
                        match_nome = cod_barras_input.lower() in item['nome'].lower()
                        match_bc = vinho_no_estoque and vinho_no_estoque.get('codigo_barras') == cod_barras_input
                        
                        if match_nome or match_bc:
                            encontrou = True
                            item['qtd_separada'] = qtd_real_informada
                            item['divergencia'] = item['qtd_separada'] - item['quantidade']
                            
                            if item['divergencia'] == 0:
                                item['autorizado_divergencia'] = True
                                item['separado'] = True
                            else:
                                item['autorizado_divergencia'] = False
                                item['separado'] = False
                                dif_tipo = "mais" if item['divergencia'] > 0 else "menos"
                                st.warning(f"⚠️ Atenção! Quantidade separada ({item['qtd_separada']}) diverge para {dif_tipo} da pedida ({item['quantidade']}) para o item '{item['nome']}'. O item foi bloqueado até a digitação correta da senha.")
                            break
                    
                    if encontrou:
                        if "codigo_bipado_checkout" in st.session_state:
                            st.session_state.codigo_bipado_checkout = ""
                        salvar_pedidos(st.session_state.pedidos)
                        st.rerun()
                    else:
                        st.error("Produto não encontrado neste mapa ou já totalmente conferido.")

                itens_com_divergencia_nao_autorizados = [i for i in pedido_ativo['itens'] if i.get('divergencia', 0) != 0 and not i.get('autorizado_divergencia', False)]
                
                if itens_com_divergencia_nao_autorizados:
                    st.markdown("---")
                    st.error("🔒 Existem itens com quantidade incorreta / divergente aguardando correção ou liberação de senha (Senha: 2026):")
                    for it_div in itens_com_divergencia_nao_autorizados:
                        # REESTRUTURADO TOTALMENTE SEM ST.FORM PARA ELIMINAR O PROBLEMA DO ENTER ACIDENTAL
                        st.markdown(f"**Item:** {it_div['nome']} | Pedido: {it_div['quantidade']} | Separado: {it_div['qtd_separada']} (Divergência: {it_div['divergencia']:+d})")
                        
                        c_acao1, c_acao2 = st.columns(2)
                        with c_acao1:
                            if st.button("🔄 Corrigir para Qtd Pedida", key=f"corrigir_{it_div['nome']}"):
                                it_div['qtd_separada'] = it_div['quantidade']
                                it_div['divergencia'] = 0
                                it_div['autorizado_divergencia'] = True
                                it_div['separado'] = True
                                salvar_pedidos(st.session_state.pedidos)
                                st.success(f"Quantidade de '{it_div['nome']}' corrigida com sucesso!")
                                st.rerun()
                                
                        senha_chave_input = f"pass_{it_div['nome']}"
                        senha_item = st.text_input("Digite a senha de liberação de divergência (2026):", type="password", key=senha_chave_input)
                        
                        if st.button("Autorizar Com Divergência", key=f"btn_autorizar_{it_div['nome']}"):
                            if senha_item == SENHA_DIVERGENCIA:
                                it_div['autorizado_divergencia'] = True
                                it_div['separado'] = True
                                salvar_pedidos(st.session_state.pedidos)
                                registrar_log(st.session_state.usuario_logado['nome'], "Liberou Divergência Item", it_div['nome'])
                                st.success(f"Divergência autorizada para '{it_div['nome']}'!")
                                st.rerun()
                            else:
                                st.error("Senha incorreta ou em branco. Digite 2026 e clique explicitamente no botão.")
                        st.markdown("---")

                with st.expander("➕ Inserção Manual Extra (Solicitação de Trajeto / Adicionar Vinho Não Listado)"):
                    with st.form("form_vinho_extra"):
                        nome_extra = st.text_input("Nome do Vinho Extra").strip().title()
                        qtd_extra = st.number_input("Quantidade", min_value=1, value=1)
                        senha_extra = st.text_input("Senha de Liberação (2026)", type="password")
                        if st.form_submit_button("Adicionar ao Pedido com Senha"):
                            if nome_extra:
                                if senha_extra == SENHA_DIVERGENCIA:
                                    novo_item_extra = {
                                        "nome": nome_extra,
                                        "safra": "Extra",
                                        "quantidade": 0,
                                        "separado": True,
                                        "qtd_separada": qtd_extra,
                                        "divergencia": qtd_extra,
                                        "autorizado_divergencia": True
                                    }
                                    pedido_ativo['itens'].append(novo_item_extra)
                                    salvar_pedidos(st.session_state.pedidos)
                                    st.success("Vinho extra incluído e autorizado com sucesso!")
                                    st.rerun()
                                else:
                                    st.error("Senha incorreta para item extra. Digite 2026.")
                            else:
                                st.error("Informe o nome do vinho.")

                st.markdown("---")
                
                col_esq, col_dir = st.columns(2)
                
                with col_esq:
                    st.markdown("<h4 style='color: #7A1C2E;'>PRODUTOS A CONFERIR</h4>", unsafe_allow_html=True)
                    pendentes = [i for i in pedido_ativo['itens'] if not i.get('separado', False)]
                    if not pendentes:
                        st.success("🎉 Todos os produtos deste mapa foram conferidos!")
                    for item in pendentes:
                        st.markdown(f"""
                        <div style='background: #FFF; padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid #7A1C2E;'>
                            <b>{item['nome']}</b> (Safra: {item.get('safra', 'N/A')})<br>
                            Qtd Pedida: <b>{item['quantidade']}</b> | Separada: {item.get('qtd_separada', 0)}
                        </div>
                        """, unsafe_allow_html=True)
                        
                with col_dir:
                    st.markdown("<h4 style='color: #2E7D32;'>PRODUTOS JÁ CONFERIDOS</h4>", unsafe_allow_html=True)
                    conferidos = [i for i in pedido_ativo['itens'] if i.get('separado', False)]
                    if not conferidos:
                        st.info("Nenhum produto conferido ainda.")
                    for item in conferidos:
                        dif = item.get('divergencia', 0)
                        if dif != 0:
                            dif_texto = f" | <span style='color: red;'>Divergência: {dif:+d}</span>"
                        else:
                            dif_texto = " | <span style='color: green;'>Correto</span>"
                            
                        st.markdown(f"""
                        <div style='background: #FFF; padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid #2E7D32;'>
                            <b>{item['nome']}</b> (Safra: {item.get('safra', 'N/A')}){dif_texto}<br>
                            Qtd Pedida: <b>{item['quantidade']}</b> | Separada: <b>{item.get('qtd_separada', 0)}</b>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                todos_conferidos = all(i.get('separado', False) for i in pedido_ativo['itens'])
                todas_divergencias_ok = all(i.get('autorizado_divergencia', False) for i in pedido_ativo['itens'] if i.get('divergencia', 0) != 0)
                
                if todos_conferidos and todas_divergencias_ok:
                    if st.button("🚀 Concluir e Finalizar Expedição deste Mapa", use_container_width=True):
                        pedido_ativo['status'] = "Concluído / Expedido"
                        salvar_pedidos(st.session_state.pedidos)
                        registrar_log(st.session_state.usuario_logado['nome'], "Finalizou Expedição Mapa", pedido_ativo['id'])
                        st.success("🎉 Expedição concluída com sucesso! O painel da matriz foi atualizado.")
                        st.rerun()
                else:
                    st.warning("⚠️ Para concluir a expedição, todos os itens precisam estar conferidos e eventuais divergências autorizadas por senha.")

elif st.session_state.menu_atual == "Filtros":
    st.subheader("🔍 Buscar e Filtrar Vinhos no Galpão")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        termo = st.text_input("Pesquisar por nome, tipo ou safra:", value=st.session_state.termo_busca)
    with col_f2:
        tipo_filtro = st.selectbox("Filtrar por Tipo:", ["Todos", "Tinto", "Branco", "Rosé", "Espumante", "Fortificado"])
        
    estoque = st.session_state.estoque
    
    resultados = []
    for v in estoque:
        match_termo = termo.lower() in v['nome'].lower() or termo.lower() in v.get('safra', '').lower() or termo.lower() in v.get('tipo', '').lower()
        match_tipo = tipo_filtro == "Todos" or v.get('tipo') == tipo_filtro
        
        if match_termo and match_tipo:
            resultados.append(v)
            
    st.markdown(f"**Total de vinhos encontrados:** {len(resultados)}")
    st.markdown("---")
    
    if not resultados:
        st.info("Nenhum vinho encontrado com os filtros informados.")
    else:
        for vinho in resultados:
            st.markdown(f"""
            <div class="wine-card">
                <div class="wine-title">🍷 {vinho['nome']} ({vinho.get('safra', 'N/A')})</div>
                <p style='margin: 2px 0; color: #555;'><b>Tipo:</b> {vinho.get('tipo', 'Tinto')} | <b>Caixa:</b> {vinho.get('caixa', 'N/A')}</p>
                <p style='margin: 2px 0; color: #555;'><b>Localização:</b> 📍 {vinho['localizacao']} ({vinho.get('lado', 'N/A')})</p>
                <p style='margin: 2px 0; color: #777; font-size: 0.85rem;'><b>Cód. Barras:</b> {vinho.get('codigo_barras', 'Não cadastrado')}</p>
            </div>
            """, unsafe_allow_html=True)

elif st.session_state.menu_atual == "MapaSeparacao":
    st.subheader("🗺️ Mapa de Separação do Galpão")
    st.markdown("Visualize a distribuição dos corredores e pallet/prateleiras para otimizar o trajeto de separação.")
    
    corredor_selecionado = st.selectbox("Selecione o Corredor para visualizar os vinhos:", LISTA_CORREDORES)
    
    vinhos_corredor = [v for v in st.session_state.estoque if corredor_selecionado.lower() in v['localizacao'].lower()]
    
    st.markdown(f"#### 📍 {corredor_selecionado} ({len(vinhos_corredor)} vinhos alocados)")
    
    if not vinhos_corredor:
        st.info(f"Nenhum vinho cadastrado neste corredor no momento.")
    else:
        for v in vinhos_corredor:
            st.markdown(f"""
            <div style='background: #FFF; padding: 12px; border-radius: 10px; border: 1px solid #E9ECEF; margin-bottom: 10px;'>
                <b>{v['nome']}</b> ({v.get('safra', 'N/A')}) - <i>{v.get('tipo', 'Tinto')}</i><br>
                Local: <b>{v['localizacao']}</b> | Lado: <b>{v.get('lado', 'N/A')}</b> | Embalagem: {v.get('caixa', 'N/A')}
            </div>
            """, unsafe_allow_html=True)

elif st.session_state.menu_atual == "Estoque":
    st.subheader("🍷 Estoque Completo do Galpão")
    st.markdown("Lista completa de todos os rótulos cadastrados no sistema.")
    
    estoque = st.session_state.estoque
    if not estoque:
        st.info("Estoque vazio.")
    else:
        df_estoque = pd.DataFrame([{
            "Nome": v['nome'],
            "Tipo": v.get('tipo', 'Tinto'),
            "Safra": v.get('safra', ''),
            "Localização": v['localizacao'],
            "Lado": v.get('lado', ''),
            "Caixa": v.get('caixa', ''),
            "Cód. Barras": v.get('codigo_barras', '')
        } for v in estoque])
        
        st.dataframe(df_estoque, use_container_width=True)

elif st.session_state.menu_atual == "Cadastrar":
    st.subheader("➕ Cadastrar Novo Vinho no Galpão")
    
    with st.form("form_cadastrar_vinho"):
        nome = st.text_input("*Nome do Vinho").strip().title()
        tipo = st.selectbox("Tipo de Vinho", ["Tinto", "Branco", "Rosé", "Espumante", "Fortificado"])
        safra = st.text_input("Safra (Ex: 2023)").strip()
        
        col_l1, col_l2, col_l3, col_l4 = st.columns(4)
        with col_l1:
            corredor = st.selectbox("Corredor", LISTA_CORREDORES)
        with col_l2:
            local_tipo = st.selectbox("Tipo Local", LISTA_LOCAIS_TIPO)
        with col_l3:
            num_local = st.selectbox("Número Item", LISTA_NUMEROS_LOCAL)
        with col_l4:
            lado = st.selectbox("Lado", LISTA_LADOS)
            
        caixa = st.selectbox("Embalagem / Caixa", OPCOES_CAIXA)
        codigo_barras = st.text_input("Código de Barras (Opcional)").strip()
        
        if st.form_submit_button("💾 Salvar Novo Vinho"):
            if nome:
                localizacao_completa = f"{corredor} - {local_tipo} {num_local}"
                novo_vinho = {
                    "nome": nome,
                    "tipo": tipo,
                    "safra": safra,
                    "localizacao": localizacao_completa,
                    "lado": lado,
                    "caixa": caixa,
                    "codigo_barras": codigo_barras,
                    "foto": ""
                }
                st.session_state.estoque.append(novo_vinho)
                salvar_dados(st.session_state.estoque)
                registrar_log(st.session_state.usuario_logado['nome'], "Cadastrou Vinho", nome)
                st.success(f"Vinho '{nome}' cadastrado com sucesso!")
                st.rerun()
            else:
                st.error("Informe o nome do vinho.")

elif st.session_state.menu_atual == "Editar":
    st.subheader("✏️ Editar ou Remover Vinho do Estoque")
    
    nomes_estoque = [v['nome'] for v in st.session_state.estoque]
    if not nomes_estoque:
        st.info("Nenhum vinho para editar.")
    else:
        vinho_escolhido = st.selectbox("Selecione o Vinho:", nomes_estoque)
        vinho_obj = next((v for v in st.session_state.estoque if v['nome'] == vinho_escolhido), None)
        
        if vinho_obj:
            with st.form("form_editar_vinho"):
                novo_nome = st.text_input("Nome do Vinho", value=vinho_obj['nome']).strip().title()
                tipos_op = ["Tinto", "Branco", "Rosé", "Espumante", "Fortificado"]
                idx_tipo = tipos_op.index(vinho_obj.get('tipo', 'Tinto')) if vinho_obj.get('tipo', 'Tinto') in tipos_op else 0
                novo_tipo = st.selectbox("Tipo de Vinho", tipos_op, index=idx_tipo)
                nova_safra = st.text_input("Safra", value=vinho_obj.get('safra', '')).strip()
                nova_caixa = st.selectbox("Embalagem / Caixa", OPCOES_CAIXA, index=0)
                novo_cb = st.text_input("Código de Barras", value=vinho_obj.get('codigo_barras', '')).strip()
                
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    btn_salvar_edicao = st.form_submit_button("💾 Salvar Alterações")
                with col_e2:
                    btn_excluir_vinho = st.form_submit_button("🗑️ Excluir Vinho do Estoque")
                    
                if btn_salvar_edicao:
                    vinho_obj['nome'] = novo_nome
                    vinho_obj['tipo'] = novo_tipo
                    vinho_obj['safra'] = nova_safra
                    vinho_obj['caixa'] = nova_caixa
                    vinho_obj['codigo_barras'] = novo_cb
                    salvar_dados(st.session_state.estoque)
                    registrar_log(st.session_state.usuario_logado['nome'], "Editou Vinho", novo_nome)
                    st.success("Alterações salvas com sucesso!")
                    st.rerun()
                    
                if btn_excluir_vinho:
                    st.session_state.estoque = [v for v in st.session_state.estoque if v['nome'] != vinho_escolhido]
                    salvar_dados(st.session_state.estoque)
                    registrar_log(st.session_state.usuario_logado['nome'], "Excluiu Vinho", vinho_escolhido)
                    st.success("Vinho excluído do estoque com sucesso!")
                    st.rerun()

elif st.session_state.menu_atual == "Historico":
    st.subheader("📋 Histórico de Auditoria e Logs do Galpão")
    logs = carregar_logs()
    if not logs:
        st.info("Nenhum registro de log encontrado.")
    else:
        df_logs = pd.DataFrame(logs)
        st.dataframe(df_logs, use_container_width=True)

elif st.session_state.menu_atual == "GerenciarUsuarios":
    st.subheader("⚙️ Gerenciamento de Contas e Usuários")
    st.markdown("Adicione ou remova operadores do sistema.")
    
    with st.form("form_novo_operador"):
        nome_op = st.text_input("Nome do Novo Operador").strip().title()
        senha_op = st.text_input("Senha Inicial", type="password").strip()
        cargo_op = st.selectbox("Cargo", ["Operador", "Administrador"])
        
        if st.form_submit_button("Cadastrar Usuário"):
            if nome_op and senha_op:
                st.session_state.usuarios.append({"nome": nome_op, "cargo": cargo_op, "senha": senha_op})
                salvar_usuarios(st.session_state.usuarios)
                st.success(f"Usuário {nome_op} cadastrado com sucesso!")
                st.rerun()
            else:
                st.error("Preencha todos os campos.")
                
    st.markdown("---")
    st.markdown("#### Usuários Atuais:")
    for u in st.session_state.usuarios:
        st.markdown(f"- **{u['nome']}** ({u.get('cargo', 'Operador')})")
