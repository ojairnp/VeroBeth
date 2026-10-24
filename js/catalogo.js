async function cargarCatalogo() {
  const grid = document.getElementById('grid-productos');
  try {
    const resp = await fetch('catalogo.json', { cache: 'no-store' });
    if (!resp.ok) throw new Error("Error HTTP del catálogo");
    const productos = await resp.json();
    if (!Array.isArray(productos)) throw new Error("Formato de catálogo inválido");
    return productos;
  } catch (err) {
    grid.innerHTML = '<p class="sin-resultados">No se pudo cargar el catalogo.</p>';
    return null;
  }
}

function escaparAtributo(valor) {
  return String(valor).replaceAll('&', '&amp;').replaceAll('"', '&quot;')
    .replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll("'", '&#039;');
}

function crearTarjeta(producto) {
  const ruta = escaparAtributo(producto.imagen_url);
  const talla = escaparAtributo(producto.talla);
  const urlCompleta = new URL(producto.imagen_url, window.location.href).href;
  const mensaje = encodeURIComponent(
    'Hola, me interesa este producto (talla ' + talla + '): ' + urlCompleta
  );
  const waLink = 'https://wa.me/5219985420424?text=' + mensaje;

  const media = producto.tipo === 'video'
    ? '<video src="' + ruta + '" autoplay muted loop controls playsinline preload="metadata"></video>'
    : '<img src="' + ruta + '" alt="Vero Beth talla ' + talla + '" loading="lazy">';

  return (
    '<div class="producto-card" data-talla="' + talla + '">' +
      media +
      '<div class="producto-info">' +
        '<div class="producto-talla">Talla ' + talla + '</div>' +
        '<a class="producto-wa" href="' + waLink + '" target="_blank" rel="noopener">Preguntar disponibilidad</a>' +
      '</div>' +
    '</div>'
  );
}

function ordenarVideosPrimero(productos) {
  const videos = productos.filter(function (p) { return p.tipo === 'video'; });
  const imagenes = productos.filter(function (p) { return p.tipo === 'imagen'; });
  return videos.concat(imagenes);
}

function renderizar(productos, tallaSeleccionada) {
  const grid = document.getElementById('grid-productos');
  const filtrados = tallaSeleccionada === 'todo'
    ? productos
    : productos.filter(function (p) { return p.talla === tallaSeleccionada; });

  const ordenados = ordenarVideosPrimero(filtrados);

  if (ordenados.length === 0) {
    grid.innerHTML = '<p class="sin-resultados">No hay productos en esta talla por ahora.</p>';
    return;
  }

  grid.innerHTML = ordenados.map(crearTarjeta).join('');
}

async function init() {
  const productos = await cargarCatalogo();
  if (productos === null) return;
  const botones = document.querySelectorAll('.filtro-btn');

  const params = new URLSearchParams(window.location.search);
  const tallaSolicitada = params.get('talla');
  const tallaInicial = ['XS', 'S', 'M', 'L'].includes(tallaSolicitada) ? tallaSolicitada : 'todo';

  botones.forEach(function (btn) {
    if (btn.dataset.talla === tallaInicial) {
      botones.forEach(function (b) { b.classList.remove('activo'); });
      btn.classList.add('activo');
    }
    btn.addEventListener('click', function () {
      botones.forEach(function (b) { b.classList.remove('activo'); });
      btn.classList.add('activo');
      renderizar(productos, btn.dataset.talla);
    });
  });

  renderizar(productos, tallaInicial);
}

init();
