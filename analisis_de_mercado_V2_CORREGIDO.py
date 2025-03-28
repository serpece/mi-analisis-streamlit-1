import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io

def obtener_indices_principales():
    """Retorna los principales índices de mercados globales."""
    indices = {
        "Estados Unidos": ["^GSPC", "^DJI", "^IXIC"],  # S&P 500, Dow Jones, NASDAQ
        "Europa": ["^STOXX50E", "^FTSE", "^GDAXI"],    # EURO STOXX 50, FTSE 100, DAX
        "Asia": ["^N225", "^HSI", "000001.SS"]         # Nikkei 225, Hang Seng, Shanghai Composite
    }
    return indices

def obtener_componentes_indice(indice):
    """Obtiene los componentes de un índice específico."""
    componentes = {
        "^GSPC": yf.Tickers("AAPL MSFT AMZN GOOGL META NVDA TSLA JPM V PG").tickers,  # Simplificado
        "^DJI": yf.Tickers("AAPL MSFT AMZN V JPM WMT HD PG UNH DIS").tickers,         # Simplificado
        "^IXIC": yf.Tickers("AAPL MSFT AMZN GOOGL META NVDA TSLA PYPL INTC AMD").tickers, # Simplificado
        "^STOXX50E": yf.Tickers("ASML.AS MC.PA SAP.DE SAN.MC AIR.PA").tickers,        # Simplificado
        "^FTSE": yf.Tickers("HSBA.L BP.L GSK.L ULVR.L AZN.L").tickers,                # Simplificado
        "^GDAXI": yf.Tickers("SAP.DE SIE.DE ALV.DE LIN.DE BAS.DE").tickers,           # Simplificado
        "^N225": yf.Tickers("7203.T 9984.T 6758.T 6954.T 6861.T").tickers,            # Simplificado
        "^HSI": yf.Tickers("0700.HK 0941.HK 0005.HK 1398.HK 0388.HK").tickers,        # Simplificado
        "000001.SS": yf.Tickers("600519.SS 601318.SS 600036.SS 600276.SS 601988.SS").tickers # Simplificado
    }
    return componentes.get(indice, [])

def descargar_datos_historicos(tickers, periodo="1y"):
    """Descarga datos históricos para un conjunto de tickers."""
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=365)
    
    datos = {}
    for ticker_symbol, ticker_obj in tickers.items():
        try:
            hist = ticker_obj.history(period=periodo)
            if not hist.empty:
                datos[ticker_symbol] = hist
        except Exception as e:
            print(f"Error al descargar datos para {ticker_symbol}: {e}")
    
    return datos

def calcular_metricas(datos_historicos):
    """Calcula métricas financieras para cada acción."""
    resultados = {}
    
    for ticker, datos in datos_historicos.items():
        if datos.empty:
            continue
            
        try:
            # Calcular rendimiento anual
            rendimiento_anual = ((datos['Close'].iloc[-1] / datos['Close'].iloc[0]) - 1) * 100
            
            # Calcular volatilidad (desviación estándar)
            rendimientos_diarios = datos['Close'].pct_change().dropna()
            volatilidad = rendimientos_diarios.std() * np.sqrt(252) * 100
            
            # Calcular ratio Sharpe (simplificado, usando tasa libre de riesgo de 2%)
            tasa_libre_riesgo = 2.0
            rendimiento_promedio_anualizado = rendimientos_diarios.mean() * 252 * 100
            sharpe_ratio = (rendimiento_promedio_anualizado - tasa_libre_riesgo) / volatilidad
            
            # Calcular momentos (últimos 30 días vs primeros 30 días)
            if len(datos) >= 60:
                momentum = ((datos['Close'].iloc[-30:].mean() / datos['Close'].iloc[:30].mean()) - 1) * 100
            else:
                momentum = 0
                
            # Obtener información financiera adicional
            info = yf.Ticker(ticker).info
            
            resultados[ticker] = {
                'Nombre': info.get('shortName', ticker),
                'Sector': info.get('sector', 'N/A'),
                'País': info.get('country', 'N/A'),
                'Precio actual': datos['Close'].iloc[-1],
                'Rendimiento anual (%)': rendimiento_anual,
                'Volatilidad (%)': volatilidad,
                'Ratio Sharpe': sharpe_ratio,
                'Momentum (%)': momentum,
                'P/E Ratio': info.get('trailingPE', 'N/A'),
                'Dividendo (%)': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                'Capitalización (M)': info.get('marketCap', 0) / 1000000 if info.get('marketCap') else 0
            }
        except Exception as e:
            print(f"Error al calcular métricas para {ticker}: {e}")
    
    return resultados

def puntuar_acciones(metricas):
    """Asigna una puntuación a cada acción basada en las métricas calculadas."""
    puntuaciones = {}
    
    for ticker, datos in metricas.items():
        try:
            # Ponderación de factores
            puntuacion = 0
            
            # Rendimiento (30%)
            if isinstance(datos.get('Rendimiento anual (%)', 0), (int, float)):
                rendimiento = datos['Rendimiento anual (%)']
                puntuacion += min(max(rendimiento / 5, -10), 10) * 3  # Escala -10 a 10
            
            # Ratio Sharpe (25%)
            if isinstance(datos.get('Ratio Sharpe', 0), (int, float)):
                sharpe = datos['Ratio Sharpe']
                puntuacion += min(max(sharpe * 2, -5), 5) * 5  # Escala -5 a 5
            
            # Momentum (20%)
            if isinstance(datos.get('Momentum (%)', 0), (int, float)):
                momentum = datos['Momentum (%)']
                puntuacion += min(max(momentum / 4, -5), 5) * 4  # Escala -5 a 5
            
            # Volatilidad (15% - inversamente proporcional)
            if isinstance(datos.get('Volatilidad (%)', 0), (int, float)) and datos['Volatilidad (%)'] > 0:
                volatilidad = datos['Volatilidad (%)']
                puntuacion += min(max(5 - (volatilidad / 10), -5), 5) * 3  # Escala -5 a 5
            
            # Dividendos (10%)
            if isinstance(datos.get('Dividendo (%)', 0), (int, float)):
                dividendo = datos['Dividendo (%)']
                puntuacion += min(dividendo, 5) * 2  # Escala 0 a 5
            
            puntuaciones[ticker] = {
                'Nombre': datos['Nombre'],
                'Sector': datos['Sector'],
                'País': datos['País'],
                'Precio': datos['Precio actual'],
                'Rendimiento (%)': datos['Rendimiento anual (%)'],
                'Sharpe': datos['Ratio Sharpe'],
                'Volatilidad (%)': datos['Volatilidad (%)'],
                'Dividendo (%)': datos['Dividendo (%)'],
                'Puntuación': puntuacion
            }
        except Exception as e:
            print(f"Error al puntuar {ticker}: {e}")
    
    return puntuaciones

def generar_pdf(puntuaciones, nombre_archivo="scanner_global_plus.pdf"):
    """Genera un PDF con el análisis de las acciones."""
    doc = SimpleDocTemplate(nombre_archivo, pagesize=letter)
    elementos = []
    
    # Estilos
    estilos = getSampleStyleSheet()
    titulo_estilo = estilos['Heading1']
    subtitulo_estilo = estilos['Heading2']
    texto_estilo = estilos['Normal']
    
    # Título
    elementos.append(Paragraph("Análisis de Mercados de Acciones", titulo_estilo))
    elementos.append(Spacer(1, 0.25*inch))
    elementos.append(Paragraph(f"Informe generado el {datetime.now().strftime('%d/%m/%Y')}", texto_estilo))
    elementos.append(Spacer(1, 0.5*inch))
    
    # Mejores acciones globales
    elementos.append(Paragraph("Las Mejores Oportunidades de Inversión", subtitulo_estilo))
    elementos.append(Spacer(1, 0.1*inch))
    
    # Ordenar por puntuación
    mejores_acciones = sorted(puntuaciones.items(), key=lambda x: x[1]['Puntuación'], reverse=True)[:10]
    
    # Tabla de mejores acciones
    datos_tabla = [["Ticker", "Nombre", "Sector", "País", "Precio", "Rend.(%)", "Sharpe", "Volatilidad", "Div.(%)", "Puntuación"]]
    
    for ticker, datos in mejores_acciones:
        datos_tabla.append([
            ticker,
            datos['Nombre'],
            datos['Sector'],
            datos['País'],
            f"{datos['Precio']:.2f}",
            f"{datos['Rendimiento (%)']:.2f}" if isinstance(datos['Rendimiento (%)'], (int, float)) else "N/A",
            f"{datos['Sharpe']:.2f}" if isinstance(datos['Sharpe'], (int, float)) else "N/A",
            f"{datos['Volatilidad (%)']:.2f}%" if isinstance(datos['Volatilidad (%)'], (int, float)) else "N/A",
            f"{datos['Dividendo (%)']:.2f}%" if isinstance(datos['Dividendo (%)'], (int, float)) else "N/A",
            f"{datos['Puntuación']:.1f}"
        ])
    
    tabla = Table(datos_tabla, repeatRows=1)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elementos.append(tabla)
    elementos.append(Spacer(1, 0.5*inch))
    
    # Gráfico de mejores acciones por puntuación
    if mejores_acciones:
        plt.figure(figsize=(10, 6))
        tickers = [ticker for ticker, _ in mejores_acciones]
        puntuaciones = [datos['Puntuación'] for _, datos in mejores_acciones]
        
        plt.barh(tickers, puntuaciones, color='darkblue')
        plt.xlabel('Puntuación')
        plt.title('Mejores Acciones por Puntuación')
        plt.tight_layout()
        
        # Guardar gráfico en un buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        
        # Añadir imagen al PDF
        img = Image(buffer)
        img.drawHeight = 4*inch
        img.drawWidth = 6*inch
        elementos.append(img)
        
        plt.close()
    
    # Conclusiones y recomendaciones
    elementos.append(Spacer(1, 0.5*inch))
    elementos.append(Paragraph("Conclusiones y Recomendaciones", subtitulo_estilo))
    elementos.append(Spacer(1, 0.1*inch))
    
    conclusiones = """
    Este análisis muestra las acciones con mejor potencial de inversión según una combinación de factores:
    rendimiento histórico, ratio Sharpe, momentum, volatilidad y dividendos. 
    
    Las acciones listadas representan oportunidades interesantes basadas en sus métricas fundamentales
    y técnicas. Sin embargo, es importante realizar un análisis adicional específico para cada título
    y considerar su adecuación a su perfil de riesgo y objetivos de inversión personales.
    
    Recuerde diversificar su cartera para reducir el riesgo y consultar con un asesor financiero
    profesional antes de tomar decisiones de inversión.
    """
    
    elementos.append(Paragraph(conclusiones, texto_estilo))
    
    # Construir el documento
    doc.build(elementos)
    print(f"PDF generado: {nombre_archivo}")

def main():
    print("Iniciando análisis de mercados de acciones...")
    
    # Obtener índices principales
    indices = obtener_indices_principales()
    
    # Recopilar todos los tickers a analizar
    todos_tickers = {}
    for region, ind_list in indices.items():
        print(f"Analizando mercados de {region}...")
        for indice in ind_list:
            componentes = obtener_componentes_indice(indice)
            todos_tickers.update(componentes)
    
    print(f"Total de acciones a analizar: {len(todos_tickers)}")
    
    # Descargar datos históricos
    print("Descargando datos históricos...")
    datos_historicos = descargar_datos_historicos(todos_tickers)
    
    # Calcular métricas
    print("Calculando métricas de inversión...")
    metricas = calcular_metricas(datos_historicos)
    
    # Puntuar acciones
    print("Evaluando y puntuando acciones...")
    puntuaciones = puntuar_acciones(metricas)
    
    # Generar PDF con resultados
    print("Generando informe ...")
    generar_pdf(puntuaciones)
    
    print("Análisis completado!")

if __name__ == "__main__":
    main()