import requests
import os
import json
import subprocess
from io import BytesIO
from PIL import Image

APP_KEY = os.environ["DROPBOX_APP_KEY"]
APP_SECRET = os.environ["DROPBOX_APP_SECRET"]
REFRESH_TOKEN = os.environ["DROPBOX_REFRESH_TOKEN"]

BASE_FOLDER = "/VeroBeth"
TALLAS = ["XS", "S", "M", "L"]
OUTPUT_PATH = "catalogo.json"
MEDIA_DIR = "media"

EXTENSIONES_IMG = (".jpg", ".jpeg", ".png", ".webp")
EXTENSIONES_VIDEO = (".mp4", ".mov", ".m4v")

ANCHO_MAX_IMG = 1200
CALIDAD_JPG = 75
SEGUNDOS_VIDEO = 6


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


def descargar_archivo(token, path_lower):
    headers = {
        "Authorization": f"Bearer {token}",
        "Dropbox-API-Arg": json.dumps({"path": path_lower}),
    }
    resp = requests.post(
        "https://content.dropboxapi.com/2/files/download", headers=headers
    )
    resp.raise_for_status()
    return resp.content


def slug_archivo(nombre_archivo):
    nombre = os.path.splitext(nombre_archivo)[0]
    nombre = nombre.lower().replace(" ", "-").replace("_", "-")
    nombre = "".join(c for c in nombre if c.isalnum() or c == "-")
    return nombre


def tipo_de_archivo(nombre_archivo):
    nombre_lower = nombre_archivo.lower()
    if nombre_lower.endswith(EXTENSIONES_IMG):
        return "imagen"
    if nombre_lower.endswith(EXTENSIONES_VIDEO):
        return "video"
    return None


def procesar_imagen(bytes_originales, ruta_salida):
    imagen = Image.open(BytesIO(bytes_originales))
    imagen = imagen.convert("RGB")
    if imagen.width > ANCHO_MAX_IMG:
        proporcion = ANCHO_MAX_IMG / imagen.width
        nuevo_alto = int(imagen.height * proporcion)
        imagen = imagen.resize((ANCHO_MAX_IMG, nuevo_alto), Image.LANCZOS)
    imagen.save(ruta_salida, "JPEG", quality=CALIDAD_JPG, optimize=True)


def procesar_video(bytes_originales, ruta_salida):
    ruta_temporal = ruta_salida + ".original.mp4"
    with open(ruta_temporal, "wb") as f:
        f.write(bytes_originales)

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", ruta_temporal,
            "-t", str(SEGUNDOS_VIDEO),
            "-vf", "scale=720:-2",
            "-c:v", "libx264",
            "-crf", "28",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "96k",
            ruta_salida,
        ],
        check=True,
    )
    os.remove(ruta_temporal)


def main():
    token = obtener_access_token()
    catalogo = []

    for talla in TALLAS:
        ruta_dropbox = f"{BASE_FOLDER}/{talla}"
        carpeta_local = os.path.join(MEDIA_DIR, talla)
        os.makedirs(carpeta_local, exist_ok=True)

        archivos = listar_archivos(token, ruta_dropbox)
        contador = 0

        for archivo in archivos:
            tipo = tipo_de_archivo(archivo["name"])
            if tipo is None:
                continue

            slug = slug_archivo(archivo["name"])
            extension = ".jpg" if tipo == "imagen" else ".mp4"
            ruta_local = os.path.join(carpeta_local, slug + extension)
            ruta_relativa = "/" + ruta_local.replace("\\", "/")

            if not os.path.exists(ruta_local):
                print(f"Procesando: {archivo['name']}")
                contenido = descargar_archivo(token, archivo["path_lower"])
                if tipo == "imagen":
                    procesar_imagen(contenido, ruta_local)
                else:
                    procesar_video(contenido, ruta_local)
            else:
                print(f"Ya existe, se omite: {archivo['name']}")

            catalogo.append({
                "talla": talla,
                "tipo": tipo,
                "imagen_url": ruta_relativa,
            })
            contador += 1

        print(f"Talla {talla}: {contador} archivos procesados")

    catalogo.sort(key=lambda x: x["talla"])

    contenido_json = json.dumps(catalogo, ensure_ascii=False, indent=2)
    with open(OUTPUT_PATH, "wb") as f:
        f.write(contenido_json.encode("utf-8"))

    print(f"catalogo.json generado con {len(catalogo)} productos")


if __name__ == "__main__":
    main()