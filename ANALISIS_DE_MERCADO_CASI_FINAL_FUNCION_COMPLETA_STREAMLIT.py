def ejecutar_analisis_completo(ticker, periodo):
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import yfinance as yf
    from sklearn.linear_model import LinearRegression
    from datetime import datetime
    import requests
    from bs4 import BeautifulSoup
    from textblob import TextBlob
    import io
    import contextlib

    buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):
    df = descargar_datos(ticker, periodo)
    sentimiento = analizar_noticias(ticker)
    analizar_accion(df, sentimiento)

return buffer.getvalue()
        
        
        def descargar_datos(ticker, periodo="5y"):
            try:
                df = yf.download(ticker, period=periodo)
                # Verificar si los datos están vacíos después de la descarga
                if df.empty:
                    print(f"No se encontraron datos para el ticker {ticker}")
                    return None
                df = df[['Close']]
                df.reset_index(inplace=True)
                df.columns = ['Fecha', 'Precio']
                return df
            except Exception as e:
                print(f"Error al descargar datos: {e}")
                return None
        
        def analizar_noticias(ticker):
            print(f"\n📰 Buscando noticias recientes sobre {ticker}...")
            try:
                url = f"https://news.google.com/rss/search?q={ticker}+stock&hl=es&gl=ES&ceid=ES:es"
                response = requests.get(url)
                soup = BeautifulSoup(response.content, features="xml")
                items = soup.findAll('item')
        
                puntuaciones = []
                noticias = []
        
                for item in items[:10]:
                    titulo = item.title.text
                    analisis = TextBlob(titulo)
                    sentimiento = analisis.sentiment.polarity
                    puntuaciones.append(sentimiento)
                    noticias.append((titulo, sentimiento))
        
                if puntuaciones:
                    promedio = sum(puntuaciones) / len(puntuaciones)
        
                    print("\n🧠 Análisis de Sentimiento de Noticias:")
                    for titulo, s in noticias:
                        color = "🔴" if s < 0 else ("🟢" if s > 0 else "⚪")
                        print(f"{color} {titulo} ({s:.2f})")
        
                    if promedio > 0.1:
                        conclusion = "🟢 Sentimiento general POSITIVO"
                    elif promedio < -0.1:
                        conclusion = "🔴 Sentimiento general NEGATIVO"
                    else:
                        conclusion = "⚪ Sentimiento general NEUTRO"
        
                    print(f"\n📊 Resultado del análisis de sentimiento: {conclusion}")
                    if "POSITIVO" in conclusion:
                        return "POSITIVO"
                    elif "NEGATIVO" in conclusion:
                        return "NEGATIVO"
                    else:
                        return "NEUTRO"
                else:
                    print("⚠️ No se encontraron suficientes noticias.")
                    return "Sin datos"
            except Exception as e:
                print(f"❌ Error al analizar noticias: {e}")
                return "Sin datos"
        
        def analizar_accion(df, sentimiento_global="NEUTRO"):
            if df is None or df.empty:
                print("Error: No se pudieron obtener datos válidos.")
                return
        
            print("✅ Datos descargados correctamente. Procesando análisis...")
        
            df['Fecha'] = pd.to_datetime(df['Fecha'])
            df = df.sort_values('Fecha').dropna()
            df['Retorno'] = df['Precio'].pct_change()
            df['Volatilidad'] = df['Retorno'].rolling(window=30).std()
            df['MA50'] = df['Precio'].rolling(window=50).mean()
            df['MA200'] = df['Precio'].rolling(window=200).mean()
        
            df['EMA12'] = df['Precio'].ewm(span=12, adjust=False).mean()
            df['EMA26'] = df['Precio'].ewm(span=26, adjust=False).mean()
            df['MACD'] = df['EMA12'] - df['EMA26']
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
            df['SMA20'] = df['Precio'].rolling(window=20).mean()
            df['BB_Upper'] = df['SMA20'] + (df['Precio'].rolling(window=20).std() * 2)
            df['BB_Lower'] = df['SMA20'] - (df['Precio'].rolling(window=20).std() * 2)
        
            delta = df['Precio'].diff()
            gain = delta.where(delta > 0, 0).fillna(0)
            loss = -delta.where(delta < 0, 0).fillna(0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            df['RSI'] = 100 - (100 / (1 + rs))
        
            # Cálculo del ATR (Average True Range)
            df['High'] = df['Precio']  # Ya que solo tenemos precios de cierre
            df['Low'] = df['Precio']   # Usamos el mismo precio para simular
            
            df['TR1'] = abs(df['High'] - df['Low'])
            df['TR2'] = abs(df['High'] - df['Precio'].shift(1))
            df['TR3'] = abs(df['Low'] - df['Precio'].shift(1))
            df['TR'] = df[['TR1', 'TR2', 'TR3']].max(axis=1)
            df['ATR'] = df['TR'].rolling(window=14).mean()
        
            # Mejora en la estrategia de trading
            df['Signal_BT'] = 0
            
            # Condiciones de compra: MACD cruza por encima de la señal y RSI < 70 y precio por encima de MA50
            df.loc[(df['MACD'] > df['Signal']) & 
                   (df['MACD'].shift(1) <= df['Signal'].shift(1)) & 
                   (df['RSI'] < 70) & 
                   (df['Precio'] > df['MA50']), 'Signal_BT'] = 1
            
            # Condiciones de venta: MACD cruza por debajo de la señal o RSI > 70 o precio por debajo de MA50
            df.loc[(df['MACD'] < df['Signal']) & 
                   (df['MACD'].shift(1) >= df['Signal'].shift(1)) | 
                   (df['RSI'] > 70) | 
                   (df['Precio'] < df['MA50']), 'Signal_BT'] = -1
        
            rsi_actual = df['RSI'].iloc[-1]
            macd_actual = df['MACD'].iloc[-1]
            signal_actual = df['Signal'].iloc[-1]
        
            # Sharpe Ratio
            rf = 0.01  # tasa libre de riesgo del 1%
            avg_return = df['Retorno'].mean() * 252
            volatility = df['Retorno'].std() * np.sqrt(252)
            sharpe_ratio = (avg_return - rf) / volatility if volatility != 0 else 0
        
            print("📊 Calculando indicadores...")
        
            recomendacion = ""
            periodo_optimo = ""
        
            if macd_actual > signal_actual and rsi_actual < 70:
                recomendacion = "✅ RECOMENDACIÓN: COMPRAR - Tendencia alcista confirmada."
                periodo_optimo = "Mediano plazo (3-12 meses)"
            elif rsi_actual > 70:
                recomendacion = "❌ RECOMENDACIÓN: NO COMPRAR - RSI indica sobrecompra, posible corrección."
            elif macd_actual < signal_actual:
                recomendacion = "❌ RECOMENDACIÓN: VENDER - MACD sugiere debilitamiento de la tendencia."
            else:
                recomendacion = "🔍 RECOMENDACIÓN: ESPERAR - Señales mixtas, mejor analizar más antes de invertir."
        
            if sentimiento_global == "NEGATIVO" and "COMPRAR" in recomendacion:
                recomendacion += "\n⚠️ El análisis técnico es positivo, pero las noticias recientes son NEGATIVAS. Precaución."
            elif sentimiento_global == "POSITIVO" and "VENDER" in recomendacion:
                recomendacion += "\n🟢 Aunque el técnico sugiere venta, las noticias son POSITIVAS. Considera esperar confirmación."
        
            print("📈 Mostrando gráficos...")
        
            plt.figure(figsize=(14, 12))
        
            plt.subplot(3, 1, 1)
            plt.plot(df['Fecha'], df['Precio'], label='Precio de Cierre', color='blue')
            plt.plot(df['Fecha'], df['MA50'], label='Media Móvil 50 días', color='orange')
            plt.plot(df['Fecha'], df['MA200'], label='Media Móvil 200 días', color='red')
            buy_signals = df[df['Signal_BT'] == 1]
            sell_signals = df[df['Signal_BT'] == -1]
            plt.scatter(buy_signals['Fecha'], buy_signals['Precio'], marker='^', color='green', label='Compra')
            plt.scatter(sell_signals['Fecha'], sell_signals['Precio'], marker='v', color='red', label='Venta')
            plt.title("📈 Evolución del Precio con Medias Móviles y Señales")
            plt.xlabel("Fecha")
            plt.ylabel("Precio")
            plt.legend()
            plt.grid(True)
        
            plt.subplot(3, 1, 2)
            plt.plot(df['Fecha'], df['Precio'], label='Precio de Cierre', color='blue')
            plt.plot(df['Fecha'], df['BB_Upper'], label='Banda Superior BB', color='green', linestyle='dashed')
            plt.plot(df['Fecha'], df['BB_Lower'], label='Banda Inferior BB', color='red', linestyle='dashed')
            plt.title("📊 Bandas de Bollinger")
            plt.xlabel("Fecha")
            plt.ylabel("Precio")
            plt.legend()
            plt.grid(True)
            
            # Nuevo gráfico para RSI y MACD
            plt.subplot(3, 1, 3)
            plt.plot(df['Fecha'], df['RSI'], label='RSI', color='purple')
            plt.axhline(y=70, color='r', linestyle='--', alpha=0.5)
            plt.axhline(y=30, color='g', linestyle='--', alpha=0.5)
            plt.title("📉 RSI y MACD")
            plt.xlabel("Fecha")
            plt.ylabel("RSI")
            plt.legend(loc='upper left')
            plt.grid(True)
            
            # MACD en el mismo gráfico pero con eje Y secundario
            ax2 = plt.twinx()
            ax2.plot(df['Fecha'], df['MACD'], label='MACD', color='blue')
            ax2.plot(df['Fecha'], df['Signal'], label='Señal', color='red')
            ax2.set_ylabel('MACD')
            ax2.legend(loc='upper right')
        
            plt.tight_layout()
            import streamlit as st
        st.pyplot(plt.gcf())
            plt.pause(0.1)
        
        
            print("\n🔎 RESULTADOS DEL ANÁLISIS:")
            print(f"📅 Fecha de los datos: {df['Fecha'].iloc[0].strftime('%Y-%m-%d')} - {df['Fecha'].iloc[-1].strftime('%Y-%m-%d')}")
            print(f"💰 Precio actual: {df['Precio'].iloc[-1]:.2f} USD")
            print(f"📈 Media Móvil 50 días: {df['MA50'].iloc[-1]:.2f} USD")
            print(f"📉 Media Móvil 200 días: {df['MA200'].iloc[-1]:.2f} USD")
            print(f"📊 MACD actual: {df['MACD'].iloc[-1]:.4f}")
            print(f"📊 Señal MACD: {df['Signal'].iloc[-1]:.4f}")
            print(f"📊 RSI actual: {df['RSI'].iloc[-1]:.2f}")
            print(f"📊 Banda Superior BB: {df['BB_Upper'].iloc[-1]:.2f} USD")
            print(f"📊 Banda Inferior BB: {df['BB_Lower'].iloc[-1]:.2f} USD")
            print(f"📊 ATR actual: {df['ATR'].iloc[-1]:.4f}")
            print(f"📊 Sharpe Ratio: {sharpe_ratio:.2f}")
        
            print("\n🔁 Ejecutando backtesting básico...")
            in_position = False
            buy_price = 0
            trades = []
        
            for index, row in df.iterrows():
                if row['Signal_BT'] == 1 and not in_position:
                    buy_price = row['Precio']
                    buy_date = row['Fecha']
                    in_position = True
                elif row['Signal_BT'] == -1 and in_position:
                    sell_price = row['Precio']
                    sell_date = row['Fecha']
                    rendimiento = (sell_price - buy_price) / buy_price
                    trades.append((buy_date.date(), sell_date.date(), buy_price, sell_price, rendimiento))
                    in_position = False
        
            if trades:
                print("\n📊 Resultados del Backtesting:")
                for t in trades:
                    print(f"🟢 Compra: {t[0]} a {t[2]:.2f} | 🔴 Venta: {t[1]} a {t[3]:.2f} | 📈 Rentabilidad: {t[4]*100:.2f}%")
                total_return = sum(t[4] for t in trades)
                print(f"\n💰 Rentabilidad total acumulada: {total_return*100:.2f}%")
                
                # Nuevas métricas
                rentabilidades = [t[4] for t in trades]
                operaciones_ganadoras = sum(1 for r in rentabilidades if r > 0)
                operaciones_perdedoras = sum(1 for r in rentabilidades if r <= 0)
                porcentaje_acierto = (operaciones_ganadoras / len(trades)) * 100 if trades else 0
                retorno_promedio = (sum(rentabilidades) / len(rentabilidades)) * 100 if rentabilidades else 0
                
                print(f"📊 Total de operaciones: {len(trades)}")
                print(f"✅ Operaciones ganadoras: {operaciones_ganadoras} ({porcentaje_acierto:.2f}%)")
                print(f"❌ Operaciones perdedoras: {operaciones_perdedoras} ({100-porcentaje_acierto:.2f}%)")
                print(f"📈 Retorno promedio por operación: {retorno_promedio:.2f}%")
            else:
                print("⚠️ No se encontraron operaciones de compra/venta para el backtesting.")
        
            print("\n🔎 Análisis finalizado.")
            print(recomendacion)
            if periodo_optimo:
                print(f"📌 PERIODO ÓPTIMO DE INVERSIÓN: {periodo_optimo}")
        
            pass  # input() removido para compatibilidad con Streamlit
        
        def guardar_resultados(df, ticker, trades):
            """Guarda los resultados del análisis en archivos CSV"""
            try:
                # Guardar DataFrame con indicadores
                fecha_actual = datetime.now().strftime("%Y%m%d")
                df.to_csv(f"{ticker}_analisis_{fecha_actual}.csv", index=False)
                
                # Guardar registro de operaciones
                if trades:
                    trades_df = pd.DataFrame(trades, columns=['Fecha_Compra', 'Fecha_Venta', 'Precio_Compra', 
                                                              'Precio_Venta', 'Rentabilidad'])
                    trades_df.to_csv(f"{ticker}_trades_{fecha_actual}.csv", index=False)
                
                print(f"\n✅ Resultados guardados en archivos CSV con prefijo {ticker}")
            except Exception as e:
                print(f"❌ Error al guardar resultados: {e}")
    return buffer.getvalue()
