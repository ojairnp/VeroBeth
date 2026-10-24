# Vero Beth

Sitio estático y catálogo sincronizado desde `/VeroBeth/{XS,S,M,L}` en Dropbox.

## Sincronización

El workflow **Actualizar Catalogo Dropbox** se ejecuta diariamente a las 13:00 UTC (08:00 en Cancún), sujeto a las demoras de GitHub Actions. También puede ejecutarse desde Actions → Run workflow en `main`.

Requiere los secretos `DROPBOX_APP_KEY`, `DROPBOX_APP_SECRET` y `DROPBOX_REFRESH_TOKEN` del repositorio. Nunca guardar tokens en archivos ni imprimirlos en registros. Se retiró el antiguo workflow de intercambio OAuth porque imprimía credenciales; si se utilizó, revisar su exposición y renovar el token correspondiente desde Dropbox.

Cada archivo usa su ruta y revisión de Dropbox para generar una URL única. Los archivos nuevos o reemplazados se convierten; los que conservan la revisión se reutilizan. Los eliminados en Dropbox dejan de aparecer en el siguiente catálogo. Los medios históricos se conservan para evitar romper enlaces de WhatsApp ya compartidos.

Una carpeta inexistente se omite; otros errores de API o conversión detienen la ejecución y conservan el catálogo anterior. El JSON se publica solo al completar todas las tallas. La primera ejecución tras esta corrección vuelve a convertir los archivos existentes para registrar sus revisiones.

## Validación local

```sh
python -m pip install requests pillow
python -m unittest discover -s tests -v
for archivo in js/*.js; do node --check "$archivo"; done
python -m http.server 8000
```

La conversión de videos requiere `ffmpeg` instalado. Las pruebas usan respuestas simuladas y no requieren credenciales de Dropbox.
