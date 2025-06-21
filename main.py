
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from institucional import analizar_mercado
import os

app = FastAPI(
    title="API Análisis Institucional Multi-Timeframe",
    description="API para análisis de trading institucional con zonas de liquidez y order blocks en múltiples temporalidades",
    version="2.0.0"
)

@app.get("/")
def read_root():
    return {
        "message": "API de Análisis Institucional Multi-Timeframe",
        "endpoints": {
            "/analisis": "Análisis completo del mercado. Query param: tf (1min/5min/15min)",
            "/analisis/{symbol}": "Análisis de un símbolo específico. Query param: tf (1min/5min/15min)",
            "/analisis/confirmacion": "Confluencia multi-timeframe (M1, M5, M15). Query param: symbol"
        },
        "ejemplos": {
            "M1": "/analisis?tf=1min",
            "M5": "/analisis?tf=5min", 
            "M15": "/analisis?tf=15min",
            "Multi-symbol": "/analisis/GBPUSD?tf=5min",
            "Confluencia": "/analisis/confirmacion?symbol=EURUSD"
        }
    }

@app.get("/analisis")
def get_analisis(tf: str = Query("1min", enum=["1min", "5min", "15min"])):
    """
    Análisis del mercado por defecto (EURUSD) con timeframe seleccionable
    """
    try:
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
        resultado = analizar_mercado(symbol="EURUSD", api_key=api_key, interval=tf)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el análisis: {str(e)}")

@app.get("/analisis/{symbol}")
def get_analisis_symbol(symbol: str, tf: str = Query("1min", enum=["1min", "5min", "15min"])):
    """
    Análisis de un símbolo específico con timeframe seleccionable
    """
    try:
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
        resultado = analizar_mercado(symbol=symbol.upper(), api_key=api_key, interval=tf)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el análisis de {symbol}: {str(e)}")

@app.get("/analisis/confirmacion")
def get_confirmacion(symbol: str = Query("EURUSD")):
    """
    Análisis multi-timeframe para confluencia institucional (M1, M5, M15)
    Incluye zonas de liquidez y ruptura por TF
    """
    try:
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
        tf_list = ["1min", "5min", "15min"]
        resultados = {}
        señales = []
        
        for tf in tf_list:
            res = analizar_mercado(symbol=symbol.upper(), api_key=api_key, interval=tf)
            resultados[tf] = {
                "señal": res.get("señal"),
                "motivo": res.get("motivo"),
                "precio_entrada": res.get("precio_entrada"),
                "stop_loss": res.get("stop_loss"),
                "take_profit": res.get("take_profit"),
                "zonas_liquidez": res.get("zonas_liquidez", []),
                "zonas_ruptura": res.get("order_blocks", []),  # Order blocks como zonas de ruptura
                "hora": res.get("timestamp")
            }
            señales.append(res.get("señal", "hold"))
        
        # Busca confluencia: las tres señales iguales y no "hold"
        if señales[0] == señales[1] == señales[2] and señales[0] not in ["hold", None]:
            confirmacion = señales[0]
            motivo = "Confluencia institucional detectada en todas las temporalidades"
        else:
            confirmacion = "NO TRADE"
            motivo = "No hay confirmación institucional multi-timeframe"
        
        return {
            "symbol": symbol.upper(),
            "M1": resultados["1min"],
            "M5": resultados["5min"],
            "M15": resultados["15min"],
            "confirmacion": confirmacion,
            "motivo": motivo
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el análisis de confirmación: {str(e)}")

@app.get("/health")
def health_check():
    """
    Endpoint de verificación de salud
    """
    return {"status": "healthy", "service": "analisis-institucional"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
