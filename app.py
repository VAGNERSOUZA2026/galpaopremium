# Usando colunas para centralizar o bloco da imagem e saudação
    _, col_logo, _ = st.columns([2, 1.2, 2])
    with col_logo:
        # Coloque aqui o nome exato do arquivo da sua logo na pasta do projeto
        nome_arquivo_logo = "logo_vinho.png" 
        
        if os.path.exists(nome_arquivo_logo):
            st.image(nome_arquivo_logo, width=180)
        else:
            # Caso o arquivo não seja encontrado com esse nome, tentamos carregar qualquer imagem PNG/JPG na pasta
            arquivos_pasta = [f for f in os.listdir('.') if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if arquivos_pasta:
                st.image(arquivos_pasta[0], width=180)
            else:
                st.warning("⚠️ Arquivo de imagem da logo não encontrado na pasta.")
        
        hora = datetime.now().hour
        saudacao = "Bom dia" if 0 <= hora < 12 else ("Boa tarde" if 12 <= hora < 18 else "Boa noite")
        st.markdown(f"<p style='text-align: center; margin-bottom: 0;'>{saudacao},</p>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align: center; color: #7A1C2E; margin-top: 0;'>{st.session_state.usuario_logado['nome']}! 👋</h2>", unsafe_allow_html=True)
