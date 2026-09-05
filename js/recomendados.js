const PRODUCTOS_URL = 'https://raw.githubusercontent.com/ojairnp/MercadoAfiliados/main/public/data/products.json';

function escaparHtml(valor) {
  return String(valor)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function precioFormateado(producto) {
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: producto.currency || 'MXN',
    maximumFractionDigits: 2
  }).format(producto.price);
}

function crearRecomendado(producto) {
  const titulo = escaparHtml(producto.title);
  const imagen = escaparHtml(producto.image);
  const enlace = escaparHtml(producto.affiliate_url);

  return (
    '<article class="recomendado-card">' +
      '<a class="recomendado-imagen" href="' + enlace + '" target="_blank" rel="noopener sponsored">' +
        '<img src="' + imagen + '" alt="' + titulo + ' recomendado para entrenamiento fitness" loading="lazy">' +
        '<span class="recomendado-sello">Recomendado</span>' +
      '</a>' +
      '<div class="recomendado-info">' +
        '<p class="recomendado-categoria">Equipo fitness</p>' +
        '<h3>' + titulo + '</h3>' +
        '<p class="recomendado-precio">' + precioFormateado(producto) + '</p>' +
        '<a class="recomendado-boton" href="' + enlace + '" target="_blank" rel="noopener sponsored">Ver en Mercado Libre</a>' +
      '</div>' +
    '</article>'
  );
}

function publicarDatosEstructurados(productos) {
  const datos = {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name: 'Accesorios fitness recomendados por Vero Beth',
    numberOfItems: productos.length,
    itemListElement: productos.map(function (producto, indice) {
      return {
        '@type': 'ListItem',
        position: indice + 1,
        url: producto.affiliate_url,
        item: {
          '@type': 'Product',
          name: producto.title,
          image: producto.image,
          category: 'Accesorios y equipo fitness',
          offers: {
            '@type': 'Offer',
            url: producto.affiliate_url,
            price: String(producto.price),
            priceCurrency: producto.currency || 'MXN',
            availability: 'https://schema.org/InStock',
            seller: {
              '@type': 'Organization',
              name: 'Mercado Libre'
            }
          }
        }
      };
    })
  };

  const script = document.createElement('script');
  script.id = 'productos-datos-estructurados';
  script.type = 'application/ld+json';
  script.textContent = JSON.stringify(datos);
  document.head.appendChild(script);
}

async function cargarRecomendados() {
  const grid = document.getElementById('grid-recomendados');

  try {
    const respuesta = await fetch(PRODUCTOS_URL, { cache: 'no-store' });
    if (!respuesta.ok) throw new Error('Respuesta no válida');

    const datos = await respuesta.json();
    const productos = Array.isArray(datos.products)
      ? datos.products.filter(function (producto) { return producto.available && producto.affiliate_url; })
      : [];

    if (productos.length === 0) {
      grid.innerHTML = '<p class="sin-resultados">No hay recomendaciones disponibles por ahora.</p>';
      return;
    }

    grid.innerHTML = productos.map(crearRecomendado).join('');
    publicarDatosEstructurados(productos);
  } catch (error) {
    grid.innerHTML = '<p class="sin-resultados">No se pudieron cargar los recomendados. Intenta de nuevo más tarde.</p>';
  }
}

cargarRecomendados();
