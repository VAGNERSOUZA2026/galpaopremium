            }, { passive: true });

            d.addEventListener('touchend', (ev) => {
                if (!started || !mobile() || !ev.changedTouches || ev.changedTouches.length !== 1) return;
                started = false;
                const t = ev.changedTouches[0];
                const dx = t.clientX - sx;
                const dy = t.clientY - sy;
                if (Math.abs(dy) > 90) return;
                const isOpen = root.classList.contains('pw-mobile-sidebar-open');
                if (!isOpen && sx <= 45 && dx >= 65) openSidebar();
                if (isOpen && dx <= -65) closeSidebar();
            }, { passive: true });

            w.addEventListener('resize', () => {
                if (!mobile()) closeSidebar();
                ensureControls();
            });
        })();
        </script>
        """,
        height=0,
        width=0,
    )
except Exception:
    pass


# ============================================================
# V11.7 — ALERTAS/CARDS SEMPRE LEGÍVEIS
# Corrige textos que só apareciam ao selecionar com o mouse.
# ============================================================
st.markdown(r"""
<style>
/* Alertas nativos do Streamlit: texto sempre escuro e 100% visível. */
html body [data-testid="stAlert"],
html body div[data-testid="stAlert"] {
    color:#2A2224 !important;
    -webkit-text-fill-color:#2A2224 !important;
    opacity:1 !important;
}
html body [data-testid="stAlert"] *,
html body [data-testid="stAlert"] p,
html body [data-testid="stAlert"] span,
html body [data-testid="stAlert"] div,
html body [data-testid="stAlert"] strong,
html body [data-testid="stAlert"] em {
    color:#2A2224 !important;
    -webkit-text-fill-color:#2A2224 !important;
    opacity:1 !important;
    visibility:visible !important;
    text-shadow:none !important;
}

/* Mantém os fundos suaves, mas com contraste suficiente. */
html body [data-testid="stAlert"]:has([data-testid*="success"]),
html body .stAlert-success {
    background:#EAF7EE !important;
    border-color:#B8DEC3 !important;
}
html body [data-testid="stAlert"]:has([data-testid*="info"]),
html body .stAlert-info {
    background:#EAF3FF !important;
    border-color:#B9D4F4 !important;
}
html body [data-testid="stAlert"]:has([data-testid*="warning"]),
html body .stAlert-warning {
    background:#FFF5DB !important;
    border-color:#E9D08D !important;
}
html body [data-testid="stAlert"]:has([data-testid*="error"]),
html body .stAlert-error {
    background:#FCEBEC !important;
    border-color:#E7B9BE !important;
}

/* Alguns releases do Streamlit usam classes BaseWeb internas. */
html body [role="alert"],
html body [role="alert"] * {
    color:#2A2224 !important;
    -webkit-text-fill-color:#2A2224 !important;
    opacity:1 !important;
    visibility:visible !important;
    text-shadow:none !important;
}

/* Evita que estilos antigos deixem textos de caption/markdown transparentes. */
html body [data-testid="stMain"] [data-testid="stAlert"] .stMarkdown,
html body [data-testid="stMain"] [data-testid="stAlert"] .stMarkdown * {
    color:#2A2224 !important;
    -webkit-text-fill-color:#2A2224 !important;
    opacity:1 !important;
}

/* Selecionar o texto continua possível, mas não é mais necessário para ler. */
html body [data-testid="stAlert"] ::selection {
    background:#C89A4A !important;
    color:#171217 !important;
    -webkit-text-fill-color:#171217 !important;
}
</style>
""", unsafe_allow_html=True)
