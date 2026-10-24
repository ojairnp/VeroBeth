import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
from io import BytesIO

import requests
from PIL import Image
import generar_catalogo as app


class CatalogoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        old = os.getcwd()
        os.chdir(self.temp.name)
        self.addCleanup(os.chdir, old)
        image = BytesIO()
        Image.new('RGB', (20, 30)).save(image, 'PNG')
        self.image = image.getvalue()

    def archivo(self, name='foto.png', rev='1'):
        return {'name': name, 'rev': rev, 'path_lower': '/verobeth/s/' + name}

    def generar(self, archivos):
        with patch.object(app, 'obtener_access_token', return_value='mock'), \
             patch.object(app, 'listar_archivos', side_effect=lambda token, ruta: archivos if ruta.endswith('/S') else []), \
             patch.object(app, 'descargar_archivo', return_value=self.image) as download:
            app.main()
            return json.loads(Path('catalogo.json').read_text()), download.call_count

    def test_reemplazo_y_cache(self):
        primero, count = self.generar([self.archivo()])
        self.assertEqual(count, 1)
        igual, count = self.generar([self.archivo()])
        self.assertEqual(count, 0)
        nuevo, count = self.generar([self.archivo(rev='2')])
        self.assertEqual(count, 1)
        self.assertEqual(primero, igual)
        self.assertNotEqual(primero[0]['imagen_url'], nuevo[0]['imagen_url'])

    def test_colisiones_y_eliminacion(self):
        datos, _ = self.generar([self.archivo('a b.png'), self.archivo('a-b.png')])
        self.assertEqual(len({p['imagen_url'] for p in datos}), 2)
        datos, _ = self.generar([])
        self.assertEqual(datos, [])

    def test_error_no_sobrescribe_catalogo(self):
        Path('catalogo.json').write_text('["previo"]')
        with patch.object(app, 'obtener_access_token', return_value='mock'), \
             patch.object(app, 'listar_archivos', side_effect=requests.HTTPError):
            with self.assertRaises(requests.HTTPError):
                app.main()
        self.assertEqual(Path('catalogo.json').read_text(), '["previo"]')

    def test_solo_not_found_se_omite(self):
        for summary, missing in [('path/not_found/', True), ('path/not_folder/', False)]:
            response = Mock(status_code=409)
            response.json.return_value = {'error_summary': summary}
            response.raise_for_status.side_effect = requests.HTTPError
            with patch.object(app.requests, 'post', return_value=response):
                if missing:
                    self.assertEqual(app.listar_archivos('mock', '/S'), [])
                else:
                    with self.assertRaises(requests.HTTPError):
                        app.listar_archivos('mock', '/S')

    def test_paginacion(self):
        first, second = Mock(status_code=200), Mock(status_code=200)
        first.json.return_value = {'entries': [{'.tag': 'file', 'name': 'a'}], 'has_more': True, 'cursor': 'cursor'}
        second.json.return_value = {'entries': [{'.tag': 'file', 'name': 'b'}], 'has_more': False}
        with patch.object(app.requests, 'post', side_effect=[first, second]):
            self.assertEqual(len(app.listar_archivos('mock', '/S')), 2)


if __name__ == '__main__':
    unittest.main()
