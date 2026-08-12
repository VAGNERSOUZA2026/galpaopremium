import json
import os
import shutil
from datetime import datetime, timezone, timedelta
import pandas as pd
import streamlit as st
import urllib.parse
from streamlit_qr_code_scanner import qr_code_scanner

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
ARQUIVO_SESSAO_CONFERENCIA = "sessao_conferencia_atual.json"
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

def obter_hora_brasilia():
    return datetime.now(timezone(timedelta(hours=-3)))

def realizar_backup(nome):
    if os.path.exists(nome):
        ts = obter_hora_brasilia().strftime("%Y%m%d_%H%M%S")
        shutil.copy(nome, os.path.join(PASTA_BACKUP, f"backup_{ts}_{nome}"))

def carregar_dados():
    if os.path.exists(NOME_ARQUIVO):
        try:
            with open(NOME_ARQUIVO, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return [{"nome": "Falernia Carmenere", "tipo": "Tinto", "safra": "2022", "localizacao": "Corredor 03 - Pallet Item 03", "lado": "Direito", "caixa": "Caixa com 12 garrafas", "foto": "", "codigo_barras": "7891000000003"}]

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
    logs.insert(0, {"data_hora": obter_hora_brasilia().strftime("%d/%m/%Y %H:%M:%S"), "usuario": usuario, "acao": acao, "detalhes": detalhes})
    with open(ARQUIVO_LOGS, "w", encoding="utf-8") as f: json.dump(logs, f, ensure_ascii=False, indent=4)

def salvar_sessao_conferencia(pedido, itens_conf):
    dados_sessao = {"pedido_ativo": pedido, "conferencia_itens": itens_conf}
    with open(ARQUIVO_SESSAO_CONFERENCIA, "w", encoding="utf-8") as f:
        json.dump(dados_sessao, f, ensure_ascii=False, indent=4)

def carregar_sessao_conferencia():
    if os.path.exists(ARQUIVO_SESSAO_CONFERENCIA):
        try:
            with open(ARQUIVO_SESSAO_CONFERENCIA, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {"pedido_ativo": [], "conferencia_itens": []}

def gerar_qr_code_api(texto):
    return f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={urllib.parse.quote(texto)}"

if "estoque" not in st.session_state: st.session_state.estoque = carregar_dados()
if "usuarios" not in st.session_state: st.session_state.usuarios = carregar_usuarios()
if "menu_atual" not in st.session_state: st.session_state.menu_atual = "🏠 Home"
if "alerta_divergencia_pendente" not in st.session_state: st.session_state.alerta_divergencia_pendente = None

sessao_salva = carregar_sessao_conferencia()
if "pedido_ativo" not in st.session_state: st.session_state.pedido_ativo = sessao_salva.get("pedido_ativo", [])
if "conferencia_itens" not in st.session_state: st.session_state.conferencia_itens = sessao_salva.get("conferencia_itens", [])

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
        if st.button("📷 Ler QR Code", use_container_width=True): st.session_state.menu_atual = "LerQR"; st.rerun()
    
    st.write("")
    c7, c8, c9, c10 = st.columns(4)
    with c7:
        if st.button("📦 Separar Pedido", use_container_width=True): st.session_state.menu_atual = "SepararMatriz"; st.rerun()
    with c8:
        if st.button("✏️ Editar", use_container_width=True): st.session_state.menu_atual = "Editar"; st.rerun()
    with c9:
        if st.button("🗑️ Excluir", use_container_width=True): st.session_state.menu_atual = "Excluir"; st.rerun()
    with c10:
        if st.button("📋 Histórico", use_container_width=True): st.session_state.menu_atual = "Historico"; st.rerun()
        
    if st.session_state.usuario_logado.get('cargo') == "Desenvolvedor":
        st.write("")
        if st.button("⚙️ Gerenciar Contas", use_container_width=True):
            st.session_state.menu_atual = "GerenciarUsuarios"
            st.rerun()

elif st.session_state.menu_atual == "Filtros":
    st.subheader("🔍 Busca por Local ou Nome")
    termo = st.text_input("Filtrar por nome ou corredor/pallet:").strip().title()
    if termo:
        res = [v for v in st.session_state.estoque if termo.lower() in v.get("nome", "").lower() or termo.lower() in v.get("localizacao", "").lower()]
        if res:
            for v in res:
                st.markdown(f"<div class='wine-card'><div class='wine-title'>🍷 {v.get('nome')} ({v.get('safra')})</div><p>Tipo: <b>{v.get('tipo', 'N/A')}</b> | Caixa: <b>{v.get('caixa', 'N/A')}</b><br><span class='badge-pallet-grande'>📍 {v.get('localizacao')} - Lado: {v.get('lado', 'N/A')}</span></p></div>", unsafe_allow_html=True)
        else: st.warning("Nenhum vinho encontrado.")

elif st.session_state.menu_atual == "SepararMatriz":
    st.subheader("📦 Conferência e Separação de Pedido da Matriz")
    st.info("Gerencie a lista de pedidos, faça a leitura e confirme divergências se necessário. Tudo salvo automaticamente.")

    with st.form("form_pedido_matriz"):
        st.write("### 1. Inserir ou Gerenciar Itens do Pedido da Matriz")
        vinho_pedido = st.selectbox("Selecione o Vinho do Estoque:", [v['nome'] for v in st.session_state.estoque])
        safra_pedido = st.text_input("Safra Exigida pela Matriz:").strip()
        qtd_pedido = st.number_input("Quantidade Exigida de Caixas:", min_value=1, value=1)
        
        btn_add = st.form_submit_button("Adicionar ao Pedido")
        if btn_add:
            st.session_state.pedido_ativo.append({"nome": vinho_pedido, "safra": safra_pedido, "qtd": int(qtd_pedido)})
            salvar_sessao_conferencia(st.session_state.pedido_ativo, st.session_state.conferencia_itens)
            st.success(f"Adicionado: {vinho_pedido} ({safra_pedido}) - {qtd_pedido} cx")

    if st.session_state.pedido_ativo:
        st.markdown("---")
        st.write("### 📋 Itens Solicitados pela Matriz:")
        
        for idx_p, item_p in enumerate(list(st.session_state.pedido_ativo)):
            col_p1, col_p2 = st.columns([4, 1])
            with col_p1:
                st.write(f"- **{item_p['nome']}** | Safra: {item_p['safra']} | Qtd: {item_p['qtd']} cx")
            with col_p2:
                if st.button("🗑️ Excluir", key=f"del_pedido_{idx_p}"):
                    st.session_state.pedido_ativo.pop(idx_p)
                    salvar_sessao_conferencia(st.session_state.pedido_ativo, st.session_state.conferencia_itens)
                    st.rerun()

        st.markdown("---")
        st.write("### 🔍 Conferência / Bipagem no Galpão")
        
        if st.session_state.alerta_divergencia_pendente:
            div_info = st.session_state.alerta_divergencia_pendente
            st.warning(f"⚠️ **DIVERGÊNCIA DETECTADA:** {div_info['mensagem']}")
            
            col_div1, col_div2 = st.columns(2)
            with col_div1:
                if st.button("✅ Estou ciente da divergência (Aceitar e Registrar)", use_container_width=True):
                    st.session_state.conferencia_itens.append(div_info['item_para_adicionar'])
                    salvar_sessao_conferencia(st.session_state.pedido_ativo, st.session_state.conferencia_itens)
                    st.session_state.alerta_divergencia_pendente = None
                    st.success("Item com divergência aceito e registrado!")
                    st.rerun()
            with col_div2:
                if st.button("❌ Cancelar / Corrigir", use_container_width=True):
                    st.session_state.alerta_divergencia_pendente = None
                    st.info("Operação cancelada. Nenhuma alteração feita.")
                    st.rerun()
        else:
            with st.form("form_conferencia"):
                codigo_ou_nome = st.text_input("Escaneie o Código de Barras ou Digite o Nome do Vinho:").strip()
                qtd_conferida = st.number_input("Quantidade de Caixas Descidas:", min_value=1, value=1)
                btn_conf = st.form_submit_button("Validar e Conferir Item")
                
                if btn_conf:
                    vinho_encontrado = next((v for v in st.session_state.estoque if v.get('codigo_barras') == codigo_ou_nome or v.get('nome').lower() == codigo_ou_nome.lower()), None)
                    
                    if not vinho_encontrado:
                        st.error("❌ ERRO: Vinho não cadastrado ou código de barras não reconhecido no sistema!")
                    else:
                        item_pedido = next((p for p in st.session_state.pedido_ativo if p['nome'].lower() == vinho_encontrado['nome'].lower()), None)
                        
                        if not item_pedido:
                            st.error(f"❌ ATENÇÃO: O vinho '{vinho_encontrado['nome']}' NÃO FOI PEDIDO pela matriz!")
                        else:
                            tem_erro_safra = item_pedido['safra'] != vinho_encontrado['safra']
                            tem_erro_qtd = int(qtd_conferida) != int(item_pedido['qtd'])
                            
                            if tem_erro_safra or tem_erro_qtd:
                                msgs = []
                                if tem_erro_safra:
                                    msgs.append(f"Safra informada ({vinho_encontrado['safra']}) difere da solicitada ({item_pedido['safra']}).")
                                if tem_erro_qtd:
                                    msgs.append(f"Quantidade informada ({qtd_conferida} cx) difere da solicitada ({item_pedido['qtd']} cx).")
                                
                                msg_completa = " ".join(msgs)
                                st.session_state.alerta_divergencia_pendente = {
                                    "mensagem": msg_completa,
                                    "item_para_adicionar": {
                                        "nome": vinho_encontrado['nome'],
                                        "safra": vinho_encontrado['safra'],
                                        "qtd_descida": int(qtd_conferida)
                                    }
                                }
                                st.rerun()
                            else:
                                st.success(f"✅ CORRETO! {vinho_encontrado['nome']} (Safra {vinho_encontrado['safra']}) validado com sucesso!")
                                st.session_state.conferencia_itens.append({
                                    "nome": vinho_encontrado['nome'],
                                    "safra": vinho_encontrado['safra'],
                                    "qtd_descida": int(qtd_conferida)
                                })
                                salvar_sessao_conferencia(st.session_state.pedido_ativo, st.session_state.conferencia_itens)
                                st.rerun()

        if st.session_state.conferencia_itens:
            st.write("### Itens já conferidos e separados:")
            
            for idx_c, item_c in enumerate(list(st.session_state.conferencia_itens)):
                col_c1, col_c2 = st.columns([4, 1])
                with col_c1:
                    st.write(f"- Vinho: **{item_c['nome']}** | Safra: {item_c['safra']} | Qtd Descida: {item_c['qtd_descida']} cx")
                with col_c2:
                    if st.button("🗑️ Excluir", key=f"del_conf_{idx_c}"):
                        st.session_state.conferencia_itens.pop(idx_c)
                        salvar_sessao_conferencia(st.session_state.pedido_ativo, st.session_state.conferencia_itens)
                        st.rerun()

            c_acao1, c_acao2 = st.columns(2)
            with c_acao1:
                if st.button("Gerar Romaneio Final e Salvar (.txt)"):
                    hora_br_str = obter_hora_brasilia().strftime('%d/%m/%Y %H:%M')
                    # Romaneio sem a localização conforme solicitado
                    texto_romaneio = f"=== ROMANEIO DE ENVIO - PREMIUM WINES ===\nData/Hora: {hora_br_str}\n\n"
                    for item in st.session_state.conferencia_itens:
                        texto_romaneio += f"- Vinho: {item['nome']} | Safra: {item['safra']} | Qtd Descida: {item['qtd_descida']} cx\n"
                    texto_romaneio += "\nStatus: Conferido e validado com sucesso."

                    st.success("Romaneio gerado com sucesso!")
                    st.download_button(
                        label="📥 Baixar Arquivo do Romaneio (.txt)",
                        data=texto_romaneio,
                        file_name=f"romaneio_matriz_{obter_hora_brasilia().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain",
                        use_container_width=True
        
