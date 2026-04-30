"""
captura_invas.py
================
Entra a Invas Monitor, extrae los datos del dashboard
y genera un archivo datos.json listo para el dashboard HTML.

INSTALACIÓN:
    python -m pip install selenium webdriver-manager

EJECUCIÓN:
    python captura_invas.py
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time, os, json, re, logging
from datetime import datetime

# ─────────────────────────────────────────────
INVAS_URL   = "https://serviallinvas.impruvex.com/invaswmsbi/dashboard/0d36ee35-8490-4f04-9db1-103a3fae6fa7/"
USUARIO     = "JCISTERNA"     # <-- cambiar
CONTRASENA  = "Serviall2026."  # <-- cambiar
CARPETA     = "."              # carpeta donde guardar datos.json
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("captura_invas.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


def iniciar_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--lang=es-CL")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=opts
    )
    return driver


def login(driver):
    log.info("Navegando a Invas...")
    driver.get(INVAS_URL)
    time.sleep(4)
    url = driver.current_url.lower()
    if "login" in url or "signin" in url or "account" in url:
        log.info("Login detectado...")
        for sel in ["input[name='username']","input[name='user']","input[type='text']"]:
            try:
                f = driver.find_element(By.CSS_SELECTOR, sel)
                f.clear(); f.send_keys(USUARIO); break
            except: continue
        driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(CONTRASENA)
        for sel in ["button[type='submit']","input[type='submit']","button[class*='btn-primary']","button"]:
            try: driver.find_element(By.CSS_SELECTOR, sel).click(); break
            except: continue
        time.sleep(6)
    if "dashboard" not in driver.current_url:
        driver.get(INVAS_URL)
        time.sleep(5)


def esperar_carga(driver):
    log.info("Esperando carga...")
    time.sleep(5)
    alto = driver.execute_script("return document.body.scrollHeight")
    for i in range(5):
        driver.execute_script(f"window.scrollTo(0, {(alto//4)*i});")
        time.sleep(1)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)


def extraer_texto_pagina(driver):
    """Extrae todo el texto visible de la página."""
    return driver.find_element(By.TAG_NAME, "body").text


def extraer_kpis(driver):
    """Extrae las 3 fichas KPI."""
    kpis = []
    try:
        fichas = driver.find_elements(By.CSS_SELECTOR, ".reportCard.widget-stats, .widget.widget-stats")
        for ficha in fichas[:3]:
            texto = ficha.text.strip().split("\n")
            titulo = texto[0] if len(texto) > 0 else ""
            valor  = texto[1] if len(texto) > 1 else ""
            sub    = texto[2] if len(texto) > 2 else ""
            kpis.append({"titulo": titulo, "valor": valor, "subtitulo": sub})
            log.info(f"  KPI: {titulo} = {valor}")
    except Exception as e:
        log.warning(f"Error extrayendo KPIs: {e}")
    return kpis


def extraer_grafico_por_texto(texto_pagina, titulo_grafico):
    """
    Extrae datos de un gráfico buscando el patrón 'LABEL (VALOR)' en el texto.
    Los gráficos de Invas (ApexCharts) generan texto con ese formato en el eje X.
    """
    # Buscar la sección del gráfico
    idx = texto_pagina.find(titulo_grafico)
    if idx == -1:
        return []
    seccion = texto_pagina[idx:idx+2000]
    # Patrón: texto (número) — puede tener % o decimales
    patron = r'([A-Z0-9\-\.\s]+)\s*\(([0-9]+\.?[0-9]*\s*%?)\)'
    matches = re.findall(patron, seccion)
    # Deduplicar — Invas repite cada label dos veces en el DOM
    vistos = set()
    resultado = []
    for label, valor in matches:
        label = label.strip()
        valor = valor.strip()
        if label not in vistos and len(label) > 0:
            vistos.add(label)
            # Convertir valor a número
            num = float(valor.replace("%","").strip())
            resultado.append({"label": label, "valor": num})
    return resultado


def extraer_tabla_ocupacion(driver):
    """Extrae la tabla de ocupación de ubicaciones."""
    filas = []
    try:
        tabla = driver.find_element(By.CSS_SELECTOR, "table")
        rows  = tabla.find_elements(By.CSS_SELECTOR, "tbody tr")
        for row in rows:
            celdas = [td.text.strip() for td in row.find_elements(By.TAG_NAME, "td")]
            if len(celdas) >= 7:
                filas.append({
                    "region":   celdas[0],
                    "area":     celdas[1],
                    "tipo":     celdas[2],
                    "total":    celdas[3],
                    "ocupadas": celdas[4],
                    "disponibles": celdas[5],
                    "porcentaje":  celdas[6]
                })
        log.info(f"  Tabla ocupación: {len(filas)} filas")
    except Exception as e:
        log.warning(f"Error extrayendo tabla: {e}")
    return filas


def main():
    log.info("=" * 50)
    log.info("Iniciando extracción — " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    log.info("=" * 50)

    driver = iniciar_driver()
    try:
        login(driver)
        esperar_carga(driver)

        texto = extraer_texto_pagina(driver)
        log.info("Texto de página extraído.")

        datos = {
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "kpis": extraer_kpis(driver),
            "tareas_por_dia": extraer_grafico_por_texto(texto, "TAREAS POR DÍA MES EN CURSO"),
            "cumplimiento":   extraer_grafico_por_texto(texto, "CUMPLIMIENTO OPERACIONAL"),
            "picking_mensual":extraer_grafico_por_texto(texto, "TAREAS DE PICKING MENSUALES"),
            "promedio_ruta":  extraer_grafico_por_texto(texto, "PROMEDIO MENSUAL TAREAS PICKING POR RUTA"),
            "despachos_mes":  extraer_grafico_por_texto(texto, "LISTAS DE PICKING DESPACHADAS POR MES"),
            "ocupacion":      extraer_tabla_ocupacion(driver),
        }

        ruta_json = os.path.join(CARPETA, "datos.json")
        with open(ruta_json, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)

        log.info(f"datos.json guardado en {ruta_json}")
        log.info("Extracción completada exitosamente.")

    except Exception as e:
        log.error(f"Error general: {e}")
        raise
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
