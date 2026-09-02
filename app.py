import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import pytz
import re

# ==========================================
# CONFIGURAÇÃO DE ESTILO E TEMA (GALPÃO PREMIUM)
# ==========================================
st.set_page_config(
    page_title="Galpão Premium - Sistema de Estoque e Expedição",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main {
        background-color: #F8F9FA;
    }
    .stButton>button {
        background-color: #7A1C2E;
        color: white;
        border-radius: 6px;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #5C1320;
        color: white;
    }
    .wine-card {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 10px;
        border-left: 4px solid #7A1C2E;
    }
    .wine-title {
        font-size: 18px;
        font-weight: bold;
        color: #2C3E50;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# ARQUIVOS DE PERSISTÊNCIA DE DADOS
# ==========================================
ARQUIVO_DADOS = "estoque_vinhos.json"
ARQUIVO_PEDIDOS = "pedidos_matriz.json"
ARQUIVO_LOGS = "historico_logs.json"
ARQUIVO_USUARIOS = "usuarios_sistema.json"

def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        try:
            with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

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
    logs.insert(0, {
        "data_hora": datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%d/%m/%Y %H:%M:%S"),
        "usuario": usuario,
        "acao": acao,
        "detalhes": detalhes
    })
    with open(ARQUIVO_LOGS, "w", encoding="utf-8") as f:
        json.dump(logs[:200], f, ensure_ascii=False, indent=4)

def carregar_usuarios():
    if os.path.exists(ARQUIVO_USUARIOS):
        try:
            with open(ARQUIVO_USUARIOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return [
        {"nome": "Dev", "senha": "123", "cargo": "Desenvolvedor"},
        {"nome": "Conferente 1", "senha": "123", "cargo": "Conferente"}
    ]

def salvar_usuarios(usuarios):
    with open(ARQUIVO_USUARIOS, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, ensure_ascii=False, indent=4)

def obter_horario_brasilia():
    return datetime.now(pytz.timezone('America/Sao_Paulo'))

# ==========================================
# LISTAS PADRÃO DE LOCALIZAÇÃO
# ==========================================
LISTA_CORREDORES = [f"Corredor {i:02d}" for i in range(1, 21)]
LISTA_LOCAIS_TIPO = ["Pallet", "Prateleira"]
LISTA_NUMEROS_LOCAL = [f"Item {i:02d}" for i in range(1, 101)]
LISTA_LADOS = ["Esquerdo", "Direito"]
OPCOES_CAIXA = [
    "Caixa com 12 garrafas",
    "Caixa com 6 garrafas",
    "Caixa com 3 garrafas",
    "Caixa com 1 garrafa (Unitário)",
    "Magnum / Especial"
]

# ==========================================
# INICIALIZAÇÃO DO SESSION STATE
# ==========================================
if 'estoque' not in st.session_state:
    st.session_state.estoque = carregar_dados()

if 'pedidos' not in st.session_state:
    st.session_state.pedidos = carregar_pedidos()

if 'usuarios' not in st.session_state:
    st.session_state.usuarios = carregar_usuarios()

if 'usuario_logado' not in st.session_state:
    st.session_state.usuario_logado = None

if 'menu_atual' not in st.session_state:
    st.session_state.menu_atual = "Estoque"

if 'termo_busca' not in st.session_state:
    st.session_state.termo_busca = ""

# ==========================================
# FUNÇÕES DE AUXÍLIO PARA PEDIDOS E ARQUIVOS
# ==========================================
def interpretar_linha_pedido(linha):
    linha_limpa = linha.strip()
    match_qtd = re.search(r'[\/\-\s]+(\d+)\s*(?:caixa|cx|unidade|un|garrafa|gf)?s?$', linha_limpa, re.IGNORECASE)
    quantidade = 1
    nome_vinho = linha_limpa
    if match_qtd:
        quantidade = int(match_qtd.group(1))
        nome_vinho = linha_limpa[:match_qtd.start()].strip(" /-")
    
    match_safra = re.search(r'\b(19\d{2}|20\d{2})\b', nome_vinho)
    safra = match_safra.group(1) if match_safra else "N/A"
    
    return {
        "nome": nome_vinho,
        "safra": safra,
        "quantidade": quantidade,
        "separado": False,
        "qtd_separada": 0,
        "divergencia": 0,
        "autorizado_divergencia": False
    }

def extrair_pedidos_de_arquivo(uploaded_file):
    itens = []
    try:
        nome_arquivo = uploaded_file.name.lower()
        if nome_arquivo.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
            for _, row in df.iterrows():
                nome = str(row.iloc[0]).strip()
                qtd = int(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else 1
                if nome and nome.lower() != 'nan':
                    match_safra = re.search(r'\b(19\d{2}|20\d{2})\b', nome)
                    safra = match_safra.group(1) if match_safra else "N/A"
                    itens.append({
                        "nome": nome,
                        "safra": safra,
                        "quantidade": qtd,
                        "separado": False,
                        "qtd_separada": 0,
                        "divergencia": 0,
                        "autorizado_divergencia": False
                    })
        elif nome_arquivo.endswith('.txt'):
            string_data = uploaded_file.getvalue().decode("utf-8")
            for linha in string_data.split("\n"):
                if linha.strip():
                    itens.append(interpretar_linha_pedido(linha))
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")
    return itens

def sincronizar_estoque_com_pedidos(pedidos, estoque):
    nomes_estoque = {v['nome'].lower() for v in estoque}
    for p in pedidos:
        for item in p['itens']:
            if item['nome'].lower() not in nomes_estoque:
                match_safra = re.search(r'\b(19\d{2}|20\d{2})\b', item['nome'])
                safra = match_safra.group(1) if match_safra else "N/A"
                novo_v = {
                    "nome": item['nome'],
                    "safra": safra,
                    "tipo": "Tinto",
                    "localizacao": "Corredor 01 - Pallet Item 01",
                    "lado": "Direito",
                    "caixa": "Caixa com 12 garrafas",
                    "codigo_barras": "",
                    "foto": ""
                }
                estoque.append(novo_v)
                nomes_estoque.add(item['nome'].lower())
    salvar_dados(estoque)

def componente_leitor_barcode(key_name):
    html_code = f"""
    <div style="background: #f1f3f4; padding: 10px; border-radius: 8px; text-align: center;">
        <p style="margin:0; font-size: 14px; color: #333;">Simulador de Câmera / Leitor de Código de Barras</p>
        <input type="text" id="barcode_{key_name}" placeholder="Clique aqui e bipe com o coletor ou digite..." style="width: 100%; padding: 8px; margin-top: 5px; border-radius: 4px; border: 1px solid #ccc;" autofocus>
    </div>
    <script>
        const input = document.getElementById("barcode_{key_name}");
        input.addEventListener("change", function() {{
            const val = input.value;
            window.parent.postMessage({{"type": "streamlit:setComponentValue", "value": val}}, "*");
        }});
    </script>
    """
    st.components.v1.html(html_code, height=90)

# ==========================================
# TELA DE LOGIN
# ==========================================
if st.session_state.usuario_logado is None:
    st.markdown("<h2 style='text-align: center; color: #7A1C2E;'>🍷 Galpão Premium - Login</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("form_login"):
            nome_usuario = st.text_input("Usuário")
            senha_usuario = st.text_input("Senha", type="password")
            btn_entrar = st.form_submit_button("Entrar no Sistema", use_container_width=True)
            
            if btn_entrar:
                usuario_encontrado = next((u for u in st.session_state.usuarios if u['nome'].lower() == nome_usuario.lower() and u['senha'] == senha_usuario), None)
                if usuario_encontrado:
                    st.session_state.usuario_logado = usuario_encontrado
                    registrar_log(usuario_encontrado['nome'], "Login", "Entrou no sistema")
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
    st.stop()

# ==========================================
# BARRA LATERAL (MENU DE NAVEGAÇÃO)
# ==========================================
st.sidebar.markdown(f"👤 **Logado como:** {st.session_state.usuario_logado['nome']} ({st.session_state.usuario_logado.get('cargo', 'Operador')})")

if st.sidebar.button("🚪 Sair do Sistema"):
    registrar_log(st.session_state.usuario_logado['nome'], "Logout", "Saiu do sistema")
    st.session_state.usuario_logado = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🧭 Menu Principal")

menu_opcoes = {
    "📦 Pedidos & Checkout": "PedidosMatriz",
    "🍷 Estoque Geral": "Estoque",
    "➕ Cadastrar Vinho": "Cadastrar",
    "✏️ Editar / Excluir Vinho": "Editar",
    "🔍 Filtros & Busca": "Filtros",
    "🗺️ Mapa de Separação": "MapaSeparacao",
    "📋 Histórico de Auditoria": "Historico"
}

if st.session_state.usuario_logado.get('cargo') == 'Desenvolvedor':
    menu_opcoes["⚙️ Gerenciar Usuários"] = "GerenciarUsuarios"

for label, key in menu_opcoes.items():
    if st.sidebar.button(label, use_container_width=True):
        st.session_state.menu_atual = key
        st.rerun()

# ==========================================
# ROTEAMENTO DE TELAS
# ==========================================

if st.session_state.menu_atual == "PedidosMatriz":
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
                
                itens_pendentes_lista = [i['nome'] for i in pedido_ativo['itens'] if not i.get('separado', False) or i.get('divergencia', 0) != 0]
                
                col_b1, col_b2, col_b3 = st.columns([2, 1, 1])
                with col_b1:
                    if modo_leitura == "📷 Câmera do Celular":
                        cod_barras_input = st.text_input("*Código de Barras ou Nome", value=codigo_capturado, key="input_bipagem_checkout")
                    else:
                        if itens_pendentes_lista:
                            opcao_selecionada_dropdown = st.selectbox("*Selecione o Vinho da Lista ou Digite/Bipe", ["-- Selecione ou Digite --"] + itens_pendentes_lista)
                            if opcao_selecionada_dropdown != "-- Selecione ou Digite --":
                                cod_barras_input = opcao_selecionada_dropdown
                            else:
                                cod_barras_input = st.text_input("*Ou digite/bipe o Código de Barras", value="", key="input_bipagem_checkout")
                        else:
                            cod_barras_input = st.text_input("*Código de Barras ou Nome", value="", key="input_bipagem_checkout")
                with col_b2:
                    qtd_input = st.number_input("*Qtd", min_value=1, value=1, key="input_qtd_checkout")
                with col_b3:
                    st.write("")
                    btn_conferir = st.button("Conferir", use_container_width=True)
                
                # CORREÇÃO APLICADA: Tratamento exato da divergência (ex: 9 conferidos para 10 pedidos resulta em -1 e bloqueia)
                if btn_conferir and cod_barras_input and cod_barras_input != "-- Selecione ou Digite --":
                    encontrou = False
                    for item in pedido_ativo['itens']:
                        vinho_no_estoque = next((v for v in st.session_state.estoque if v['nome'].lower() in item['nome'].lower() or v.get('codigo_barras') == cod_barras_input), None)
                        
                        match_nome = cod_barras_input.lower() in item['nome'].lower()
                        match_bc = vinho_no_estoque and vinho_no_estoque.get('codigo_barras') == cod_barras_input
                        
                        if match_nome or match_bc:
                            encontrou = True
                            item['qtd_separada'] = int(qtd_input)
                            item['divergencia'] = int(qtd_input) - int(item['quantidade'])
                            
                            if item['divergencia'] == 0:
                                item['autorizado_divergencia'] = True
                                item['separado'] = True
                            else:
                                item['autorizado_divergencia'] = False
                                item['separado'] = False 
                                dif_tipo = "mais" if item['divergencia'] > 0 else "menos"
                                st.warning(f"⚠️ Atenção! Quantidade separada ({item['qtd_separada']}) diverge para {dif_tipo} da pedida ({item['quantidade']}) para o item '{item['nome']}'. O item foi bloqueado até a digitação da senha.")
                            break
                    
                    if encontrou:
                        if "codigo_bipado_checkout" in st.session_state:
                            st.session_state.codigo_bipado_checkout = ""
                        salvar_pedidos(st.session_state.pedidos)
                        st.rerun()
                    else:
                        st.error("Produto não encontrado neste mapa.")

                itens_com_divergencia_nao_autorizados = [i for i in pedido_ativo['itens'] if i.get('divergencia', 0) != 0 and not i.get('autorizado_divergencia', False)]
                
                if itens_com_divergencia_nao_autorizados:
                    st.markdown("---")
                    st.error("🔒 Existem itens com quantidade incorreta / divergente aguardando correção ou liberação de senha (Senha: 2026):")
                    for it_div in itens_com_divergencia_nao_autorizados:
                        with st.form(f"form_senha_item_{it_div['nome']}"):
                            st.markdown(f"**Item:** {it_div['nome']} | Pedido: {it_div['quantidade']} | Separado: {it_div['qtd_separada']} (Divergência: {it_div['divergencia']:+d})")
                            st.info("Dica: Se foi erro de digitação, você pode corrigir clicando abaixo para ajustar a quantidade exata:")
                            
                            corrigir_para_pedida = st.form_submit_button("🔄 Corrigir e Ajustar para Qtd Pedida Automaticamente")
                            if corrigir_para_pedida:
                                it_div['qtd_separada'] = it_div['quantidade']
                                it_div['divergencia'] = 0
                                it_div['autorizado_divergencia'] = True
                                it_div['separado'] = True
                                salvar_pedidos(st.session_state.pedidos)
                                st.success(f"Quantidade de '{it_div['nome']}' corrigida com sucesso para o valor do pedido!")
                                st.rerun()

                            senha_item = st.text_input("Ou digite a senha de liberação de divergência (2026):", type="password", key=f"pass_{it_div['nome']}")
                            if st.form_submit_button("Autorizar Com Divergência"):
                                if senha_item == "2026":
                                    it_div['autorizado_divergencia'] = True
                                    it_div['separado'] = True
                                    salvar_pedidos(st.session_state.pedidos)
                                    registrar_log(st.session_state.usuario_logado['nome'], "Liberou Divergência Item", it_div['nome'])
                                    st.success(f"Divergência autorizada para '{it_div['nome']}'!")
                                    st.rerun()
                                else:
                                    st.error("Senha incorreta. Digite 2026.")

                with st.expander("➕ Inserção Manual Extra (Solicitação de Trajeto / Adicionar Vinho Não Listado)"):
                    with st.form("form_vinho_extra"):
                        nome_extra = st.text_input("Nome do Vinho Extra").strip().title()
                        qtd_extra = st.number_input("Quantidade", min_value=1, value=1)
                        senha_extra = st.text_input("Senha de Liberação (2026)", type="password")
                        if st.form_submit_button("Adicionar ao Pedido com Senha"):
                            if nome_extra:
                                if senha_extra == "2026":
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
                    pendentes = [i for i in pedido_ativo['itens'] if not i.get('separado', False) or i.get('divergencia', 0) != 0 and not i.get('autorizado_divergencia', False)]
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
                    st.markdown("<h4 style='color: #2E7D32;'>PRODUTOS CONFERIDOS</h4>", unsafe_allow_html=True)
                    conferidos = [i for i in pedido_ativo['itens'] if i.get('separado', False) and (i.get('divergencia', 0) == 0 or i.get('autorizado_divergencia', False))]
                    if not conferidos:
                        st.info("Nenhum produto conferido ainda.")
                    for item in conferidos:
                        dif_val = item.get('divergencia', 0)
                        dif_texto = f" ({dif_val:+d})" if dif_val != 0 else " (0)"
                        st.markdown(f"""
                        <div style='background: #F1F8E9; padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid #2E7D32;'>
                            ✅ <b>{item['nome']}</b> ({item.get('safra', 'N/A')}) - {item.get('qtd_separada', 0)} unidade(s) conferida(s) <b style='color: #C62828;'>{dif_texto}</b>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.write("")
                col_salvar1, col_salvar2 = st.columns(2)
                with col_salvar1:
                    if st.button("💾 Salvar Pedido e Enviar Depois", use_container_width=True):
                        salvar_pedidos(st.session_state.pedidos)
                        registrar_log(st.session_state.usuario_logado['nome'], "Salvou Pedido Parcial", pedido_ativo['id'])
                        st.success(f"Progresso do pedido {pedido_ativo['id']} salvo com sucesso!")
                with col_salvar2:
                    if st.button("🚀 Finalizar e Enviar para Matriz", use_container_width=True):
                        divergencias_pendentes = [i for i in pedido_ativo['itens'] if i.get('divergencia', 0) != 0 and not i.get('autorizado_divergencia', False)]
                        
                        if divergencias_pendentes:
                            st.error("⚠️ Não é possível finalizar! Existem itens com quantidade divergente que ainda precisam da senha de liberação (2026) ou correção.")
                        else:
                            tem_divergencia_geral = any(i.get('divergencia', 0) != 0 for i in pedido_ativo['itens'])
                            if tem_divergencia_geral:
                                pedido_ativo['status'] = "Concluído / Expedido (Com Divergência)"
                            else:
                                pedido_ativo['status'] = "Concluído / Expedido"
                                
                            salvar_pedidos(st.session_state.pedidos)
                            registrar_log(st.session_state.usuario_logado['nome'], "Finalizou e Enviou Pedido", pedido_ativo['id'])
                            st.success(f"Pedido {pedido_ativo['id']} finalizado e enviado para a Matriz com sucesso!")
                            st.rerun()

elif st.session_state.menu_atual == "Estoque":
    st.subheader("🍷 Estoque Completo do Galpão (Ordem Alfabética)")
    estoque_ordenado = sorted(st.session_state.estoque, key=lambda x: x.get("nome", "").lower())
    for vinho in estoque_ordenado:
        st.markdown(f"""
        <div class="wine-card">
            <div class="wine-title">{vinho['nome']} ({vinho.get('safra', 'N/A')})</div>
            <div>Tipo: {vinho.get('tipo', 'N/A')} | Local: {vinho.get('localizacao', 'N/A')} - Lado: {vinho.get('lado', 'N/A')} | Caixa: {vinho.get('caixa', 'N/A')}</div>
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.menu_atual == "Cadastrar":
    st.subheader("➕ Cadastrar Novo Vinho")
    
    with st.form("form_cad", clear_on_submit=True):
        nome_c = st.text_input("Nome do Vinho").strip().title()
        safra_c = st.text_input("Safra").strip()
        tipo_c = st.selectbox("Tipo", ["Tinto", "Branco", "Rosé", "Espumante", "Fortificado"])
        corredor_c = st.selectbox("Corredor", LISTA_CORREDORES)
        tipo_local_c = st.selectbox("Tipo de Local", LISTA_LOCAIS_TIPO)
        num_local_c = st.selectbox("Número do Local", LISTA_NUMEROS_LOCAL)
        lado_c = st.selectbox("Lado", LISTA_LADOS)
        caixa_c = st.selectbox("Embalagem", OPCOES_CAIXA)
        bc_c = st.text_input("Código de Barras").strip()
        
        btn_salvando = st.form_submit_button("Salvar Vinho")
        
        if btn_salvando:
            if nome_c:
                local_completo = f"{corredor_c} - {tipo_local_c} {num_local_c}"
                vinho_existente = next((v for v in st.session_state.estoque if v['nome'].lower() == nome_c.lower()), None)
                
                if vinho_existente:
                    st.warning(f"⚠️ Atenção: O vinho '{nome_c}' já consta no sistema! Como houve alteração, o cadastro foi aceito.")
                
                novo_vinho = {
                    "nome": nome_c,
                    "safra": safra_c,
                    "tipo": tipo_c,
                    "localizacao": local_completo,
                    "lado": lado_c,
                    "caixa": caixa_c,
                    "codigo_barras": bc_c,
                    "foto": ""
                }
                st.session_state.estoque.append(novo_vinho)
                salvar_dados(st.session_state.estoque)
                registrar_log(st.session_state.usuario_logado['nome'], "Cadastrou Vinho", nome_c)
                st.success("Vinho cadastrado com sucesso!")
            else:
                st.error("Informe o nome do vinho.")

elif st.session_state.menu_atual == "Editar":
    st.subheader("✏️ Editar ou Excluir Vinho do Estoque")
    if not st.session_state.estoque:
        st.warning("Nenhum vinho cadastrado para editar.")
    else:
        nomes_vinhos = [f"{v['nome']} ({v.get('safra', 'N/A')})" for v in sorted(st.session_state.estoque, key=lambda x: x.get('nome', '').lower())]
        vinho_selecionado_str = st.selectbox("Selecione o Vinho para Editar:", nomes_vinhos)
        
        vinho_obj = next((v for v in st.session_state.estoque if f"{v['nome']} ({v.get('safra', 'N/A')})" == vinho_selecionado_str), None)
        
        if vinho_obj:
            with st.form("form_edicao_vinho"):
                n_edit = st.text_input("Nome do Vinho", value=vinho_obj.get('nome', '')).strip().title()
                s_edit = st.text_input("Safra", value=vinho_obj.get('safra', '')).strip()
                t_edit = st.selectbox("Tipo", ["Tinto", "Branco", "Rosé", "Espumante", "Fortificado"])
                
                loc_atual = vinho_obj.get('localizacao', 'Corredor 01 - Pallet Item 01')
                corr_atual = loc_atual.split(" - ")[0] if " - " in loc_atual else "Corredor 01"
                
                corredor_edit = st.selectbox("Corredor", LISTA_CORREDORES, index=LISTA_CORREDORES.index(corr_atual) if corr_atual in LISTA_CORREDORES else 0)
                tipo_local_edit = st.selectbox("Tipo de Local", LISTA_LOCAIS_TIPO)
                num_local_edit = st.selectbox("Número do Local", LISTA_NUMEROS_LOCAL)
                lado_edit = st.selectbox("Lado", LISTA_LADOS)
                caixa_edit = st.selectbox("Embalagem", OPCOES_CAIXA)
                bc_edit = st.text_input("Código de Barras", value=vinho_obj.get('codigo_barras', '')).strip()
                
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    btn_salvar_ed = st.form_submit_button("💾 Salvar Alterações", use_container_width=True)
                with col_e2:
                    btn_excluir_vinho = st.form_submit_button("🗑️ Excluir este Vinho", use_container_width=True)
                
                if btn_salvar_ed:
                    vinho_obj['nome'] = n_edit
                    vinho_obj['safra'] = s_edit
                    vinho_obj['tipo'] = t_edit
                    vinho_obj['localizacao'] = f"{corredor_edit} - {tipo_local_edit} {num_local_edit}"
                    vinho_obj['lado'] = lado_edit
                    vinho_obj['caixa'] = caixa_edit
                    vinho_obj['codigo_barras'] = bc_edit
                    salvar_dados(st.session_state.estoque)
                    registrar_log(st.session_state.usuario_logado['nome'], "Editou Vinho", n_edit)
                    st.success("Alterações salvas com sucesso!")
                    st.rerun()
                
                if btn_excluir_vinho:
                    st.session_state.estoque = [v for v in st.session_state.estoque if v != vinho_obj]
                    salvar_dados(st.session_state.estoque)
                    registrar_log(st.session_state.usuario_logado['nome'], "Excluiu Vinho", vinho_obj['nome'])
                    st.success("Vinho excluído com sucesso!")
                    st.rerun()

elif st.session_state.menu_atual == "Filtros":
    st.subheader("🔍 Buscar e Filtrar Vinhos")
    termo = st.text_input("Digite o nome ou código de barras:", value=st.session_state.termo_busca)
    filtrados = [v for v in sorted(st.session_state.estoque, key=lambda x: x.get('nome', '').lower()) if termo.lower() in v['nome'].lower() or termo in v.get('codigo_barras', '')]
    for v in filtrados:
        st.markdown(f"""
        <div class="wine-card">
            <div class="wine-title">{v['nome']} ({v.get('safra', 'N/A')})</div>
            <div>Local: {v.get('localizacao', 'N/A')} - Lado: {v.get('lado', 'N/A')} | Caixa: {v.get('caixa', 'N/A')} | Cód: {v.get('codigo_barras', 'N/A')}</div>
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.menu_atual == "MapaSeparacao":
    st.subheader("🗺️ Mapa de Separação por Corredor")
    corredor_sel = st.selectbox("Selecione o Corredor", LISTA_CORREDORES)
    vinhos_corr = [v for v in sorted(st.session_state.estoque, key=lambda x: x.get('nome', '').lower()) if corredor_sel.lower() in v.get('localizacao', '').lower()]
    st.write(f"Total de itens no {corredor_sel}: {len(vinhos_corr)}")
    for v in vinhos_corr:
        st.markdown(f"""
        <div class="wine-card">
            <div class="wine-title">{v['nome']} ({v.get('safra', 'N/A')})</div>
            <div>Posição: {v.get('localizacao', 'N/A')} - Lado {v.get('lado', 'N/A')}</div>
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.menu_atual == "Historico":
    st.subheader("📋 Histórico de Auditoria")
    logs = carregar_logs()
    if not logs:
        st.info("Nenhum registro no histórico.")
    for l in logs[:50]:
        st.markdown(f"- **{l['data_hora']}** | *{l['usuario']}* - {l['acao']}: {l['detalhes']}")

elif st.session_state.menu_atual == "GerenciarUsuarios":
    st.subheader("⚙️ Gerenciar Contas de Usuários")
    for u in st.session_state.usuarios:
        st.markdown(f"- **{u['nome']}** ({u.get('cargo', 'Operador')})")
