/**
 * Interactive Variant Image Management for GearUp Admin.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Cropper.js variables
    let cropper = null;
    let currentImageInputId = null;
    let originalImageBlob = null;
    
    // Selectors
    const cropModal = document.getElementById('crop-modal');
    const cropImage = document.getElementById('crop-image');
    const aspectRatio = document.getElementById('aspect-ratio');
    const zoomSlider = document.getElementById('zoom-slider');
    const cancelCrop = document.getElementById('cancel-crop');
    const applyCrop = document.getElementById('apply-crop');
    const closeCropModalBtn = document.getElementById('close-crop-modal');

    // --- Helper Functions ---
    
    function showSnackbar(message, type = 'info') {
        if (window.showSnackbar) {
            window.showSnackbar(message, type);
        } else {
            alert(message);
        }
    }

    // --- Image Preview Handler ---
    
    function handleImagePreview(input, previewId, containerId) {
        if (input.files && input.files[0]) {
            const file = input.files[0];
            const reader = new FileReader();
            
            reader.onload = function(e) {
                const preview = document.getElementById(previewId);
                const container = document.getElementById(containerId);
                
                if (preview) {
                    preview.src = e.target.result;
                    preview.classList.remove('hidden');
                }
                
                if (container) {
                    container.classList.remove('no-image');
                    container.classList.add('has-image');
                }

                // Show crop button if it exists
                const cropBtn = input.closest('.image-upload-wrapper').querySelector('.crop-btn');
                if (cropBtn) cropBtn.classList.remove('hidden');
            };
            
            reader.readAsDataURL(file);
        }
    }

    // --- Cropping Logic ---

    function openCropModal(imageSrc, inputId) {
        if (!cropImage || !cropModal) return;
        
        currentImageInputId = inputId;
        const input = document.getElementById(inputId);
        if (input && input.files && input.files[0]) {
            originalImageBlob = input.files[0];
        }

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
            cropper.setAspectRatio(parseFloat(eval(ratio)));
        }
    }

    function closeCropModal() {
        if (cropModal) cropModal.classList.add('hidden');
        document.body.style.overflow = 'auto';
        if (cropper) {
            cropper.destroy();
            cropper = null;
        }
    }

    if (aspectRatio) aspectRatio.addEventListener('change', updateAspectRatio);
    if (zoomSlider) {
        zoomSlider.addEventListener('input', function() {
            if (cropper) cropper.zoomTo(parseFloat(this.value));
        });
    }
    
    if (cancelCrop) cancelCrop.addEventListener('click', closeCropModal);
    if (closeCropModalBtn) closeCropModalBtn.addEventListener('click', closeCropModal);
    
    if (applyCrop) {
        applyCrop.addEventListener('click', function() {
            if (cropper) {
                const canvas = cropper.getCroppedCanvas({
                    width: 1200,
                    height: 1200,
                    imageSmoothingEnabled: true,
                    imageSmoothingQuality: 'high',
                });
                
                canvas.toBlob(function(blob) {
                    if (!blob) {
                        showSnackbar('Failed to crop image.', 'error');
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
                            
                            // Trigger change to update preview
                            const event = new Event('change', { bubbles: true });
                            imageInput.dispatchEvent(event);
                        }
                        showSnackbar('Image cropped successfully!', 'success');
                    }
                    closeCropModal();
                }, 'image/jpeg', 0.95);
            }
        });
    }

    // --- Dynamic Formset Handling ---

    const addImageBtn = document.getElementById('add-image-formset-btn');
    const formsetContainer = document.getElementById('image-formset-container');
    const totalForms = document.getElementById('id_additional_images-TOTAL_FORMS') || document.getElementById('id_images-TOTAL_FORMS');
    const emptyFormTemplate = document.getElementById('empty-form-template');

    if (addImageBtn && formsetContainer && totalForms && emptyFormTemplate) {
        addImageBtn.addEventListener('click', function() {
            const count = parseInt(totalForms.value);
            let newFormHtml = emptyFormTemplate.innerHTML.replace(/__prefix__/g, count);
            
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = newFormHtml;
            const newForm = tempDiv.firstElementChild;
            
            formsetContainer.appendChild(newForm);
            totalForms.value = count + 1;
            
            initImageInteraction(newForm);
        });
    }

    function initImageInteraction(element) {
        const fileInput = element.querySelector('input[type="file"]');
        const previewImg = element.querySelector('.preview-image-el');
        const cropBtn = element.querySelector('.crop-btn');
        const removeBtn = element.querySelector('.remove-image-btn');
        const uploadBox = element.querySelector('.upload-box');

        if (fileInput) {
            fileInput.addEventListener('change', function() {
                if (this.files && this.files[0]) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        if (previewImg) {
                            previewImg.src = e.target.result;
                            previewImg.classList.remove('hidden');
                        }
                        if (uploadBox) {
                            uploadBox.classList.add('has-image');
                        }
                        if (cropBtn) {
                            cropBtn.classList.remove('hidden');
                        }
                    };
                    reader.readAsDataURL(this.files[0]);
                }
            });
        }

        if (cropBtn) {
            cropBtn.addEventListener('click', function(e) {
                e.preventDefault();
                if (fileInput && fileInput.files && fileInput.files[0]) {
                    const reader = new FileReader();
                    reader.onload = (e) => openCropModal(e.target.result, fileInput.id);
                    reader.readAsDataURL(fileInput.files[0]);
                } else if (previewImg && previewImg.src && !previewImg.src.includes('placeholder')) {
                    // Handle existing images if needed (might need different logic for cross-origin)
                    openCropModal(previewImg.src, fileInput.id);
                }
            });
        }

        if (removeBtn) {
            removeBtn.addEventListener('click', function(e) {
                e.preventDefault();
                const deleteCheckbox = element.querySelector('input[type="checkbox"][name$="-DELETE"]');
                if (deleteCheckbox) {
                    deleteCheckbox.checked = true;
                    element.classList.add('hidden');
                    showSnackbar('Image removed.', 'info');
                } else {
                    element.remove();
                    // Update total forms? Usually not strictly necessary for simple remove before save
                }
            });
        }

        // Drag and Drop
        if (uploadBox && fileInput) {
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                uploadBox.addEventListener(eventName, preventDefaults, false);
            });

            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }

            ['dragenter', 'dragover'].forEach(eventName => {
                uploadBox.addEventListener(eventName, () => uploadBox.classList.add('drag-over'), false);
            });

            ['dragleave', 'drop'].forEach(eventName => {
                uploadBox.addEventListener(eventName, () => uploadBox.classList.remove('drag-over'), false);
            });

            uploadBox.addEventListener('drop', function(e) {
                const dt = e.dataTransfer;
                const files = dt.files;
                fileInput.files = files;
                
                const event = new Event('change', { bubbles: true });
                fileInput.dispatchEvent(event);
            });
        }
    }

    // Initialize existing interactions
    document.querySelectorAll('.image-interaction-wrapper').forEach(wrapper => {
        initImageInteraction(wrapper);
    });
});
