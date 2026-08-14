with aba_scan2:
        foto = st.camera_input("Tirar foto de um QR Code impresso")
        if foto and OPENCV_DISPONIVEL:
            img = cv2.imdecode(np.frombuffer(foto.getvalue(), np.uint8), cv2.IMREAD_COLOR)
            detector = cv2.QRCodeDetector()
            val, _, _ = detector.detectAndDecode(img)
            if val:
                st.success(f"QR Code Lido: **{val}**")
                st.session_state.termo_busca = val
                st.session_state.menu_atual = "Filtros"
                st.rerun()
            else:
                st.warning("Nenhum QR Code detectado na imagem. Tente novamente.")
        elif foto and not OPENCV_DISPONIVEL:
            st.error("A biblioteca OpenCV não está disponível neste ambiente para decodificar a foto.")

elif st.session_state.menu_atual == "Estoque":
    st.subheader("🍷 Estoque Completo do Galpão")
    if st.session_state.estoque:
        for v in st.session_state.estoque:
            st.markdown(
                f"<div class='wine-card'>"
                f"<div class='wine-title'>🍷 {v.get('nome')} ({v.get('safra')})</div>"
                f"<p>Tipo: <b>{v.get('tipo', 'N/A')}</b><br>"
                f"C. Barras: <code>{v.get('codigo_barras', 'S/N')}</code><br>"
                f"<span class='badge-pallet-grande'>📍 {v.get('localizacao')}</span></p>"
                f"</div>",
                unsafe_allow_html=True
            )
    else:
        st.info("O estoque está vazio.")

elif st.session_state.menu_atual == "Cadastrar":
    st.subheader("➕ Cadastrar Novo Vinho")
    with st.form("form_cadastrar_vinho"):
        nome_cad = st.text_input("Nome do Vinho").strip().title()
        tipo_cad = st.selectbox("Tipo", ["Tinto", "Branco", "Rosé", "Espumante", "Fortificado"])
        safra_cad = st.text_input("Safra").strip()
        
        col_loc1, col_loc2, col_loc3, col_loc4 = st.columns(4)
        with col_loc1: cor = st.selectbox("Corredor", LISTA_CORREDORES)
        with col_loc2: tipo_l = st.selectbox("Tipo Local", LISTA_LOCAIS_TIPO)
        with col_loc3: num_l = st.selectbox("Número", LISTA_NUMEROS_LOCAL)
        with col_loc4: lado = st.selectbox("Lado", LISTA_LADOS)
        
        localizacao_completa = f"{cor} - {tipo_l} {num_l} ({lado})"
        
        caixa_cad = st.selectbox("Tipo de Caixa", OPCOES_CAIXA)
        codigo_cad = st.text_input("Código de Barras", value=st.session_state.codigo_capturado_cadastro).strip()
        
        if st.form_submit_button("Salvar Vinho"):
            if nome_cad:
                novo_vinho = {
                    "nome": nome_cad,
                    "tipo": tipo_cad,
                    "safra": safra_cad,
                    "localizacao": localizacao_completa,
                    "lado": lado,
                    "caixa": caixa_cad,
                    "codigo_barras": codigo_cad,
                    "foto": ""
                }
                st.session_state.estoque.append(novo_vinho)
                salvar_dados(st.session_state.estoque)
                registrar_log(st.session_state.usuario_logado['nome'], "Cadastrar Vinho", nome_cad)
                st.session_state.codigo_capturado_cadastro = ""
                st.success("Vinho cadastrado com sucesso!")
                st.rerun()
            else:
                st.error("O nome do vinho é obrigatório.")

elif st.session_state.menu_atual == "GerarQR":
    st.subheader("📱 Gerar QR Code de Localização")
    loc_qr = st.selectbox("Selecione o Corredor/Local:", [f"{c} - {t} {n}" for c in LISTA_CORREDORES for t in LISTA_LOCAIS_TIPO for n in LISTA_NUMEROS_LOCAL])
    url_qr = gerar_qr_code_api(loc_qr)
    st.image(url_qr, width=250, caption=f"QR Code: {loc_qr}")
    st.markdown(f"Link direto para impressão: [Abrir QR Code]({url_qr})", unsafe_allow_html=True)

elif st.session_state.menu_atual == "Editar":
    st.subheader("✏️ Editar ou Excluir Vinho")
    if not st.session_state.estoque:
        st.info("Nenhum vinho cadastrado para editar.")
    else:
        nomes_vinhos = [f"{v['nome']} ({v.get('safra', 'S/Safra')}) - {v.get('localizacao', '')}" for v in st.session_state.estoque]
        escolha_ed = st.selectbox("Selecione o Vinho:", nomes_vinhos)
        idx_vinho = nomes_vinhos.index(escolha_ed)
        v_atual = st.session_state.estoque[idx_vinho]
        
        with st.form("form_editar_vinho"):
            n_nome = st.text_input("Nome", value=v_atual.get('nome', '')).strip().title()
            n_safra = st.text_input("Safra", value=v_atual.get('safra', '')).strip()
            n_loc = st.text_input("Localização", value=v_atual.get('localizacao', '')).strip()
            n_barras = st.text_input("Código de Barras", value=v_atual.get('codigo_barras', '')).strip()
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                btn_salvar = st.form_submit_button("💾 Salvar Alterações")
            with col_b2:
                btn_excluir = st.form_submit_button("🗑️ Excluir Vinho")
                
            if btn_salvar:
                v_atual['nome'] = n_nome
                v_atual['safra'] = n_safra
                v_atual['localizacao'] = n_loc
                v_atual['codigo_barras'] = n_barras
                salvar_dados(st.session_state.estoque)
                registrar_log(st.session_state.usuario_logado['nome'], "Editar Vinho", n_nome)
                st.success("Alterações salvas com sucesso!")
                st.rerun()
            elif btn_excluir:
                removido = st.session_state.estoque.pop(idx_vinho)
                salvar_dados(st.session_state.estoque)
                registrar_log(st.session_state.usuario_logado['nome'], "Excluir Vinho", removido.get('nome'))
                st.success("Vinho excluído com sucesso!")
                st.rerun()

elif st.session_state.menu_atual == "Historico":
    st.subheader("📋 Histórico de Auditoria do Galpão")
    logs = carregar_logs()
    if logs:
        for l in logs:
            st.markdown(f"**[{l['data_hora']}] {l['usuario']}** - *{l['acao']}*: {l['detalhes']}")
    else:
        st.info("Nenhum registro de log encontrado.")

elif st.session_state.menu_atual == "GerenciarUsuarios":
    st.subheader("⚙️ Gerenciamento de Contas e Usuários")
    if st.session_state.usuario_logado.get('cargo') != "Desenvolvedor":
        st.error("Acesso negado. Apenas desenvolvedores.")
    else:
        usuarios = st.session_state.usuarios
        for i, usr in enumerate(usuarios):
            st.markdown(f"**Usuário:** {usr['nome']} | **Cargo:** {usr.get('cargo', 'Operador')}")
