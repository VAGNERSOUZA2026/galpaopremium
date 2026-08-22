import streamlit as st

# Configuração da página para ocupar a largura correta e evitar espaços em branco
st.set_page_config(
    page_title="Separação de Vinho Galpão", page_icon="🍷", layout="wide"
)

# Inicialização do controle de sessão
if "logado" not in st.session_state:
  st.session_state["logado"] = False
if "usuario_atual" not in st.session_state:
  st.session_state["usuario_atual"] = ""
if "modo_dev" not in st.session_state:
  st.session_state["modo_dev"] = False

# Base simulada de usuários (você pode substituir por banco de dados ou st.secrets)
# Formato: "usuario": {"senha": "...", "tipo": "dev" ou "comum"}
if "usuarios_cadastrados" not in st.session_state:
  st.session_state["usuarios_cadastrados"] = {
      "admin": {
          "senha": "28121980",
          "tipo": "dev",
      },  # Senha mestre ajustada para 28121980
      "funcionario1": {"senha": "123", "tipo": "comum"},
  }

# ---------------------------------------------------------
# TELA DE LOGIN
# ---------------------------------------------------------
if not st.session_state["logado"]:
  # Layout centralizado para evitar visual feio e rolagem excessiva
  col1, col2, col3 = st.columns([1, 1.5, 1])

  with col2:
    st.markdown("<br>", unsafe_allow_html=True)  # Pequeno respiro superior

    # Seção visual inicial
    st.markdown(
        "<h2 style='text-align: center; color: #5a189a;'>SEPARAÇÃO DE VINHO"
        " GALPÃO</h2>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    with st.form("form_login"):
      usuario_input = st.text_input("Usuário")
      senha_input = st.text_input("Senha", type="password")
      submit_login = st.form_submit_button("ENTRAR", use_container_width=True)

      if submit_login:
        usuarios = st.session_state["usuarios_cadastrados"]

        # Verifica se o usuário existe na base
        if (
            usuario_input in usuarios
            and usuarios[usuario_input]["senha"] == senha_input
        ):
          st.session_state["logado"] = True
          st.session_state["usuario_atual"] = usuario_input

          # REGRA RIGOROSA DE DEV: Só é dev se o usuário for 'admin' E usar a senha mestre
          if (
              usuario_input == "admin" and senha_input == "28121980"
          ):  #
            st.session_state["modo_dev"] = True
          else:
            st.session_state["modo_dev"] = False

          st.success("Login realizado com sucesso!")
          st.rerun()
        else:
          st.error("Usuário ou senha incorretos.")

# ---------------------------------------------------------
# TELA PRINCIPAL / SISTEMA APÓS O LOGIN
# ---------------------------------------------------------
else:
  # Barra lateral (Sidebar) para navegação e logout
  st.sidebar.title(f"Olá, {st.session_state['usuario_atual']}")
  st.sidebar.markdown(
      f"Perfil: **{'Desenvolvedor' if st.session_state['modo_dev'] else 'Comum'}**"
  )

  menu = ["Área de Trabalho", "Sobre"]

  # Se for desenvolvedor, adiciona a opção de cadastrar usuários no menu
  if st.session_state["modo_dev"]:
    menu.append("Cadastrar Novo Usuário")

  escolha = st.sidebar.selectbox("Navegação", menu)

  if st.sidebar.button("Sair / Logout", use_container_width=True):
    st.session_state["logado"] = False
    st.session_state["usuario_atual"] = ""
    st.session_state["modo_dev"] = False
    st.rerun()

  # ---------------------------------------------------------
  # CONTEÚDO DAS PÁGINAS
  # ---------------------------------------------------------
  if escolha == "Área de Trabalho":
    st.title("📦 Sistema de Separação de Estoque")
    st.write(
        "Bem-vindo ao painel operacional. Aqui você gerencia os pedidos e"
        " separações."
    )
    # Coloque aqui as suas tabelas de estoque e lógica de separação

  elif escolha == "Cadastrar Novo Usuário" and st.session_state["modo_dev"]:
    st.title("🛠️ Painel do Desenvolvedor - Cadastro de Usuários")
    st.write(
        "Adicione novos usuários ao sistema definindo permissões corretas."
    )

    with st.form("form_cadastro"):
      novo_usuario = st.text_input("Nome do Novo Usuário")
      nova_senha = st.text_input("Senha do Novo Usuário", type="password")
      tipo_usuario = st.selectbox(
          "Tipo de Perfil", ["comum", "dev"]
      )  # Cuidado ao criar outro dev

      submit_cadastro = st.form_submit_button("Salvar Cadastro")

      if submit_cadastro:
        if novo_usuario and nova_senha:
          if (
              novo_usuario
              in st.session_state["usuarios_cadastrados_comum_ou_dev"]
          ):  # Correção chave
            st.warning("Este usuário já existe!")
          else:
            st.session_state["usuarios_cadastrados"][novo_usuario] = {
                "senha": nova_senha,
                "tipo": tipo_usuario,
            }
            st.success(
                f"Usuário '{novo_usuario}' cadastrado com sucesso como"
                f" '{tipo_usuario}'!"
            )
        else:
          st.error("Preencha todos os campos para cadastrar.")

  elif escolha == "Sobre":
    st.title("ℹ️ Sobre o Aplicativo")
    st.write("Sistema desenvolvido para controle de estoque e separação de vinhos.")
