import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os
import json
import base64

# Configuração da Página
st.set_page_config(
    page_title="Separação de Vinho Galpão",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Constantes e Listas
SENHA_DIVERGENCIA = "2026"
LISTA_CORREDORES = [f"Corredor {i:02d}" for i in range(1, 21)]
LISTA_LOCAIS_TIPO = ["Pallet", "Estante", "Pilha"]
LISTA_NUMEROS_LOCAL = [f"{i:02d}" for i in range(1, 51)]
LISTA_LADOS = ["Lado Direito", "Lado Esquerdo", "Centro / Único"]
OPCOES_CAIXA = [
    "Caixa com 12 garrafas", 
    "Caixa com 6 garrafas", 
    "Caixa com 3 garrafas", 
    "Unidade (Garrafa Avulsa)"
]

ARQUIVO_ESTOQUE = "estoque_vinhos.json"
ARQUIVO_PEDIDOS = "pedidos_vinhos.json"
ARQUIVO_LOGS = "logs_vinhos.json"

# Estilos CSS Customizados
st.markdown("""
<style>
    .main { background-color: #F8F9FA; }
    .wine-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #E9ECEF;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .wine-title {
        font-weight: bold;
        color: #7A1C2E;
        font-size: 1.1rem;
        margin-bottom: 5px;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Funções Utilitárias e de Horário
def obter_horario_brasilia():
    fuso = pytz.timezone("America/Sao_Paulo")
    return datetime.now(fuso)

def obter_saudacao():
    hora = obter_horario_brasilia().hour
    if 5 <= hora < 12:
        return "Bom dia"
    elif 12 <= hora < 18:
        return "Boa tarde"
    else:
        return "Boa noite"

# Gerenciamento de Dados (JSON)
def carregar_dados():
    if os.path.exists(ARQUIVO_ESTOQUE):
        try:
            with open(ARQUIVO_ESTOQUE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def salvar_dados(estoque):
    with open(ARQUIVO_ESTOQUE, "w", encoding="utf-8") as f:
        json.dump(estoque, f, ensure_ascii=False, indent=4)

def carregar_pedidos():
    if os.path.exists(ARQUIVO_PEDIDOS):
        try:
            with open(ARQUIVO_PEDIDOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def salvar_pedidos(pedidos):
    with open(ARQUIVO_PEDIDOS, "w", encoding="utf-8") as f:
        json.dump(pedidos, f, ensure_ascii=False, indent=4)

def carregar_logs():
    if os.path.exists(ARQUIVO_LOGS):
        try:
            with open(ARQUIVO_LOGS, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def registrar_log(usuario, acao, detalhes):
    logs = carregar_logs()
    novo_log = {
        "data_hora": obter_horario_brasilia().strftime("%d/%m/%Y %H:%M:%S"),
        "usuario": usuario,
        "acao": acao,
        "detalhes": detalhes
    }
    logs.insert(0, novo_log)
    with open(ARQUIVO_LOGS, "w", encoding="utf-8") as f:
        json.dump(logs[:200], f, ensure_ascii=False, indent=4)

def sincronizar_estoque_com_pedidos(pedidos, estoque):
    pass

def interpretar_linha_pedido(linha):
    partes = linha.split("/")
    nome = partes[0].strip() if len(partes) > 0 else "Vinho Desconhecido"
    safra = partes[1].strip() if len(partes) > 1 else "N/A"
    try:
        qtd = int(partes[2].strip()) if len(partes) > 2 else 1
    except:
        qtd = 1
    return {
        "nome": nome,
        "safra": safra,
        "quantidade": qtd,
        "separado": False,
        "qtd_separada": 0,
        "divergencia": 0,
        "autorizado_divergencia": False
    }

def extrair_pedidos_de_arquivo(arquivo):
    itens = []
    try:
        if arquivo.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(arquivo)
            for _, row in df.iterrows():
                itens.append({
                    "nome": str(row.iloc[0]).strip(),
                    "safra": str(row.iloc[1]).strip() if len(row) > 1 else "N/A",
                    "quantidade": int(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else 1,
                    "separado": False, "qtd_separada": 0, "divergencia": 0, "autorizado_divergencia": False
                })
        elif arquivo.name.endswith('.txt'):
            linhas = arquivo.getvalue().decode("utf-8").splitlines()
            for linha in linhas:
                if linha.strip():
                    itens.append(interpretar_linha_pedido(linha))
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")
    return itens

# Componente de Leitor de Código de Barras customizado (com ativação manual de câmera)
def componente_leitor_barcode(chave_estado):
    col_ativar, _ = st.columns([1, 2])
    with col_ativar:
        ativar_cam = st.toggle("📷 Ligar Câmera do Leitor", key=f"toggle_cam_{chave_estado}")
    
    if ativar_cam:
        st.info("Aponte a câmera para o código de barras.")
        # Simulação ou componente visual para captura de câmera HTML5 se integrado
    
    codigo_digitado = st.text_input("Ou digite / bipar código de barras manualmente:", key=f"input_manual_{chave_estado}")
    if codigo_digitado:
        st.session_state[f"codigo_bipado_{chave_estado}"] = codigo_digitado

# Inicialização de Session State
if "estoque" not in st.session_state:
    st.session_state.estoque = carregar_dados()
if "pedidos" not in st.session_state:
    st.session_state.pedidos = carregar_pedidos()
if "usuarios" not in st.session_state:
    st.session_state.usuarios = [{"nome": "Administrador", "cargo": "Desenvolvedor"}]
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = {"nome": "Operador Galpão", "cargo": "Operador"}
if "menu_atual" not in st.session_state:
    st.session_state.menu_atual = "🏠 Home"
if "termo_busca" not in st.session_state:
    st.session_state.termo_busca = ""

# Barra Superior / Navegação
st.markdown(f"""
<div style='display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #7A1C2E; padding-bottom: 10px; margin-bottom: 20px;'>
    <h3 style='color: #7A1C2E; margin: 0;'>🍷 Separação de Vinho Galpão</h3>
    <span style='color: #444; font-weight: 500;'>👤 {st.session_state.usuario_logado['nome']} ({st.session_state.usuario_logado['cargo']})</span>
</div>
""", unsafe_allow_html=True)

if st.session_state.menu_atual != "🏠 Home":
    if st.button("⬅️ Voltar ao Menu Principal"):
        st.session_state.menu_atual = "🏠 Home"
        st.rerun()

st.markdown("---")

# MENU PRINCIPAL
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
    termo_mapa = st.text_input("🔍 Digite o nome do vinho para buscar no mapa:", value="")
    estoque_mapa = st.session_state.estoque
    if termo_mapa.strip():
        estoque_mapa = [v for v in estoque_mapa if termo_mapa.lower() in v['nome'].lower() or termo_mapa.lower() in v.get('localizacao', '').lower()]
    
    if not estoque_mapa:
        st.info("Nenhum vinho encontrado.")
    else:
        for vinho in sorted(estoque_mapa, key=lambda x: (x.get('localizacao', ''), x.get('nome', ''))):
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
    busca = st.text_input("Pesquisar por nome ou código de barras:", value="")
    vinhos_filtrados = st.session_state.estoque
    if busca.strip():
        vinhos_filtrados = [v for v in vinhos_filtrados if busca.lower() in v['nome'].lower() or busca in v.get('codigo_barras', '')]
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
        foto_c = st.file_uploader("🖼️ Inserir Imagem do Vinho / Rótulo", type=["jpg", "jpeg", "png"])
        
        btn_salvar_novo = st.form_submit_button("Salvar Vinho")
        if btn_salvar_novo:
            if nome_c:
                localizacao_completa = f"{corredor_c} - {tipo_local_c} {numero_local_c}"
                novo_id = f"vinho_{len(st.session_state.estoque)}_{int(obter_horario_brasilia().timestamp())}"
                novo_vinho = {
                    "id": novo_id, "nome": nome_c, "tipo": tipo_c, "safra": safra_c,
                    "localizacao": localizacao_completa, "lado": lado_c, "caixa": caixa_c,
                    "codigo_barras": codigo_barras_c, "foto": foto_c.name if foto_c else ""
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
        st.info("Nenhum vinho cadastrado.")
    else:
        opcoes_vinhos = {f"{v['nome']} ({v.get('safra', 'S/ Safra')}) - Local: {v.get('localizacao', 'N/A')}": v['id'] for v in st.session_state.estoque}
        id_vinho_selecionado = opcoes_vinhos[st.selectbox("Selecione o Vinho:", list(opcoes_vinhos.keys()))]
        vinho_obj = next((v for v in st.session_state.estoque if v['id'] == id_vinho_selecionado), None)
        
        if vinho_obj:
            with st.form("form_editar_vinho_completo"):
                novo_nome = st.text_input("Nome do Vinho", value=vinho_obj.get('nome', '')).strip().title()
                novo_codigo_barras = st.text_input("Código de Barras", value=vinho_obj.get('codigo_barras', '')).strip()
                btn_atualizar = st.form_submit_button("💾 Salvar Alterações")
                if btn_atualizar:
                    vinho_obj['nome'] = novo_nome
                    vinho_obj['codigo_barras'] = novo_codigo_barras
                    salvar_dados(st.session_state.estoque)
                    st.success("Atualizado com sucesso!")
                    st.rerun()

elif st.session_state.menu_atual == "Historico":
    st.subheader("📋 Histórico de Auditoria e Logs")
    for l in carregar_logs():
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
    st.markdown("Selecione corredor, pallet e lado para gerar a etiqueta correta:")
    
    col_g1, col_g2, col_g3 = st.columns(3)
    with col_g1:
        corredor_gerar = st.selectbox("Corredor:", LISTA_CORREDORES)
    with col_g2:
        pallet_gerar = st.selectbox("Pallet:", LISTA_NUMEROS_LOCAL)
    with col_g3:
        lado_gerar = st.selectbox("Lado:", LISTA_LADOS)
        
    if st.button("Gerar Etiqueta QR"):
        st.success(f"Etiqueta gerada para: **{corredor_gerar} - Pallet {pallet_gerar} - {lado_gerar}**")

elif st.session_state.menu_atual == "PainelMatriz":
    st.subheader("🏢 Painel da Matriz - Acompanhamento de Pedidos")
    st.markdown("Utilize a busca abaixo para carregar os detalhes do pedido ou data:")
    
    termo_busca_matriz = st.text_input("🔍 Buscar por Número do Pedido ou Data (DD/MM/AAAA):", value="")
    
    if termo_busca_matriz.strip():
        pedidos_filtrados = [p for p in st.session_state.pedidos if termo_busca_matriz in p['id'] or termo_busca_matriz in p['data']]
        if not pedidos_filtrados:
            st.warning("Nenhum pedido encontrado com este critério.")
        else:
            for p in pedidos_filtrados:
                tem_div = any(item.get('divergencia', 0) != 0 for item in p['itens'])
                status_txt = "⚠️ Contém Divergência" if tem_div else p.get('status', 'Pendente')
                st.markdown(f"""
                <div class='wine-card'>
                    <b>Pedido Nº {p['id']}</b> | Data: {p['data']} | Status: <b style='color: {'#7A1C2E' if tem_div else '#2E7D32'};'>{status_txt}</b>
                </div>
                """, unsafe_allow_html=True)
                df_itens = [{"Produto": i['nome'], "Qtd Pedida": i['quantidade'], "Qtd Separada": i.get('qtd_separada', 0), "Divergência": i.get('divergencia', 0)} for i in p['itens']]
                st.dataframe(pd.DataFrame(df_itens), use_container_width=True)

elif st.session_state.menu_atual == "PedidosMatriz":
    st.subheader("📦 Gestão de Pedidos & Checkout de Expedição")
    aba_ped1, aba_ped2 = st.tabs(["📋 Cadastrar / Enviar Pedidos", "🔍 Conferência (Checkout Estilo WMS)"])
    
    with aba_ped1:
        proximo_numero = len(st.session_state.pedidos) + 1
        id_pedido = st.text_input("Código de Barras do Pedido / Mapa", value=f"123{proximo_numero:03d}")
        
        if "itens_novo_pedido_temp" not in st.session_state:
            st.session_state.itens_novo_pedido_temp = []
            
        texto_manual_pedido = st.text_area("Digite os itens (Nome / Safra / Qtd por linha):", value="")
        if st.button("➕ Adicionar à Lista"):
            for linha in texto_manual_pedido.split("\n"):
                if linha.strip():
                    st.session_state.itens_novo_pedido_temp.append(interpretar_linha_pedido(linha))
            st.success("Itens adicionados!")
            st.rerun()
            
        if st.session_state.itens_novo_pedido_temp:
            for it in st.session_state.itens_novo_pedido_temp:
                st.write(f"- **{it['nome']}** | Qtd: {it['quantidade']}")
            if st.button("💾 Salvar Pedido Definitivo", use_container_width=True):
                novo_p = {"id": id_pedido, "data": obter_horario_brasilia().strftime("%d/%m/%Y %H:%M"), "itens": list(st.session_state.itens_novo_pedido_temp), "status": "Pendente"}
                st.session_state.pedidos.append(novo_p)
                salvar_pedidos(st.session_state.pedidos)
                st.session_state.itens_novo_pedido_temp = []
                st.success("Salvo com sucesso!")
                st.rerun()

    with aba_ped2:
        st.markdown("Conferência WMS: Digitação manual / código como primeira opção, seguida de leitura por câmera.")
        ids_ativos = [p['id'] for p in st.session_state.pedidos if p.get('status') != "Concluído / Expedido"]
        
        if not ids_ativos:
            st.info("Nenhum pedido pendente para conferência.")
        else:
            pedido_conf_id = st.selectbox("Selecione o Pedido:", ids_ativos)
            pedido_obj = next((p for p in st.session_state.pedidos if p['id'] == pedido_conf_id), None)
            
            if pedido_obj:
                # Opções de Entrada em ordem solicitada
                modo_conferencia = st.radio("Método de Entrada:", ["⌨️ Digitação Manual / Código de Barras", "📷 Leitor por Câmera"], horizontal=True)
                
                if "⌨️" in modo_conferencia:
                    cod_digitavel = st.text_input("Digite o código de barras ou SKU do produto:")
                    if cod_digitavel:
                        st.info(f"Código inserido: {cod_digitavel}")
                else:
                    componente_leitor_barcode("checkout_wms")
                
                st.markdown("---")
                # Layout WMS: Esquerdo (Lista Original) vs Direito (Conferidos)
                col_wms_esq, col_wms_dir = st.columns(2)
                
                with col_wms_esq:
                    st.markdown("#### 📋 Vinhos da Lista (Pedido)")
                    for idx, item in enumerate(pedido_obj['itens']):
                        st.markdown(f"- **{item['nome']}** (Safra: {item.get('safra', 'N/A')})<br>Qtd Pedida: <b>{item['quantidade']}</b>", unsafe_allow_html=True)
                        st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)
                        
                with col_wms_dir:
                    st.markdown("#### 📦 Conferidos (WMS)")
                    # Seleção flutuante de vinhos da lista para evitar digitação manual do nome
                    nomes_disponiveis = [i['nome'] for i in pedido_obj['itens']]
                    vinho_selecionado_flutuante = st.selectbox("Selecionar Vinho Flutuante:", nomes_disponiveis, key=f"flu_{pedido_conf_id}")
                    
                    item_atual_conf = next((i for i in pedido_obj['itens'] if i['nome'] == vinho_selecionado_flutuante), None)
                    if item_atual_conf:
                        idx_item = pedido_obj['itens'].index(item_atual_conf)
                        qtd_sep = st.number_input("Quantidade Conferida:", min_value=0, value=item_atual_conf.get('qtd_separada', item_atual_conf['quantidade']), key=f"qtd_wms_{pedido_conf_id}_{idx_item}")
                        item_atual_conf['qtd_separada'] = qtd_sep
                        item_atual_conf['divergencia'] = qtd_sep - item_atual_conf['quantidade']
                        
                        if item_atual_conf['divergencia'] != 0 and not item_atual_conf.get('autorizado_divergencia', False):
                            st.warning(f"⚠️ Divergência detectada ({item_atual_conf['divergencia']})!")
                            senha_div = st.text_input("Senha da Gerência para Divergência:", type="password", key=f"pwd_wms_{idx_item}")
                            if st.button("Liberar Divergência", key=f"btn_lib_{idx_item}"):
                                if senha_div == SENHA_DIVERGENCIA:
                                    item_atual_conf['autorizado_divergencia'] = True
                                    st.success("Liberado com sucesso!")
                                    st.rerun()
                                else:
                                    st.error("Senha incorreta.")
                        else:
                            st.markdown("✅ Status: Conferido Correto / Liberado")

                if st.button("🚀 Finalizar e Expedir Pedido (Checkout WMS)", use_container_width=True):
                    bloqueio = any(it['divergencia'] != 0 and not it.get('autorizado_divergencia', False) for it in pedido_obj['itens'])
                    if bloqueio:
                        st.error("Existem itens com divergência não autorizados pela senha gerencial (2026).")
                    else:
                        pedido_obj['status'] = "Concluído / Expedido"
                        salvar_pedidos(st.session_state.pedidos)
                        registrar_log(st.session_state.usuario_logado['nome'], "Expediu Pedido WMS", str(pedido_conf_id))
                        st.success("Pedido expedido e atualizado no Painel da Matriz com sucesso!")
                        st.rerun()
