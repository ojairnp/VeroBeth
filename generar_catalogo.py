import requests
import os
import json

APP_KEY = os.environ["DROPBOX_APP_KEY"]
APP_SECRET = os.environ["DROPBOX_APP_SECRET"]
REFRESH_TOKEN = os.environ["DROPBOX_REFRESH_TOKEN"]

BASE_FOLDER = "/VeroBeth"  # AJUSTAR: ej. "/VeroBeth" si tus carpetas XS/S/M/L estan dentro de esa carpeta
TALLAS = ["XS", "S", "M", "L"]
OUTPUT_PATH = "catalogo.json"

EXTENSIONES_IMG = (".jpg", ".jpeg", ".png", ".webp")
EXTENSIONES_VIDEO = (".mp4", ".mov", ".m4v")

def obtener_access_token():
    resp = requests.post(
        "https://api.dropbox.com/oauth2/token",
        data={
            "refresh_token": REFRESH_TOKEN,
            "grant_type": "refresh_token",
            "client_id": APP_KEY,
            "client_secret": APP_SECRET,
        },
    )
    resp.raise_for_status()
    return resp.json()["access_token"]

def listar_archivos(token, ruta):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    archivos = []
    data = {"path": ruta, "recursive": False}
    resp = requests.post(
        "https://api.dropboxapi.com/2/files/list_folder", headers=headers, json=data
    )
    if resp.status_code == 409:
        print(f"AVISO: la carpeta '{ruta}' no existe en Dropbox, se omite.")
        return archivos
    resp.raise_for_status()
    body = resp.json()
    archivos.extend(body["entries"])
    while body.get("has_more"):
        resp = requests.post(
            "https://api.dropboxapi.com/2/files/list_folder/continue",
            headers=headers,
            json={"cursor": body["cursor"]},
        )
        resp.raise_for_status()
        body = resp.json()
        archivos.extend(body["entries"])
    return [a for a in archivos if a[".tag"] == "file"]

def obtener_o_crear_link(token, path_lower):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    resp = requests.post(
        "https://api.dropboxapi.com/2/sharing/list_shared_links",
        headers=headers,
        json={"path": path_lower, "direct_only": True},
    )
    resp.raise_for_status()
    links = resp.json().get("links", [])
    if links:
        url = links[0]["url"]
    else:
        resp = requests.post(
            "https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings",
            headers=headers,
            json={"path": path_lower},
        )
        if resp.status_code == 409:
            resp2 = requests.post(
                "https://api.dropboxapi.com/2/sharing/list_shared_links",
                headers=headers,
                json={"path": path_lower, "direct_only": True},
            )
            resp2.raise_for_status()
            url = resp2.json()["links"][0]["url"]
        else:
            resp.raise_for_status()
            url = resp.json()["url"]

    if "?dl=0" in url:
        url = url.replace("?dl=0", "?raw=1")
    elif "?" not in url:
        url = url + "?raw=1"
    return url

def slug_a_nombre(nombre_archivo):
    nombre = os.path.splitext(nombre_archivo)[0]
    nombre = nombre.replace("-", " ").replace("_", " ")
    return nombre.strip().title()

def tipo_de_archivo(nombre_archivo):
    nombre_lower = nombre_archivo.lower()
    if nombre_lower.endswith(EXTENSIONES_IMG):
        return "imagen"
    if nombre_lower.endswith(EXTENSIONES_VIDEO):
        return "video"
    return None

def main():
    token = obtener_access_token()
    catalogo = []

    for talla in TALLAS:
        ruta = f"{BASE_FOLDER}/{talla}"
        archivos = listar_archivos(token, ruta)
        contador = 0
        for archivo in archivos:
            tipo = tipo_de_archivo(archivo["name"])
            if tipo is None:
                continue
            url = obtener_o_crear_link(token, archivo["path_lower"])
            catalogo.append({
                "nombre": slug_a_nombre(archivo["name"]),
                "talla": talla,
                "tipo": tipo,
                "imagen_url": url,
            })
            contador += 1
        print(f"Talla {talla}: {contador} archivos procesados")

    catalogo.sort(key=lambda x: (x["talla"], x["nombre"]))

    contenido = json.dumps(catalogo, ensure_ascii=False, indent=2)
    with open(OUTPUT_PATH, "wb") as f:
        f.write(contenido.encode("utf-8"))

    print(f"catalogo.json generado con {len(catalogo)} productos")

if __name__ == "__main__":
    main()
