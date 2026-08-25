elif st.session_state.menu_atual == "Editar":
    st.subheader("✏️ Editar ou Excluir Vinhos do Estoque")
    
    if not st.session_state.estoque:
        st.info("Nenhum vinho cadastrado para editar.")
    else:
        opcoes_vinhos = {f"{v['nome']} ({v.get('safra', 'S/ Safra')}) - Local: {v.get('localizacao', 'N/A')} [ID: {v.get('id', idx)}]": idx for idx, v in enumerate(st.session_state.estoque)}
        
        vinho_selecionado_label = st.selectbox("Selecione o Vinho para Editar/Excluir:", list(opcoes_vinhos.keys()), key="select_vinho_edicao")
        idx_vinho = opcoes_vinhos[vinho_selecionado_label]
        vinho_obj = st.session_state.estoque[idx_vinho]
        
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
        
        if st.button("🗑️ Excluir permanentemente este vinho selecionado", type="primary"):
            nome_removido = vinho_obj.get('nome', 'Desconhecido')
            st.session_state.estoque.pop(idx_vinho)
            salvar_dados(st.session_state.estoque)
            registrar_log(st.session_state.usuario_logado['nome'], "Excluiu Vinho", nome_removido)
            st.success(f"Vinho '{nome_removido}' excluído com sucesso do arquivo!")
            st.rerun()
