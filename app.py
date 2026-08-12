import json
import os
import shutil
from datetime import datetime, timezone, timedelta
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import urllib.parse
from docx import Document

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

if not os.path.exists(PASTA_BACKUP): os.makedirs(PASTA_BACKUP)
if not os.path.exists(PASTA_FOTOS): os.makedirs(PASTA_FOTOS)

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
    return [{"nome": "Château Margaux", "tipo": "Tinto", "safra": "2015", "localizacao": "Corredor 01 - Pallet Item 01", "lado": "Direito", "caixa": "Caixa com 12 garrafas", "codigo_barras": "7891020304051", "foto": ""}]

def salvar_dados(estoque):
    with open(NOME_ARQUIVO, "w", encoding="utf-8") as f: json.dump(estoque, f, ensure_ascii=False, indent=4)
    realizar_backup(NOME_ARQUIVO)

def carregar_usuarios():
    if os.path.exists(ARQUIVO_USUARIOS):
        try:
            with open(ARQUIVO_USUARIOS, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return [{"nome": "Vagner Souza", "cargo": "Desenvolvedor", "senha": "1980"}]

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
        elif ext == 'txt':
            linhas = [l.strip().title() for l in arq.getvalue().decode("utf-8").split("\n") if l.strip()]
    except: pass
    return linhas

# Componente de Câmera com Leitor Estilo Banco (QuaggaJS)
def componente_leitor_banco(chave_id="scanner_padrao"):
    html_scanner = f"""
    <div style="width: 100%; text-align: center;">
        <div id="interactive-{chave_id}" class="viewport" style="position: relative; width: 100%; max-width: 400px; margin: 0 auto; height: 250px; background: #000; border-radius: 12px; overflow: hidden;">
            <video style="width: 100%; height: 100%; object-fit: cover;" autoplay muted playsinline></video>
            <canvas style="display: none;"></canvas>
            <div style="position: absolute; top: 50%; left: 10%; right: 10%; height: 2px; background: red; box-shadow: 0 0 8px red; animation: pulse 1.5s infinite;"></div>
        </div>
        <p id="status-{chave_id}" style="color: #666; font-size: 13px; margin-top: 8px;">Aponte para o código de barras...</p>
        <input type="text" id="resultado-{chave_id}" style="opacity: 0; position: absolute;" />
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/quagga/0.12.1/quagga.min.js"></script>
    <script>
        const targetDiv = document.querySelector('#interactive-{chave_id}');
        Quagga.init({{
            inputStream: {{
                type: "LiveStream",
                target: targetDiv,
                constraints: {{ facingMode: "environment" }}
            },
            decoder: {{ readers: ["ean_reader", "code_128_reader", "upc_reader"] }}
        }}, function(err) {{
            if (err) {{
                document.getElementById('status-{chave_id}').innerText = "Erro ao abrir câmera.";
                return;
            }}
            Quagga.start();
        }});
        
        Quagga.onDetected(function(result) {{
            const code = result.codeResult.code;
            document.getElementById('status-{chave_id}').innerText = "Lido com sucesso: " + code;
            // Envia para o Streamlit via postMessage/URL params ou manipulação de input
            const inputEl = window.parent.document.querySelector('input[aria-label="Código de Barras Capturado"]');
            if(inputEl) {{
                inputEl.value = code;
                inputEl.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
        }});
    </script>
    """
    components.html(html_scanner, height=320)

if "estoque" not in st.session_state: st.session_state.estoque = carregar_dados()
if "usuarios" not in st.session_state: st.session_state.usuarios = carregar_usuarios()
if "menu_atual" not in st.session_state: st.session_state.menu_atual = "🏠 Home"

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
with ct1: st.markdown(f"🍷 <b>PREMIUM WINES</b> | Usuário: {st.session_state.usuario_logado['nome']} ({st.session_state.usuario_logado.get('cargo','Operador')})", unsafe_allow_html=True)
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
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("📦 Separar Pedido Matriz (Bipagem 🧪)", use_container_width=True):
                st.session_state.menu_atual = "SepararMatriz"
                st.rerun()
        with cc2:
            if st.button("⚙️ Gerenciar Contas", use_container_width=True):
                st.session_state.menu_atual = "GerenciarUsuarios"
                st.rerun()

elif st.session_state.menu_atual == "Filtros":
    st.subheader("🔍 Busca por Local ou Nome")
    termo = st.text_input("Filtrar por nome ou corredor/pallet:").strip().title()
    if termo:
        res = [v for v in st.session_state.estoque if termo.lower() in v.get("nome", "").lower() or termo.lower() in v.get("localizacao", "").lower() or termo.lower() in str(v.get("codigo_barras", "")).lower()]
        if res:
            for v in res:
                cb_txt = f" | Cód. Barras: <code>{v.get('codigo_barras')}</code>" if v.get('codigo_barras') else ""
                st.markdown(f"<div class='wine-card'><div class='wine-title'>🍷 {v.get('nome')} ({v.get('safra')})</div><p>Tipo: <b>{v.get('tipo', 'N/A')}</b> | Caixa: <b>{v.get('caixa', 'N/A')}</b>{cb_txt}<br><span class='badge-pallet-grande'>📍 {v.get('localizacao')} - Lado: {v.get('lado', 'N/A')}</span></p></div>", unsafe_allow_html=True)
        else: st.warning("Nenhum vinho encontrado.")

elif st.session_state.menu_atual == "SepararMatriz":
    st.subheader("📦 Conferência e Separação por Código de Barras (Matriz) 🧪")
    tab_s1, tab_s2 = st.tabs(["1. Importar Pedido da Matriz", "2. Bipar com Câmera Contínua 📱"])
    
    with tab_s1:
        arq_matriz = st.file_uploader("Envie o pedido da Matriz (.xlsx ou .txt)", type=["xlsx", "xls", "txt"])
        pedido_manual = st.text_area("Ou cole a lista de vinhos pedidos:")
        if st.button("Carregar Pedido"):
            itens_pedido = []
            if arq_matriz:
                ext = arq_matriz.name.split('.')[-1].lower()
                if ext in ['xlsx', 'xls']:
                    dfm = pd.read_excel(arq_matriz)
                    for _, row in dfm.iterrows():
                        np_ = str(row.get('Nome', row.iloc[0])).strip().title()
                        qp_ = int(row.get('Quantidade', 1)) if 'Quantidade' in dfm.columns else 1
                        if np_ and np_ != 'Nan': itens_pedido.append({"nome": np_, "qtd_esperada": qp_})
                elif ext == 'txt':
                    for lt in arq_matriz.getvalue().decode("utf-8").split("\n"):
                        if lt.strip(): itens_pedido.append({"nome": lt.strip().title(), "qtd_esperada": 1})
            if pedido_manual.strip():
                for lm in pedido_manual.split("\n"):
                    if lm.strip(): itens_pedido.append({"nome": lm.strip().title(), "qtd_esperada": 1})
            if itens_pedido:
                st.session_state.pedido_matriz_ativo = itens_pedido
                st.session_state.bipados_galpao = {}
                st.success(f"Pedido carregado! {len(itens_pedido)} itens.")
            else: st.error("Nenhum item encontrado.")
            
        if "pedido_matriz_ativo" in st.session_state and st.session_state.pedido_matriz_ativo:
            st.dataframe(pd.DataFrame(st.session_state.pedido_matriz_ativo), use_container_width=True)

    with tab_s2:
        if "pedido_matriz_ativo" not in st.session_state or not st.session_state.pedido_matriz_ativo:
            st.warning("⚠️ Carregue o pedido na aba anterior primeiro!")
        else:
            st.markdown("Use o leitor abaixo para escanear as caixas corredor por corredor:")
            componente_leitor_banco("scanner_matriz")
            
            # Campo invisível/visível para recepção do JS
            codigo_lido = st.text_input("Código de Barras Capturado", key="cod_capturado_input").strip()
            qtd_lida = st.number_input("Quantidade de caixas desta leitura:", min_value=1, value=1)
            
            if st.button("Confirmar Leitura"):
                if codigo_lido:
                    vinho_enc = next((v for v in st.session_state.estoque if str(v.get('codigo_barras', '')).strip().lower() == codigo_lido.lower()), None)
                    if vinho_enc:
                        nome_v = vinho_enc['nome']
                        item_ped = next((ip for ip in st.session_state.pedido_matriz_ativo if ip['nome'].lower() in nome_v.lower() or nome_v.lower() in ip['nome'].lower()), None)
                        if item_ped:
                            atual = st.session_state.bipados_galpao.get(item_ped['nome'], 0)
                            st.session_state.bipados_galpao[item_ped['nome']] = atual + qtd_lida
                            st.success(f"✅ Bipado: **{nome_v}** (+{qtd_lida} cx). Local: **{vinho_enc.get('localizacao')}**")
                        else:
                            st.error(f"❌ ATENÇÃO: O vinho **{nome_v}** NÃO consta no pedido da matriz!")
                    else:
                        st.error(f"❌ Código '{codigo_lido}' não cadastrado no galpão!")
                else: st.warning("Nenhum código capturado ainda.")
                
            st.markdown("---")
            st.markdown("### 📊 Status em Tempo Real")
            if "bipados_galpao" in st.session_state:
                conf = []
                tudo_ok = True
                for item in st.session_state.pedido_matriz_ativo:
                    esp = item['qtd_esperada']
                    sep = st.session_state.bipados_galpao.get(item['nome'], 0)
                    st_txt = "✅ Concluído"
                    if sep < esp: st_txt = f"⏳ Faltam {esp - sep}"; tudo_ok = False
                    elif sep > esp: st_txt = f"⚠️ Excedente (+{sep - esp})"; tudo_ok = False
                    conf.append({"Vinho": item['nome'], "Qtd Esperada": esp, "Qtd Separada": sep, "Status": st_txt})
                st.dataframe(pd.DataFrame(conf), use_container_width=True)
                
                if tudo_ok and len(st.session_state.pedido_matriz_ativo) > 0:
                    st.success("🎉 Pedido 100% conferido!")
                    
                    # Conteúdo do Romaneio para Download
                    texto_romaneio = f"=== ROMANEIO DE ENVIO - PREMIUM WINES ===\nData: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
                    for item in st.session_state.pedido_matriz_ativo:
                        texto_romaneio += f"- {item['nome']}: {item['qtd_esperada']} caixas\n"
                    texto_romaneio += "\nStatus: Validado e Conferido via Leitor de Código de Barras."
                    
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        st.download_button(
                            label="📥 Baixar Arquivo do Romaneio (.txt)",
                            data=texto_romaneio,
                            file_name=f"romaneio_matriz_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                    with col_b2:
                        if st.button("💾 Baixar & Dar Baixa no Estoque", use_container_width=True):
                            # Realiza a baixa real no estoque do galpão
                            for item in st.session_state.pedido_matriz_ativo:
                                nome_alvo = item['nome']
                                qtd_retirada = item['qtd_esperada']
                                for v in st.session_state.estoque:
                                    if v['nome'].lower() == nome_alvo.lower():
                                        # Remove do estoque ou ajusta
                                        st.session_state.estoque.remove(v)
                                        break
                            salvar_dados(st.session_state.estoque)
                            registrar_log(st.session_state.usuario_logado['nome'], "Baixa Pedido Matriz", "Romaneio concluído e estoque atualizado.")
                            st.success("Estoque do galpão atualizado com sucesso!")

elif st.session_state.menu_atual == "MapaSeparacao":
    st.subheader("🗺️ Mapa de Separação")
    arq = st.file_uploader("Envie lista de vinhos (.xlsx ou .txt)", type=["xlsx", "xls", "txt"])
    txt_man = st.text_area("Ou cole a lista manual:").title()
    if st.button("Gerar Rota"):
        linhas = extrair_linhas_de_arquivo(arq) if arq else []
        if txt_man.strip(): linhas.extend([l.strip().title() for l in txt_man.split("\n") if l.strip()])
        if linhas:
            enc = [v for v in st.session_state.estoque if any(l.lower() in v.get("nome","").lower() for l in linhas)]
            for v in enc:
                st.markdown(f"<div class='wine-card'><div class='wine-title'>🍷 {v.get('nome')}</div><p><span class='badge-pallet-grande'>📍 {v.get('localizacao')}</span></p></div>", unsafe_allow_html=True)

elif st.session_state.menu_atual == "Scanner":
    st.subheader("📷 Escanear Local")
    componente_leitor_banco("scanner_local")
    loc_input = st.text_input("Código de Barras Capturado", key="cod_loc_input")
    if loc_input:
        st.success(f"Localizado: {loc_input}")

elif st.session_state.menu_atual == "Estoque":
    st.subheader("🍷 Estoque Completo")
    for v in st.session_state.estoque:
        cb = f" | Cód: `{v.get('codigo_barras')}`" if v.get('codigo_barras') else ""
        st.markdown(f"<div class='wine-card'><div class='wine-title'>🍷 {v.get('nome')} ({v.get('safra')})</div><p>📍 <b>{v.get('localizacao')}</b>{cb}</p></div>", unsafe_allow_html=True)

elif st.session_state.menu_atual == "Cadastrar":
    st.subheader("➕ Cadastrar Vinho")
    tipo_cad = st.radio("Método de Código de Barras:", ["Digitação Manual", "Escanear com Câmera"])
    
    cb_val = ""
    if tipo_cad == "Escanear com Câmera":
        componente_leitor_banco("scanner_cadastro")
        cb_val = st.text_input("Código de Barras Capturado", key="cad_codigo_capturado").strip()
    
    with st.form("cad_form"):
        nome = st.text_input("Nome").strip().title()
        tipo = st.selectbox("Tipo", ["Tinto", "Branco", "Rosé", "Espumante"])
        safra = st.text_input("Safra").strip()
        if tipo_cad == "Digitação Manual":
            cb_val = st.text_input("Código de Barras (Digitável)").strip()
        else:
            st.info(f"Código de Barras escaneado atual: **{cb_val}**")
            
        corredor = st.selectbox("Corredor", LISTA_CORREDORES)
        tipo_loc = st.selectbox("Tipo Local", LISTA_LOCAIS_TIPO)
        numero = st.selectbox("Número", LISTA_NUMEROS_LOCAL)
        lado = st.selectbox("Lado", LISTA_LADOS)
        caixa = st.selectbox("Caixa", OPCOES_CAIXA)
        
        if st.form_submit_button("Salvar Vinho"):
            if nome:
                st.session_state.estoque.append({
                    "nome": nome, "tipo": tipo, "safra": safra,
                    "localizacao": f"{corredor} - {tipo_loc} {numero}",
                    "lado": lado, "caixa": caixa, "codigo_barras": cb_val, "foto": ""
                })
                salvar_dados(st.session_state.estoque)
                registrar_log(st.session_state.usuario_logado['nome'], "Cadastrar Vinho", nome)
                st.success("Cadastrado com sucesso!")
                st.session_state.menu_atual = "🏠 Home"
                st.rerun()
            else: st.error("Informe o nome.")

elif st.session_state.menu_atual == "GerarQR":
    st.subheader("📱 Gerar QR Code")
    c_cor = st.selectbox("Corredor", LISTA_CORREDORES)
    c_tip = st.selectbox("Tipo", LISTA_LOCAIS_TIPO)
    c_num = st.selectbox("Número", LISTA_NUMEROS_LOCAL)
    txt_qr = f"{c_cor} - {c_tip} {c_num}"
    if st.button("Gerar"):
        url = gerar_qr_code_api(txt_qr)
        st.image(url, width=220)
        st.markdown(f"<a href='{url}' target='_blank' download>📥 Baixar Imagem</a>", unsafe_allow_html=True)

elif st.session_state.menu_atual == "Historico":
    st.subheader("📋 Histórico")
    for l in carregar_logs():
        st.markdown(f"- **{l['data_hora']}** | {l['usuario']} | {l['acao']}")

elif st.session_state.menu_atual == "GerenciarUsuarios":
    st.subheader("⚙️ Contas")
    for u in st.session_state.usuarios:
        st.write(f"👤 **{u['nome']}** ({u.get('cargo')})")

elif st.session_state.menu_atual == "Editar":
    st.subheader("✏️ Editar Vinho")
    nomes = [v['nome'] for v in st.session_state.estoque]
    if nomes:
        sel = st.selectbox("Selecione:", nomes)
        idx = nomes.index(sel)
        v = st.session_state.estoque[idx]
        with st.form("ed"):
            nn = st.text_input("Nome", value=v['nome']).strip().title()
            ncb = st.text_input("Código de Barras", value=v.get('codigo_barras','')).strip()
            if st.form_submit_button("Atualizar"):
                st.session_state.estoque[idx]['nome'] = nn
                st.session_state.estoque[idx]['codigo_barras'] = ncb
                salvar_dados(st.session_state.estoque)
                st.success("Atualizado!")
                st.session_state.menu_atual = "🏠 Home"
                st.rerun()

elif st.session_state.menu_atual == "Excluir":
    st.subheader("🗑️ Excluir")
    nomes = [v['nome'] for v in st.session_state.estoque]
    if nomes:
        sel = st.selectbox("Excluir:", nomes)
        if st.button("Confirmar Exclusão"):
            idx = nomes.index(sel)
            st.session_state.estoque.pop(idx)
            salvar_dados(st.session_state.estoque)
            st.success("Excluído!")
            st.session_state.menu_atual = "🏠 Home"
            st.rerun()
