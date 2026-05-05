"""
captura_invas.py — v4
=====================
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
CARPETA     = "."
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
        for sel in ["input[name='username']", "input[name='user']", "input[type='text']"]:
            try:
                f = driver.find_element(By.CSS_SELECTOR, sel)
                f.clear(); f.send_keys(USUARIO); break
            except: continue
        driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(CONTRASENA)
        for sel in ["button[type='submit']", "input[type='submit']", "button[class*='btn-primary']", "button"]:
            try: driver.find_element(By.CSS_SELECTOR, sel).click(); break
            except: continue
        time.sleep(6)
    if "dashboard" not in driver.current_url:
        driver.get(INVAS_URL)
        time.sleep(5)


def esperar_carga(driver):
    log.info("Esperando carga completa...")
    time.sleep(6)
    alto = driver.execute_script("return document.body.scrollHeight")
    for i in range(6):
        driver.execute_script(f"window.scrollTo(0, {(alto//5)*i});")
        time.sleep(1.5)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(3)
    log.info("Carga completada.")


def parsear_lineas(texto_panel):
    """Extrae datos buscando lineas con patron LABEL (VALOR)."""
    resultado = []
    vistos = set()
    ignorar = ['Download SVG', 'Download PNG', 'Download CSV']
    patron = re.compile(r'^(.+?)\s*\(([0-9]+\.?[0-9]*\s*%?)\)')
    for linea in texto_panel.split('\n'):
        linea = linea.strip()
        m = patron.match(linea)
        if m:
            label = m.group(1).strip()
            valor_str = m.group(2).strip().replace('%', '').strip()
            if len(label) > 40 or label in ignorar: continue
            if re.match(r'^[0-9\.]+$', label): continue
            if label not in vistos:
                try:
                    num = float(valor_str)
                    resultado.append({"label": label, "valor": num})
                    vistos.add(label)
                except: pass
    return resultado


def extraer_kpis(driver):
    kpis = []
    try:
        fichas = driver.find_elements(By.CSS_SELECTOR, ".reportCard.widget-stats, .widget.widget-stats")
        for ficha in fichas[:3]:
            lineas = [l.strip() for l in ficha.text.strip().split("\n") if l.strip()]
            titulo = lineas[0] if len(lineas) > 0 else ""
            valor  = lineas[1] if len(lineas) > 1 else ""
            sub    = lineas[2] if len(lineas) > 2 else ""
            kpis.append({"titulo": titulo, "valor": valor, "subtitulo": sub})
            log.info(f"  KPI: {titulo} = {valor}")
    except Exception as e:
        log.warning(f"Error KPIs: {e}")
    return kpis


def extraer_grafico(driver, titulo_buscar):
    try:
        paneles = driver.find_elements(By.CSS_SELECTOR, ".panel.reportPanel, .reportPanel")
        log.info(f"  Buscando '{titulo_buscar}' en {len(paneles)} paneles...")
        for panel in paneles:
            texto = panel.text
            if titulo_buscar.upper() in texto.upper():
                datos = parsear_lineas(texto)
                log.info(f"  '{titulo_buscar}': {len(datos)} puntos -> {[d['label'] for d in datos]}")
                return datos
        log.warning(f"  Panel '{titulo_buscar}' no encontrado")
        return []
    except Exception as e:
        log.warning(f"  Error '{titulo_buscar}': {e}")
        return []


def extraer_top5_operadores(driver):
    """Extrae la tabla TOP 5 tareas procesadas por operador."""
    filas = []
    try:
        paneles = driver.find_elements(By.CSS_SELECTOR, ".panel.reportPanel, .reportPanel")
        for panel in paneles:
            texto = panel.text
            if "TOP 5" in texto.upper() or "PROCESADAS EN 20" in texto.upper():
                rows = panel.find_elements(By.CSS_SELECTOR, "tbody tr")
                for row in rows:
                    celdas = [td.text.strip() for td in row.find_elements(By.TAG_NAME, "td")]
                    if len(celdas) >= 3:
                        filas.append({
                            "operador":   celdas[0],
                            "total":      celdas[1],
                            "porcentaje": celdas[2]
                        })
                log.info(f"  TOP 5 operadores: {len(filas)} filas")
                break
        if not filas:
            log.warning("  TOP 5 no encontrado")
    except Exception as e:
        log.warning(f"  Error TOP 5: {e}")
    return filas


def extraer_tabla_ocupacion(driver):
    filas = []
    try:
        tablas = driver.find_elements(By.CSS_SELECTOR, "table")
        for tabla in tablas:
            rows = tabla.find_elements(By.CSS_SELECTOR, "tbody tr")
            if len(rows) > 3:
                for row in rows:
                    celdas = [td.text.strip() for td in row.find_elements(By.TAG_NAME, "td")]
                    if len(celdas) >= 7:
                        filas.append({
                            "region":      celdas[0],
                            "area":        celdas[1],
                            "tipo":        celdas[2],
                            "total":       celdas[3],
                            "ocupadas":    celdas[4],
                            "disponibles": celdas[5],
                            "porcentaje":  celdas[6]
                        })
                if filas:
                    log.info(f"  Tabla ocupacion: {len(filas)} filas")
                    break
    except Exception as e:
        log.warning(f"  Error tabla: {e}")
    return filas


def main():
    log.info("=" * 50)
    log.info("Iniciando extraccion — " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    log.info("=" * 50)

    driver = iniciar_driver()
    try:
        login(driver)
        esperar_carga(driver)

        datos = {
            "timestamp":        datetime.now().strftime("%d/%m/%Y %H:%M"),
            "kpis":             extraer_kpis(driver),
            "tareas_por_dia":   extraer_grafico(driver, "TAREAS POR"),
            "cumplimiento":     extraer_grafico(driver, "CUMPLIMIENTO OPERACIONAL"),
            "picking_mensual":  extraer_grafico(driver, "TAREAS DE PICKING MENSUALES"),
            "promedio_ruta":    extraer_grafico(driver, "PROMEDIO MENSUAL TAREAS PICKING POR RUTA"),
            "despachos_mes":    extraer_grafico(driver, "LISTAS DE PICKING DESPACHADAS"),
            "top5_operadores":  extraer_top5_operadores(driver),
            "ocupacion":        extraer_tabla_ocupacion(driver),
        }

        ruta_json = os.path.join(CARPETA, "datos.json")
        with open(ruta_json, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)

        log.info("datos.json guardado.")
        log.info("Extraccion completada exitosamente.")

    except Exception as e:
        log.error(f"Error general: {e}")
        raise
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
