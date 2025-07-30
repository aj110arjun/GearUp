let cropper;
const imageInput = document.getElementById('id_image');
const previewImage = document.getElementById('preview-image');

imageInput.addEventListener('change', function () {
  const file = this.files[0];
  if (!file) return;

  const url = URL.createObjectURL(file);
  previewImage.src = url;
  previewImage.style.display = 'block';

  if (cropper) cropper.destroy();

  cropper = new Cropper(previewImage, {
    aspectRatio: 1, // Change as needed (e.g. 4/3, 16/9)
    viewMode: 1,
  });
});

document.querySelector('form').addEventListener('submit', function (e) {
  e.preventDefault(); // prevent normal submit

  if (cropper) {
    cropper.getCroppedCanvas().toBlob(function (blob) {
      const form = e.target;
      const formData = new FormData(form);

      formData.set('image', blob, 'cropped.png');  // Replace the original image

      fetch(form.action, {
        method: 'POST',
        body: formData,
      })
      .then(res => {
        if (res.redirected) {
          window.location.href = res.url;
        } else {
          return res.text().then(html => {
            document.open();
            document.write(html);
            document.close();
          });
        }
      });
    });
  } else {
    this.submit();  // fallback if cropper not initialized
  }
});
