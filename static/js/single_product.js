const mainImage = document.getElementById('mainProductImage');
const zoomLens = document.getElementById('zoomLens');
const zoomResult = document.getElementById('zoomResult');

function getCursorPos(e) {
  const rect = mainImage.getBoundingClientRect();
  const x = e.pageX - rect.left - window.pageXOffset;
  const y = e.pageY - rect.top - window.pageYOffset;
  return { x, y };
}

function moveLens(e) {
  e.preventDefault();
  zoomLens.style.display = 'block';
  zoomResult.style.display = 'block';
  const pos = getCursorPos(e);
  let x = pos.x - zoomLens.offsetWidth / 2;
  let y = pos.y - zoomLens.offsetHeight / 2;

  const maxX = mainImage.width - zoomLens.offsetWidth;
  const maxY = mainImage.height - zoomLens.offsetHeight;

  x = Math.max(0, Math.min(x, maxX));
  y = Math.max(0, Math.min(y, maxY));

  zoomLens.style.left = x + "px";
  zoomLens.style.top = y + "px";

  const cx = zoomResult.offsetWidth / zoomLens.offsetWidth;
  const cy = zoomResult.offsetHeight / zoomLens.offsetHeight;

  zoomResult.style.backgroundImage = `url('${mainImage.src}')`;
  zoomResult.style.backgroundSize = `${mainImage.width * cx}px ${mainImage.height * cy}px`;
  zoomResult.style.backgroundPosition = `-${x * cx}px -${y * cy}px`;
}

function switchMainImage(el) {
  mainImage.src = el.src;
  zoomResult.style.backgroundImage = `url('${el.src}')`;
  document.querySelectorAll('.thumb').forEach(img => img.classList.remove('active-thumb'));
  el.classList.add('active-thumb');
}

// Events
mainImage.addEventListener("mousemove", moveLens);
zoomLens.addEventListener("mousemove", moveLens);
mainImage.addEventListener("mouseenter", () => {
  zoomLens.style.display = "block";
  zoomResult.style.display = "block";
});
mainImage.addEventListener("mouseleave", () => {
  zoomLens.style.display = "none";
  zoomResult.style.display = "none";
});
