import requests
import os
import json
import subprocess
import hashlib
import tempfile
from io import BytesIO
from PIL import Image, ImageOps


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
        timeout=60,
        data={
            "refresh_token": os.environ["DROPBOX_REFRESH_TOKEN"],
            "grant_type": "refresh_token",
            "client_id": os.environ["DROPBOX_APP_KEY"],
            "client_secret": os.environ["DROPBOX_APP_SECRET"],
        },
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def listar_archivos(token, ruta):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    archivos = []
    data = {"path": ruta, "recursive": False}
    resp = requests.post(
        "https://api.dropboxapi.com/2/files/list_folder", headers=headers, json=data, timeout=60
    )
    if (resp.status_code == 409
            and resp.json().get("error_summary", "").startswith("path/not_found/")):
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
            timeout=60,
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
        "https://content.dropboxapi.com/2/files/download", headers=headers, timeout=120
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
    imagen = ImageOps.exif_transpose(imagen).convert("RGB")
    if imagen.width > ANCHO_MAX_IMG:
        proporcion = ANCHO_MAX_IMG / imagen.width
        nuevo_alto = int(imagen.height * proporcion)
        imagen = imagen.resize((ANCHO_MAX_IMG, nuevo_alto), Image.LANCZOS)
    imagen.save(ruta_salida, "JPEG", quality=CALIDAD_JPG, optimize=True)


def procesar_video(bytes_originales, ruta_salida):
    ruta_temporal = ruta_salida + ".original.mp4"
    with open(ruta_temporal, "wb") as f:
        f.write(bytes_originales)

    try:
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
                "-movflags", "+faststart",
                ruta_salida,
            ],
            check=True,
        )
    finally:
        if os.path.exists(ruta_temporal):
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

            identidad = archivo["path_lower"] + ":" + archivo["rev"]
            version = hashlib.sha256(identidad.encode("utf-8")).hexdigest()[:16]
            slug = (slug_archivo(archivo["name"])[:80] or "producto") + "-" + version
            extension = ".jpg" if tipo == "imagen" else ".mp4"
            ruta_local = os.path.join(carpeta_local, slug + extension)
            ruta_relativa = "/" + ruta_local.replace("\\", "/")

            if not os.path.exists(ruta_local):
                print(f"Procesando: {archivo['name']}")
                contenido = descargar_archivo(token, archivo["path_lower"])
                temporal = ruta_local + ".tmp" + extension
                try:
                    if tipo == "imagen":
                        procesar_imagen(contenido, temporal)
                    else:
                        procesar_video(contenido, temporal)
                    os.replace(temporal, ruta_local)
                finally:
                    if os.path.exists(temporal):
                        os.remove(temporal)
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
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8",
                                     dir=os.path.dirname(OUTPUT_PATH) or ".",
                                     delete=False) as f:
        temporal = f.name
        f.write(contenido_json)
    os.replace(temporal, OUTPUT_PATH)

    print(f"catalogo.json generado con {len(catalogo)} productos")


if __name__ == "__main__":
    main()