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
        estoque = [
            {"nome": "La Consulta Malbec", "tipo": "Tinto", "safra": "2024", "localizacao": "Corredor 01 - Pallet Item 01", "lado": "Direito", "caixa": "Caixa com 12 garrafas", "codigo_barras": "7891008116632", "foto": ""},
            {"nome": "Quereu Carmenere", "tipo": "Tinto", "safra": "2025", "localizacao": "Corredor 01 - Pallet Item 02", "lado": "Esquerdo", "caixa": "Caixa com 12 garrafas", "codigo_barras": "7891008116633", "foto": ""}
        ]
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
    ativo_key = f"camera_ativa_{chave_sessao}"
    if ativo_key not in st.session_state:
        st.session_state[ativo_key] = False

    col_btn1, col_btn2 = st.columns([1, 2])
    with col_btn1:
        if not st.session_state[ativo_key]:
            if st.button("📷 Abrir Câmera", key=f"btn_on_{chave_sessao}"):
                st.session_state[ativo_key] = True
                st.rerun()
        else:
            if st.button("❌ Fechar Câmera", key=f"btn_off_{chave_sessao}"):
                st.session_state[ativo_key] = False
                st.rerun()

    if st.session_state[ativo_key]:
        html_code = f"""
        <div style="text-align: center; background: #FFF; padding: 10px; border-radius: 12px; border: 1px solid #E9ECEF; margin-top: 10px;">
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
            st.session_state["camera_ativa_checkout_camera"] = False
        elif sess_key == "consulta_camera":
            st.session_state.codigo_bipado_consulta = valor_limpo
            st.session_state["camera_ativa_consulta_camera"] = False
        elif sess_key == "cadastro_camera":
            st.session_state.codigo_barras_cadastrado = valor_limpo
            st.session_state["camera_ativa_cadastro_camera"] = False
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
        if st.button("📱 Gerar QR Code Pallet", use_container_width=True): st.session_state.menu_atual = "GerarQRCode"; st.rerun()
    with c9:
        if st.button("📷 Ler QR Code (Corredor)", use_container_width=True): st.session_state.menu_atual = "LerQRCode"; st.rerun()

    st.write("")
    c10, c11 = st.columns(2)
    with c10:
        if st.button("📋 Histórico", use_container_width=True): st.session_state.menu_atual = "Historico"
    with c11:
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
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_num_pedido = st.text_input("🔍 Filtrar por Número do Pedido / Mapa", value="")
        with col_f2:
            filtro_data = st.text_input("📅 Filtrar por Data (Ex: DD/MM/AAAA ou parte dela)", value="")
            
        pedidos_filtrados = st.session_state.pedidos
        if filtro_num_pedido.strip():
            pedidos_filtrados = [p for p in pedidos_filtrados if filtro_num_pedido.strip().lower() in str(p.get('id', '')).lower()]
        if filtro_data.strip():
            pedidos_filtrados = [p for p in pedidos_filtrados if filtro_data.strip() in str(p.get('data', ''))]
            
        if not pedidos_filtrados:
            st.warning("Nenhum pedido corresponde aos filtros informados.")
        else:
            for p in pedidos_filtrados:
                status_col = "#2E7D32" if p.get('status') == "Concluído / Expedido" else "#7A1C2E"
                st.markdown(f"""
                <div style='background: #FFF; padding: 15px; border-radius: 10px; border: 1px solid #E9ECEF; margin-bottom: 15px;'>
                    <b>Mapa / Pedido Nº {p['id']}</b> | Data: {p['data']} | Status: <b style='color: {status_col};'>{p.get('status', 'Pendente')}</b>
                </div>
                """, unsafe_allow_html=True)
                
                df_itens = []
                for item in p['itens']:
                    dif = item.get('divergencia', 0)
                    dif_str = f"({dif:+d})" if dif != 0 else "(0)"
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
            texto_manual_pedido = st.text_area("Ou digite os itens (Ex: La Consulta Malbec 2024 / Caixa com 12 garrafas)")
            
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
                    registrar_log(st.session_state.usuario_logado['nome'], "Cadastrar Pedido", f"Pedido/Mapa {id_pedido} cadastrado.")
                    st.success("✅ Pedido cadastrado com sucesso!")
                    st.rerun()
                else:
                    st.error("⚠️ Nenhum item válido foi encontrado no arquivo ou texto digitado.")

        st.markdown("---")
        st.markdown("### 🗑️ Excluir Pedidos Cadastrados")
        if not st.session_state.pedidos:
            st.info("Nenhum pedido para excluir.")
        else:
            ids_disponiveis = [p['id'] for p in st.session_state.pedidos]
            pedido_para_excluir = st.selectbox("Selecione o ID do Pedido / Mapa para Excluir", ids_disponiveis)
            if st.button("🗑️ Excluir Pedido Selecionado"):
                st.session_state.pedidos = [p for p in st.session_state.pedidos if str(p['id']) != str(pedido_para_excluir)]
                salvar_pedidos(st.session_state.pedidos)
                registrar_log(st.session_state.usuario_logado['nome'], "Excluir Pedido", f"Pedido {pedido_para_excluir} excluído.")
                st.success(f"Pedido {pedido_para_excluir} excluído com sucesso!")
                st.rerun()

    with aba_ped2:
        st.markdown("### 🔍 Conferência e Checkout de Itens")
        if not st.session_state.pedidos:
            st.info("Nenhum pedido cadastrado para conferência.")
        else:
            ids_pendentes = [p['id'] for p in st.session_state.pedidos if p.get('status') != "Concluído / Expedido"]
            if not ids_pendentes:
                ids_pendentes = [p['id'] for p in st.session_state.pedidos]

            pedido_selecionado_id = st.selectbox("Selecione o Número do Mapa / Pedido para Conferência", ids_pendentes)
            pedido_obj = next((p for p in st.session_state.pedidos if str(p['id']) == str(pedido_selecionado_id)), None)

            if pedido_obj:
                st.markdown(f"""
                <div style='background: #FFF; padding: 12px; border-radius: 8px; border: 1px solid #E9ECEF; margin-bottom: 15px;'>
                    <b>Conferência do Mapa cod. {pedido_obj['id']}</b> | Status: <b style='color: #7A1C2E;'>{pedido_obj.get('status', 'Pendente')}</b><br>
                    Data/Carga: {pedido_obj.get('data', '')}
                </div>
                """, unsafe_allow_html=True)
                
                # Seletor da forma de leitura (Pistola ou Câmera com botão liga/desliga)
                forma_leitura = st.radio("Forma de Leitura:", ["Seleção / Pistola USB", "Câmera do Celular"], horizontal=True)
                
                if forma_leitura == "Câmera do Celular":
                    componente_leitor_barcode("checkout_camera")
                
                # Entrada de código de barras ou nome + quantidade + botão conferir
                col_inp1, col_inp2, col_inp3 = st.columns([3, 1.5, 1])
                with col_inp1:
                    codigo_inputado = st.text_input("Código de Barras ou Nome", value="", key="input_conferencia_manual")
                with col_inp2:
                    qtd_inputada = st.number_input("*Qtd", min_value=1, value=1, key="input_conferencia_qtd")
                with col_inp3:
                    st.write("") # espaçamento visual
                    btn_conferir = st.button("Conferir", use_container_width=True)

                # Processar leitura por câmera se houver
                codigo_bipado = st.session_state.get("codigo_bipado_checkout", "")
                if codigo_bipado:
                    codigo_inputado = codigo_bipado
                    btn_conferir = True
                    st.session_state.codigo_bipado_checkout = ""

                if btn_conferir and codigo_inputado.strip():
                    termo_pesquisa = codigo_inputado.strip().lower()
                    vinho_encontrado = next((v for v in st.session_state.estoque if termo_pesquisa in str(v.get("codigo_barras", "")).lower() or termo_pesquisa in str(v.get("nome", "")).lower()), None)
                    
                    item_pedido = next((item for item in pedido_obj['itens'] if termo_pesquisa in item['nome'].lower() or (vinho_encontrado and vinho_encontrado['nome'].lower() in item['nome'].lower())), None)
                    
                    if item_pedido:
                        item_pedido['qtd_separada'] = item_pedido.get('qtd_separada', 0) + int(qtd_inputada)
                        if item_pedido['qtd_separada'] > item_pedido['quantidade']:
                            item_pedido['divergencia'] = item_pedido['qtd_separada'] - item_pedido['quantidade']
                        salvar_pedidos(st.session_state.pedidos)
                        st.success(f"✅ Item '{item_pedido['nome']}' atualizado com sucesso!")
                        st.rerun()
                    else:
                        st.warning(f"⚠️ O item '{codigo_inputado}' não foi encontrado neste pedido.")

                with st.expander("➕ Inserção Manual Extra (Solicitação de Trajeto / Adicionar Vinho Não Listado)"):
                    st.markdown("Caso precise adicionar um item fora da lista original do mapa.")

                st.markdown("---")
                
                # ESTRUTURA EXATA DO PRINT: Lado esquerdo (Produtos a Conferir) e Lado direito (Produtos Conferidos)
                col_esq, col_dir = st.columns(2)
                
                with col_esq:
                    st.markdown("### PRODUTOS A CONFERIR")
                    pendentes_lista = [i for i in pedido_obj['itens'] if i.get('qtd_separada', 0) < i['quantidade']]
                    if not pendentes_lista:
                        st.markdown("<div style='background: #D4EDDA; color: #155724; padding: 12px; border-radius: 8px; border: 1px solid #C3E6CB;'>✨ Todos os produtos deste mapa foram conferidos!</div>", unsafe_allow_html=True)
                    else:
                        for item in pendentes_lista:
                            falta = item['quantidade'] - item.get('qtd_separada', 0)
                            st.markdown(f"""
                            <div class='wine-card'>
                                <div class='wine-title'>{item['nome']} ({item.get('safra', 'NV')})</div>
                                <div><b>Qtd Pedida:</b> {item['quantidade']} | <b>Falta:</b> {falta}</div>
                            </div>
                            """, unsafe_allow_html=True)

                with col_dir:
                    st.markdown("### PRODUTOS CONFERIDOS")
                    conferidos_lista = [i for i in pedido_obj['itens'] if i.get('qtd_separada', 0) > 0]
                    if not conferidos_lista:
                        st.info("Nenhum produto conferido ainda.")
                    else:
                        for item in conferidos_lista:
                            qtd_sep = item.get('qtd_separada', 0)
                            st.markdown(f"""
                            <div class='wine-card'>
                                <div class='wine-title' style='color: #2E7D32;'>✔ {item['nome']} ({item.get('safra', 'NV')}) - {qtd_sep} unidade(s) conferida(s)</div>
                            </div>
                            """, unsafe_allow_html=True)

                st.markdown("---")
                
                # Dois botões inferiores idênticos ao print
                col_b_inf1, col_b_inf2 = st.columns(2)
                with col_b_inf1:
                    if st.button("💾 Salvar Pedido e Enviar Depois", use_container_width=True):
                        st.success("Pedido salvo com sucesso para continuar depois!")
                with col_b_inf2:
                    if st.button("🚀 Finalizar e Enviar para Matriz", use_container_width=True):
                        pedido_obj['status'] = "Concluído / Expedido"
                        salvar_pedidos(st.session_state.pedidos)
                        registrar_log(st.session_state.usuario_logado['nome'], "Checkout Concluído", f"Pedido {pedido_selecionado_id} finalizado.")
                        st.success("🎉 Checkout concluído e enviado para a Matriz com sucesso!")
                        st.rerun()

elif st.session_state.menu_atual == "Filtros":
    st.subheader("🔍 Buscar e Filtrar Vinhos no Estoque")
    termo = st.text_input("Digite o nome do vinho, safra ou localização", value=st.session_state.termo_busca)
    st.session_state.termo_busca = termo

    estoque = st.session_state.estoque
    if termo.strip():
        termo_l = termo.lower()
        estoque = [v for v in estoque if termo_l in v.get('nome', '').lower() or termo_l in v.get('safra', '').lower() or termo_l in v.get('localizacao', '').lower() or termo_l in v.get('codigo_barras', '').lower()]

    if not estoque:
        st.info("Nenhum vinho encontrado com os critérios informados.")
    else:
        st.markdown(f"Mostrando **{len(estoque)}** vinhos encontrados:")
        for v in estoque:
            st.markdown(f"""
            <div class='wine-card'>
                <div class='wine-title'>{v.get('nome')} ({v.get('safra', 'NV')})</div>
                <div><b>Tipo:</b> {v.get('tipo')} | <b>Caixa:</b> {v.get('caixa')}</div>
                <div><b>Localização:</b> {v.get('localizacao')} - <b>Lado:</b> {v.get('lado')}</div>
                <div><b>Cód. Barras:</b> {v.get('codigo_barras', 'Não cadastrado')}</div>
            </div>
            """, unsafe_allow_html=True)

elif st.session_state.menu_atual == "MapaSeparacao":
    st.subheader("🗺️ Mapa de Separação do Galpão")
    st.markdown("Visualização organizada por Corredores e Localizações para agilizar a separação física.")
    
    corredor_escolhido = st.selectbox("Selecione o Corredor", LISTA_CORREDORES)
    vinhos_corredor = [v for v in st.session_state.estoque if corredor_escolhido.lower() in v.get('localizacao', '').lower()]

    if not vinhos_corredor:
        st.info(f"Nenhum vinho cadastrado no {corredor_escolhido}.")
    else:
        st.markdown(f"### Vinhos no {corredor_escolhido}")
        for v in vinhos_corredor:
            st.markdown(f"""
            <div class='wine-card'>
                <div class='wine-title'>🍷 {v.get('nome')} - Safra {v.get('safra')}</div>
                <div><b>Local:</b> {v.get('localizacao')} ({v.get('lado')})</div>
                <div><b>Embalagem:</b> {v.get('caixa')}</div>
            </div>
            """, unsafe_allow_html=True)

elif st.session_state.menu_atual == "Estoque":
    st.subheader("🍷 Estoque Completo de Vinhos")
    termo_estoque = st.text_input("🔍 Buscar no Estoque por Nome, Safra ou Localização", value="")
    
    estoque = st.session_state.estoque
    if termo_estoque.strip():
        tl = termo_estoque.strip().lower()
        estoque = [v for v in estoque if tl in v.get('nome', '').lower() or tl in v.get('safra', '').lower() or tl in v.get('localizacao', '').lower()]

    if not estoque:
        st.info("O estoque está vazio ou nenhum vinho corresponde à busca.")
    else:
        df_est = pd.DataFrame([{
            "Nome": v.get('nome'),
            "Safra": v.get('safra'),
            "Tipo": v.get('tipo'),
            "Localização": v.get('localizacao'),
            "Lado": v.get('lado'),
            "Caixa": v.get('caixa'),
            "Cód. Barras": v.get('codigo_barras', '')
        } for v in estoque])
        st.dataframe(df_est, use_container_width=True)

elif st.session_state.menu_atual == "Cadastrar":
    st.subheader("➕ Cadastrar Novo Vinho no Estoque")
    
    st.markdown("#### 📷 Ler Código de Barras pela Câmera")
    componente_leitor_barcode("cadastro_camera")
    
    codigo_barras_lido = st.session_state.get("codigo_barras_cadastrado", "")
    if codigo_barras_lido:
        st.success(f"Código de barras capturado: **{codigo_barras_lido}**")

    with st.form("form_cadastrar_vinho"):
        nome_v = st.text_input("Nome do Vinho").strip().title()
        safra_v = st.text_input("Safra (Ex: 2024)").strip()
        tipo_v = st.selectbox("Tipo de Vinho", ["Tinto", "Branco", "Rosé", "Espumante", "Fortificado"])
        corredor_v = st.selectbox("Corredor", LISTA_CORREDORES)
        tipo_local_v = st.selectbox("Tipo de Local", LISTA_LOCAIS_TIPO)
        num_local_v = st.selectbox("Número do Local", LISTA_NUMEROS_LOCAL)
        lado_v = st.selectbox("Lado", LISTA_LADOS)
        caixa_v = st.selectbox("Tipo de Caixa / Embalagem", OPCOES_CAIXA)
        
        barras_v = st.text_input("Código de Barras", value=codigo_barras_lido).strip()
        foto_arquivo = st.file_uploader("Enviar Imagem do Vinho (Opcional)", type=["jpg", "jpeg", "png"])

        if st.form_submit_button("Salvar Novo Vinho"):
            if nome_v:
                caminho_foto = ""
                if foto_arquivo is not None:
                    caminho_foto = os.path.join(PASTA_FOTOS, foto_arquivo.name)
                    with open(caminho_foto, "wb") as f:
                        f.write(foto_arquivo.getbuffer())

                localizacao_completa = f"{corredor_v} - {tipo_local_v} {num_local_v}"
                novo_vinho = {
                    "nome": nome_v,
                    "safra": safra_v,
                    "tipo": tipo_v,
                    "localizacao": localizacao_completa,
                    "lado": lado_v,
                    "caixa": caixa_v,
                    "codigo_barras": barras_v,
                    "foto": caminho_foto
                }
                st.session_state.estoque.append(novo_vinho)
                salvar_dados(st.session_state.estoque)
                registrar_log(st.session_state.usuario_logado['nome'], "Cadastrar Vinho", f"Vinho {nome_v} cadastrado.")
                st.session_state.codigo_barras_cadastrado = ""
                st.success(f"✅ Vinho '{nome_v}' cadastrado com sucesso!")
                st.rerun()
            else:
                st.error("⚠️ O nome do vinho é obrigatório.")

elif st.session_state.menu_atual == "Editar":
    st.subheader("✏️ Editar ou Remover Vinho do Estoque")
    if not st.session_state.estoque:
        st.info("Nenhum vinho cadastrado para editar.")
    else:
        nomes_vinhos = [f"{v['nome']} ({v.get('safra', 'NV')}) - {v.get('localizacao', '')}" for v in st.session_state.estoque]
        escolha_vinho = st.selectbox("Selecione o Vinho", nomes_vinhos)
        indice_vinho = nomes_vinhos.index(escolha_vinho)
        vinho_selecionado = st.session_state.estoque[indice_vinho]

        loc_atual = vinho_selecionado.get('localizacao', 'Corredor 01 - Pallet Item 01')
        partes_loc = loc_atual.split(" - ")
        corr_atual = partes_loc[0] if len(partes_loc) > 0 and partes_loc[0] in LISTA_CORREDORES else "Corredor 01"
        
        tipo_loc_atual = "Pallet"
        num_loc_atual = "Item 01"
        if len(partes_loc) > 1:
            sub_partes = partes_loc[1].split(" ")
            if len(sub_partes) > 0 and sub_partes[0] in LISTA_LOCAIS_TIPO:
                tipo_loc_atual = sub_partes[0]
            if len(sub_partes) >= 2:
                num_loc_atual = f"{sub_partes[1]} {sub_partes[2]}" if len(sub_partes) > 2 else f"{sub_partes[1]}"

        lado_atual = vinho_selecionado.get('lado', 'Centro / Único')
        if lado_atual not in LISTA_LADOS:
            lado_atual = "Centro / Único"

        with st.form("form_editar_vinho"):
            novo_nome = st.text_input("Nome do Vinho", value=vinho_selecionado.get('nome', '')).strip().title()
            nova_safra = st.text_input("Safra", value=vinho_selecionado.get('safra', '')).strip()
            
            idx_corr = LISTA_CORREDORES.index(corr_atual) if corr_atual in LISTA_CORREDORES else 0
            novo_corredor = st.selectbox("Corredor", LISTA_CORREDORES, index=idx_corr)
            
            idx_tipo_loc = LISTA_LOCAIS_TIPO.index(tipo_loc_atual) if tipo_loc_atual in LISTA_LOCAIS_TIPO else 0
            novo_tipo_local = st.selectbox("Tipo de Local", LISTA_LOCAIS_TIPO, index=idx_tipo_loc)
            
            idx_num_loc = LISTA_NUMEROS_LOCAL.index(num_loc_atual) if num_loc_atual in LISTA_NUMEROS_LOCAL else 0
            novo_num_local = st.selectbox("Número do Local", LISTA_NUMEROS_LOCAL, index=idx_num_loc)
            
            idx_lado = LISTA_LADOS.index(lado_atual) if lado_atual in LISTA_LADOS else 0
            novo_lado = st.selectbox("Lado", LISTA_LADOS, index=idx_lado)
            
            novo_barras = st.text_input("Código de Barras", value=vinho_selecionado.get('codigo_barras', '')).strip()
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.form_submit_button("💾 Salvar Alterações"):
                    vinho_selecionado['nome'] = novo_nome
                    vinho_selecionado['safra'] = nova_safra
                    vinho_selecionado['localizacao'] = f"{novo_corredor} - {novo_tipo_local} {novo_num_local}"
                    vinho_selecionado['lado'] = novo_lado
                    vinho_selecionado['codigo_barras'] = novo_barras
                    salvar_dados(st.session_state.estoque)
                    registrar_log(st.session_state.usuario_logado['nome'], "Editar Vinho", f"Vinho {novo_nome} atualizado.")
                    st.success("✅ Alterações salvas com sucesso!")
                    st.rerun()
            with col_b2:
                if st.form_submit_button("🗑️ Excluir este Vinho"):
                    st.session_state.estoque.pop(indice_vinho)
                    salvar_dados(st.session_state.estoque)
                    registrar_log(st.session_state.usuario_logado['nome'], "Excluir Vinho", f"Vinho excluído.")
                    st.success("✅ Vinho excluído com sucesso!")
                    st.rerun()

elif st.session_state.menu_atual == "GerarQRCode":
    st.subheader("📱 Gerar QR Code para Pallets / Corredores")
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        qr_corredor = st.selectbox("Selecione o Corredor", LISTA_CORREDORES, key="qr_corr")
        qr_tipo = st.selectbox("Tipo de Local", LISTA_LOCAIS_TIPO, key="qr_tipo")
    with col_g2:
        qr_numero = st.selectbox("Número do Local", LISTA_NUMEROS_LOCAL, key="qr_num")
        qr_lado = st.selectbox("Lado", LISTA_LADOS, key="qr_lado")

    texto_qr = f"{qr_corredor} - {qr_tipo} {qr_numero} ({qr_lado})"
    
    st.markdown("---")
    url_encoded = urllib.parse.quote(texto_qr)
    url_qrcode = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={url_encoded}"
    st.markdown(f"<div style='text-align: center;'><img src='{url_qrcode}' style='border-radius: 10px; border: 1px solid #E9ECEF;'></div>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; margin-top: 10px;'><b>QR Code gerado para:</b> {texto_qr}</p>", unsafe_allow_html=True)

elif st.session_state.menu_atual == "LerQRCode":
    st.subheader("📷 Ler QR Code / Código de Barras (Corredor)")
    componente_leitor_barcode("consulta_camera")
    
    codigo_lido = st.session_state.get("codigo_bipado_consulta", "")
    if codigo_lido:
        st.success(f"Código lido com sucesso: **{codigo_lido}**")
        vinhos_encontrados = [v for v in st.session_state.estoque if codigo_lido.lower() in v.get('localizacao', '').lower() or codigo_lido.lower() == str(v.get('codigo_barras', '')).lower()]
        if vinhos_encontrados:
            st.markdown(f"### Vinhos encontrados para '{codigo_lido}':")
            for v in vinhos_encontrados:
                st.markdown(f"""
                <div class='wine-card'>
                    <div class='wine-title'>🍷 {v.get('nome')} ({v.get('safra')})</div>
                    <div><b>Local:</b> {v.get('localizacao')} - <b>Lado:</b> {v.get('lado')}</div>
                    <div><b>Caixa:</b> {v.get('caixa')}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Nenhum vinho encontrado associado a este código ou localização.")

elif st.session_state.menu_atual == "Historico":
    st.subheader("📋 Histórico de Logs e Auditoria")
    logs = carregar_logs()
    if not logs:
        st.info("Nenhum registro de auditoria encontrado.")
    else:
        df_logs = pd.DataFrame(logs)
        st.dataframe(df_logs, use_container_width=True)

elif st.session_state.menu_atual == "GerenciarUsuarios":
    st.subheader("⚙️ Gerenciamento de Contas e Usuários")
    if st.session_state.usuario_logado.get('cargo') != "Desenvolvedor":
        st.error("Acesso negado. Apenas desenvolvedores podem gerenciar contas.")
    else:
        usuarios = st.session_state.usuarios
        df_usr = pd.DataFrame(usuarios)
        st.dataframe(df_usr, use_container_width=True)
        
        st.markdown("---")
        with st.form("form_novo_usuario_dev"):
            nome_novo = st.text_input("Nome do Novo Usuário").strip().title()
            senha_nova = st.text_input("Senha", type="password").strip()
            cargo_novo = st.selectbox("Cargo", ["Operador", "Administrador", "Desenvolvedor"])
            if st.form_submit_button("Criar Usuário"):
                if nome_novo and senha_nova:
                    st.session_state.usuarios.append({"nome": nome_novo, "cargo": cargo_novo, "senha": senha_nova})
                    salvar_usuarios(st.session_state.usuarios)
                    st.success(f"Usuário {nome_novo} criado com sucesso!")
                    st.rerun()
                else:
                    st.error("Preencha todos os campos.")
