"""
subir_datos.py
==============
Sube datos.json a GitHub usando la API REST.
No usa Git — nunca puede pisar otros archivos.

CONFIGURACIÓN:
  Edita las variables GITHUB_TOKEN, REPO_OWNER y REPO_NAME
"""

import requests, base64, json, os

# ─────────────────────────────────────────────
GITHUB_TOKEN = "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"   # <-- pega tu Personal Access Token
REPO_OWNER   = "josecisternaferreira"
REPO_NAME    = "dashboard-serviall"
ARCHIVO      = "datos.json"
# ─────────────────────────────────────────────

def subir_archivo():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{ARCHIVO}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Leer el archivo local
    with open(ARCHIVO, "r", encoding="utf-8") as f:
        contenido = f.read()

    contenido_b64 = base64.b64encode(contenido.encode("utf-8")).decode("utf-8")

    # Obtener el SHA actual del archivo en GitHub (necesario para actualizarlo)
    resp = requests.get(url, headers=headers)
    sha = resp.json().get("sha") if resp.status_code == 200 else None

    # Subir el archivo
    payload = {
        "message": "Actualizacion automatica datos.json",
        "content": contenido_b64,
    }
    if sha:
        payload["sha"] = sha

    resp = requests.put(url, headers=headers, json=payload)

    if resp.status_code in [200, 201]:
        print(f"[OK] datos.json subido exitosamente a GitHub")
    else:
        print(f"[ERROR] {resp.status_code}: {resp.json()}")
        exit(1)

if __name__ == "__main__":
    subir_archivo()
