import streamlit as st
from ANALISIS_DE_MERCADO_CASI_FINAL_FUNCION_COMPLETA_STREAMLIT import ejecutar_analisis_completo
import analisis_de_mercado_V2_CORREGIDO as analisis_global

st.set_page_config(page_title="Análisis Financiero", layout="wide")

st.title("📈 Plataforma de Análisis Financiero")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.header("🔍 Análisis Individual de una Acción")
    ticker = st.text_input("Introduce el ticker (ej. AAPL, MSFT, TSLA):")
    periodo = st.selectbox("Selecciona el período:", ["1y", "3y", "5y"])
    if st.button("Analizar Acción"):
        if ticker:
            with st.spinner("Analizando acción..."):
                resultado = ejecutar_analisis_completo(ticker, periodo)
                st.code(resultado, language='text')
        else:
            st.error("⚠️ Debes introducir un ticker.")

with col2:
    st.header("🌍 Análisis Global del Mercado")
    if st.button("Ejecutar Scanner Global"):
        with st.spinner("Generando informe PDF..."):
            analisis_global.main()
            st.success("✅ Informe generado como 'scanner_global_plus.pdf'")
            with open("scanner_global_plus.pdf", "rb") as f:
                st.download_button(
                    label="📥 Descargar Informe",
                    data=f,
                    file_name="scanner_global_plus.pdf",
                    mime="application/pdf"
                )
