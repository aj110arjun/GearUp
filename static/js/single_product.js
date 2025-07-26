// Zoom Feature Script

const mainImage = document.getElementById('mainProductImage');
const zoomLens = document.getElementById('zoomLens');
const zoomResult = document.getElementById('zoomResult');
const thumbnails = document.querySelectorAll('.thumb');

if (mainImage && zoomLens && zoomResult) {
  let cx, cy;

  // Update the zoom background and highlight active thumbnail
  function switchMainImage(el) {
    const newSrc = el.src;
    mainImage.src = newSrc;
    zoomResult.style.backgroundImage = `url('${newSrc}')`;

    thumbnails.forEach(img => img.classList.remove('active-thumb'));
    el.classList.add('active-thumb');
  }

  // Calculate cursor position relative to main image
  function getCursorPosition(e) {
    const bounds = mainImage.getBoundingClientRect();
    const x = e.pageX - bounds.left - window.scrollX;
    const y = e.pageY - bounds.top - window.scrollY;
    return { x, y };
  }

  // Move the lens and update the zoomed view
  function moveLens(e) {
    const pos = getCursorPosition(e);
    let x = pos.x - zoomLens.offsetWidth / 2;
    let y = pos.y - zoomLens.offsetHeight / 2;

    // Clamp within image boundaries
    const maxX = mainImage.width - zoomLens.offsetWidth;
    const maxY = mainImage.height - zoomLens.offsetHeight;
    x = Math.max(0, Math.min(x, maxX));
    y = Math.max(0, Math.min(y, maxY));

    // Position lens
    zoomLens.style.left = `${x}px`;
    zoomLens.style.top = `${y}px`;

    // Zoom ratio
    cx = zoomResult.offsetWidth / zoomLens.offsetWidth;
    cy = zoomResult.offsetHeight / zoomLens.offsetHeight;

    zoomResult.style.backgroundPosition = `-${x * cx}px -${y * cy}px`;
  }

  // Show zoom elements and initialize background
  mainImage.addEventListener('mouseenter', () => {
    zoomLens.style.display = 'block';
    zoomResult.style.display = 'block';
    zoomResult.style.backgroundImage = `url('${mainImage.src}')`;
  });

  // Hide zoom elements
  mainImage.addEventListener('mouseleave', () => {
    zoomLens.style.display = 'none';
    zoomResult.style.display = 'none';
  });

  // Move lens on cursor movement
  mainImage.addEventListener('mousemove', moveLens);

  // Setup thumbnail click switching
  thumbnails.forEach(thumb => {
    thumb.addEventListener('click', () => switchMainImage(thumb));
  });
}
