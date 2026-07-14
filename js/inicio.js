async function cargarHero() {
  const contenedor = document.getElementById('hero-media');
  try {
    const resp = await fetch('/catalogo.json');
    const productos = await resp.json();
    const soloImagenes = productos.filter(function (p) { return p.tipo === 'imagen'; });

    if (soloImagenes.length === 0) {
      return;
    }

    const elegido = soloImagenes[Math.floor(Math.random() * soloImagenes.length)];
    const img = document.createElement('img');
    img.src = elegido.imagen_url;
    img.alt = 'Vero Beth';
    img.className = 'hero-img';
    contenedor.innerHTML = '';
    contenedor.appendChild(img);
  } catch (err) {
    console.log('No se pudo cargar el catalogo para el hero');
  }
}

cargarHero();
