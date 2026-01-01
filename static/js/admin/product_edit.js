/**
 * Product Edit logic for GearUp Admin.
 */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('product-form');
    const submitBtn = document.getElementById('submit-btn');
    const submitText = document.getElementById('submit-text');
    
    // Cropper.js variables
    let cropper = null;
    let currentImageInputId = null;
    let originalImageBlob = null;
    
    // Handle form submission
    if (form) {
      form.addEventListener('submit', function() {
        if (submitBtn) submitBtn.disabled = true;
        if (submitText) submitText.textContent = 'Updating...';
      });
    }
    
    // Dynamic formset handling for images
    const addImageBtn = document.getElementById('add-image-btn');
    const imageTableBody = document.getElementById('image-table-body');
    const totalImageForms = document.querySelector('#id_images-TOTAL_FORMS');
    const emptyFormTemplate = document.getElementById('image-empty-form');
  
    if (addImageBtn && imageTableBody && totalImageForms && emptyFormTemplate) {
      addImageBtn.addEventListener('click', function() {
        const formCount = parseInt(totalImageForms.value);
        let newRowHtml = emptyFormTemplate.innerHTML;
        newRowHtml = newRowHtml.replace(/__prefix__/g, formCount);
        
        const tempTable = document.createElement('table'); 
        tempTable.innerHTML = `<tbody>${newRowHtml}</tbody>`;
        const newRowNode = tempTable.querySelector('tr');
  
        if (newRowNode) {
          imageTableBody.appendChild(newRowNode);
          totalImageForms.value = formCount + 1;
          initImageRow(newRowNode);
          newRowNode.classList.add('bg-indigo-50/50', 'highlight-new');
          setTimeout(() => {
            newRowNode.classList.remove('bg-indigo-50/50');
          }, 1000);
        }
      });
    }
  
    // Initialize existing rows
    document.querySelectorAll('.image-form-row').forEach(row => {
      initImageRow(row);
    });
  
    function initImageRow(row) {
      const imageInput = row.querySelector('input[type="file"]');
      const previewImg = row.querySelector('.preview-img');
      const noImageText = row.querySelector('.no-image-text');
      const cropBtn = row.querySelector('.crop-new-image'); 
      
      if (imageInput) {
        if (cropBtn && !cropBtn.getAttribute('data-input-id')) {
           cropBtn.setAttribute('data-input-id', imageInput.id);
        }
  
        imageInput.addEventListener('change', function(e) {
          if (this.files && this.files[0]) {
            const file = this.files[0];
            const reader = new FileReader();
            reader.onload = function(e) {
              if (previewImg) {
                previewImg.src = e.target.result;
                previewImg.classList.remove('hidden');
                previewImg.style.display = 'block'; 
              }
              if (noImageText) noImageText.classList.add('hidden');
              if (cropBtn) cropBtn.classList.remove('hidden');
            }
            reader.readAsDataURL(file);
          }
        });
      }
  
      const deleteBtn = row.querySelector('.delete-image-row');
      if (deleteBtn) {
        deleteBtn.addEventListener('click', function() {
          const deleteCheckbox = row.querySelector('input[type="checkbox"][name$="-DELETE"]');
          if (deleteCheckbox) {
            deleteCheckbox.checked = true;
            row.style.display = 'none';
            if (window.showSnackbar) {
                window.showSnackbar('Image marked for removal.', 'info');
            }
          } else {
             row.style.display = 'none';
          }
        });
      }
    }
    
    // Image cropping functionality
    const cropModal = document.getElementById('crop-modal');
    const cropImage = document.getElementById('crop-image');
    const aspectRatio = document.getElementById('aspect-ratio');
    const zoomSlider = document.getElementById('zoom-slider');
    const cancelCrop = document.getElementById('cancel-crop');
    const applyCrop = document.getElementById('apply-crop');
    const closeCropModalBtn = document.getElementById('close-crop-modal');
    
    // Open crop modal for new images
    document.addEventListener('click', function(e) {
      const cropNewBtn = e.target.closest('.crop-new-image');
      if (cropNewBtn) {
        const inputId = cropNewBtn.getAttribute('data-input-id');
        const imageInput = document.getElementById(inputId);
        if (imageInput && imageInput.files && imageInput.files[0]) {
          currentImageInputId = inputId;
          originalImageBlob = imageInput.files[0];
          const reader = new FileReader();
          reader.onload = (e) => openCropModal(e.target.result);
          reader.readAsDataURL(imageInput.files[0]);
        } else {
          alert('Please select an image first.');
        }
      }
      
      const cropExistBtn = e.target.closest('.crop-existing-image');
      if (cropExistBtn) {
        const imageUrl = cropExistBtn.getAttribute('data-image-url');
        currentImageInputId = null;
        openCropModal(imageUrl);
      }
    });
    
    function openCropModal(imageSrc) {
      if (!cropImage || !cropModal) return;
      cropImage.src = imageSrc;
      cropModal.classList.remove('hidden');
      document.body.style.overflow = 'hidden';
      
      if (cropper) cropper.destroy();
      
      cropper = new Cropper(cropImage, {
        aspectRatio: 1,
        viewMode: 1,
        autoCropArea: 0.8,
        responsive: true,
        restore: false,
        guides: true,
        center: true,
        highlight: false,
        cropBoxMovable: true,
        cropBoxResizable: true,
        toggleDragModeOnDblclick: false,
      });
      
      updateAspectRatio();
    }
    
    function updateAspectRatio() {
      if (!cropper || !aspectRatio) return;
      const ratio = aspectRatio.value;
      if (ratio === 'free') {
        cropper.setAspectRatio(NaN);
      } else {
        cropper.setAspectRatio(eval(ratio));
      }
    }
    
    if (aspectRatio) aspectRatio.addEventListener('change', updateAspectRatio);
    if (zoomSlider) zoomSlider.addEventListener('input', function() {
        if (cropper) cropper.zoomTo(parseFloat(this.value));
    });
    
    function closeCropModal() {
      if (cropModal) cropModal.classList.add('hidden');
      document.body.style.overflow = 'auto';
      if (cropper) {
        cropper.destroy();
        cropper = null;
      }
    }
  
    if (cancelCrop) cancelCrop.addEventListener('click', closeCropModal);
    if (closeCropModalBtn) closeCropModalBtn.addEventListener('click', closeCropModal);
    
    if (applyCrop) applyCrop.addEventListener('click', function() {
      if (cropper) {
        const canvas = cropper.getCroppedCanvas({
          width: 1200,
          height: 1200,
          imageSmoothingEnabled: true,
          imageSmoothingQuality: 'high',
        });
        
        canvas.toBlob(function(blob) {
          if (!blob) {
            alert('Failed to crop image.');
            return;
          }
          
          const fileName = originalImageBlob ? originalImageBlob.name : 'cropped-image.jpg';
          const file = new File([blob], fileName, { type: 'image/jpeg', lastModified: Date.now() });
          
          if (currentImageInputId) {
            const imageInput = document.getElementById(currentImageInputId);
            if (imageInput) {
              const dataTransfer = new DataTransfer();
              dataTransfer.items.add(file);
              imageInput.files = dataTransfer.files;
              
              const event = new Event('change', { bubbles: true });
              imageInput.dispatchEvent(event);
            }
            if (window.showSnackbar) window.showSnackbar('Image cropped successfully!', 'success');
          } else {
            if (window.showSnackbar) window.showSnackbar('Download the cropped image and re-upload.', 'info');
          }
          closeCropModal();
        }, 'image/jpeg', 0.95);
      }
    });
  
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && cropModal && !cropModal.classList.contains('hidden')) closeCropModal();
    });
    
    if (cropModal) {
        cropModal.addEventListener('click', (e) => {
            if (e.target === cropModal) closeCropModal();
        });
    }
});
