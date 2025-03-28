import yfinance as yf
import pandas as pd
import numpy as np
from textblob import TextBlob
import requests
from bs4 import BeautifulSoup
import datetime
import matplotlib.pyplot as plt
import io
import streamlit as st

def obtener_noticias(ticker):
    url = f"https://finance.yahoo.com/quote/{ticker}?p={ticker}&.tsrc=fin-srch"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    headlines = soup.find_all("h3")
    noticias = [h.get_text() for h in headlines[:5]]
    return noticias

def analizar_sentimiento(noticias):
    polaridades = []
    for noticia in noticias:
        blob = TextBlob(noticia)
        polaridades.append(blob.sentiment.polarity)
    if not polaridades:
        return 0
    return sum(polaridades) / len(polaridades)

def ejecutar_analisis_completo(ticker, periodo='5y'):
    try:
        datos = yf.download(ticker, period=periodo)
        if datos.empty:
            return f"No se pudieron obtener datos válidos para {ticker}."

        datos["Media50"] = datos["Close"].rolling(window=50).mean()
        datos["Media200"] = datos["Close"].rolling(window=200).mean()

        datos["Retorno Diario"] = datos["Close"].pct_change()
        volatilidad = datos["Retorno Diario"].std() * np.sqrt(252)

        rendimiento_total = datos["Close"].iloc[-1] / datos["Close"].iloc[0] - 1
        sharpe_ratio = rendimiento_total / volatilidad if volatilidad != 0 else 0

        noticias = obtener_noticias(ticker)
        sentimiento = analizar_sentimiento(noticias)

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(datos["Close"], label="Precio")
        ax.plot(datos["Media50"], label="Media 50 días")
        ax.plot(datos["Media200"], label="Media 200 días")
        ax.set_title(f"Precio de {ticker}")
        ax.legend()
        st.pyplot(fig)

        resultado = f"""
Ticker: {ticker}
Periodo: {periodo}
Rendimiento total: {rendimiento_total:.2%}
Volatilidad anualizada: {volatilidad:.2%}
Sharpe Ratio: {sharpe_ratio:.2f}
Sentimiento medio de noticias: {sentimiento:.2f}
Últimas noticias: {'; '.join(noticias)}
"""

        return resultado
    except Exception as e:
        return f"Error al procesar {ticker}: {e}"
