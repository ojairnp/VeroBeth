async function cargarCatalogo() {
  const grid = document.getElementById('grid-productos');
  try {
    const resp = await fetch('/catalogo.json');
    const productos = await resp.json();
    return productos;
  } catch (err) {
    grid.innerHTML = '<p class="sin-resultados">No se pudo cargar el catalogo.</p>';
    return [];
  }
}

function crearTarjeta(producto) {
  const mensaje = encodeURIComponent(
    'Hola, me interesa: ' + producto.nombre + ' talla ' + producto.talla
  );
  const waLink = 'https://wa.me/5219985420424?text=' + mensaje;

  const media = producto.tipo === 'video'
    ? '<video src="' + producto.imagen_url + '" muted loop autoplay playsinline></video>'
    : '<img src="' + producto.imagen_url + '" alt="' + producto.nombre + '" loading="lazy">';

  return (
    '<div class="producto-card" data-talla="' + producto.talla + '">' +
      media +
      '<div class="producto-info">' +
        '<div class="producto-nombre">' + producto.nombre + '</div>' +
        '<div class="producto-talla">Talla ' + producto.talla + '</div>' +
        '<a class="producto-wa" href="' + waLink + '" target="_blank" rel="noopener">Preguntar disponibilidad</a>' +
      '</div>' +
    '</div>'
  );
}

function renderizar(productos, tallaSeleccionada) {
  const grid = document.getElementById('grid-productos');
  const filtrados = tallaSeleccionada === 'todo'
    ? productos
    : productos.filter(function (p) { return p.talla === tallaSeleccionada; });

  if (filtrados.length === 0) {
    grid.innerHTML = '<p class="sin-resultados">No hay productos en esta talla por ahora.</p>';
    return;
  }

  grid.innerHTML = filtrados.map(crearTarjeta).join('');
}

async function init() {
  const productos = await cargarCatalogo();
  const botones = document.querySelectorAll('.filtro-btn');

  const params = new URLSearchParams(window.location.search);
  const tallaInicial = params.get('talla') || 'todo';

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
