with aba_qr2:
        st.markdown("### 🖨️ Gerador de Lote de Etiquetas")
        st.markdown("Selecione o intervalo para gerar uma página organizada com vários QR Codes prontos para impressão em grade.")
        
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            qtd_corredores = st.slider("Até qual corredor?", 1, 16, 16)
        with col_l2:
            qtd_itens = st.slider("Quantos pallets/itens por corredor?", 1, 25, 11)
            
        lados_lote = st.multiselect("Lados a incluir:", LISTA_LADOS, default=["Direito", "Esquerdo"])
        
        if st.button("Gerar Grade de Etiquetas para Impressão"):
            lista_etiquetas = []
            for c in range(1, qtd_corredores + 1):
                corr_str = f"Corredor {c:02d}"
                for i in range(1, qtd_itens + 1):
                    item_str = f"Item {i:02d}"
                    for lado in lados_lote:
                        texto_loc = f"{corr_str} - Pallet {item_str} - Lado: {lado}"
                        lista_etiquetas.append(texto_loc)
            
            st.session_state.lista_etiquetas_cache = lista_etiquetas
            st.success(f"Foram geradas {len(lista_etiquetas)} etiquetas com base nos seus parâmetros!")

        if "lista_etiquetas_cache" in st.session_state and st.session_state.lista_etiquetas_cache:
            lista_etiquetas = st.session_state.lista_etiquetas_cache
            
            st.markdown("---")
            st.markdown("#### 👁️ Impressão e Pré-visualização")
            
            # Criação do arquivo HTML completo
            html_grade_completo = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Impressão de Etiquetas - Premium Wines</title>
                <style>
                    body { font-family: sans-serif; background: white; margin: 20px; }
                    .grid-container { display: flex; flex-wrap: wrap; gap: 15px; justify-content: center; }
                    .etiqueta-card { border: 2px dashed #7A1C2E; border-radius: 8px; padding: 10px; width: 180px; text-align: center; background: white; page-break-inside: avoid; margin-bottom: 10px; }
                    .etiqueta-card img { display: block; margin: 0 auto; width: 120px; }
                    .etiqueta-texto { font-size: 10px; font-weight: bold; color: #1A1A1A; margin-top: 6px; line-height: 1.2; }
                    .btn-imprimir { position: fixed; top: 20px; right: 20px; background-color: #7A1C2E; color: white; padding: 12px 20px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; z-index: 1000; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
                    .btn-imprimir:hover { background-color: #5c1322; }
                    @media print { .btn-imprimir { display: none; } }
                </style>
            </head>
            <body>
                <button class="btn-imprimir" onclick="window.print()">🖨️ Imprimir / Salvar PDF</button>
                <div class="grid-container">
            """
            
            for etiqueta in lista_etiquetas:
                api_url = gerar_qr_code_api(etiqueta)
                html_grade_completo += f"""
                    <div class="etiqueta-card">
                        <img src="{api_url}">
                        <div class="etiqueta-texto">{etiqueta}</div>
                    </div>
                """
            html_grade_completo += """
                </div>
            </body>
            </html>
            """
            
            # Botão de download nativo do Streamlit (100% confiável e sem bloqueios de pop-up)
            st.download_button(
                label="📥 Baixar Página de Etiquetas Pronta para Impressão (.html)",
                data=html_grade_completo,
                file_name="grade_etiquetas_galpao.json" if False else "grade_etiquetas_galpao.html",
                mime="text/html",
                use_container_width=True
            )
            
            st.markdown("Dica: Clique no botão acima para baixar o arquivo **grade_etiquetas_galpao.html**. Dê um duplo clique nele para abri-lo no seu navegador (Google Chrome, Edge, etc.) e clique no botão vermelho **🖨️ Imprimir / Salvar PDF** no canto superior direito.")
            
            # Pré-visualização na tela principal
            html_preview = "<div style='display: flex; flex-wrap: wrap; gap: 15px; justify-content: center; font-family: sans-serif;'>"
            for etiqueta in lista_etiquetas:
                api_url = gerar_qr_code_api(etiqueta)
                html_preview += f"""
                    <div style="border: 2px dashed #7A1C2E; border-radius: 8px; padding: 10px; width: 180px; text-align: center; background: white; margin-bottom: 10px;">
                        <img src="{api_url}" width="120" style="display: block; margin: 0 auto;">
                        <div style="font-size: 10px; font-weight: bold; color: #1A1A1A; margin-top: 6px; line-height: 1.2;">{etiqueta}</div>
                    </div>
                """
            html_preview += "</div>"
            components.html(html_preview, height=500, scrolling=True)
