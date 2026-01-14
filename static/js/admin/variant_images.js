/**
 * Interactive Variant Image Management for GearUp Admin.
 */

document.addEventListener('DOMContentLoaded', function() {
    const VERSION = '1.2.2';
    console.log('GearUp Variant Media Manager v' + VERSION + ' initialized');

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
            console.log(`[${type}] ${message}`);
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

        if (cropper) cropper.destroy();
        
        // Treat as cross-origin if it's not a data URL
        if (!imageSrc.startsWith('data:')) {
            cropImage.crossOrigin = 'anonymous';
            if (imageSrc.includes('http') || imageSrc.includes('cloudinary')) {
                const separator = imageSrc.includes('?') ? '&' : '?';
                cropImage.src = imageSrc + separator + 'crop_ts=' + Date.now();
            } else {
                cropImage.src = imageSrc;
            }
        } else {
            cropImage.crossOrigin = null;
            cropImage.src = imageSrc;
        }

        cropModal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';

        cropper = new Cropper(cropImage, {
            aspectRatio: 1,
            viewMode: 1,
            autoCropArea: 0.8,
            checkCrossOrigin: true,
            responsive: true,
            restore: false,
            guides: true,
            center: true,
            highlight: false,
            cropBoxMovable: true,
            cropBoxResizable: true,
            toggleDragModeOnDblclick: false,
            ready() {
                console.log('Cropper ready');
            }
        });
        
        updateAspectRatio();
    }

    function updateAspectRatio() {
        if (!cropper || !aspectRatio) return;
        const ratio = aspectRatio.value;
        if (ratio === 'free') {
            cropper.setAspectRatio(NaN);
        } else {
            let finalRatio;
            if (ratio.includes('/')) {
                const parts = ratio.split('/');
                finalRatio = parseFloat(parts[0]) / parseFloat(parts[1]);
            } else {
                finalRatio = parseFloat(ratio);
            }
            cropper.setAspectRatio(finalRatio);
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
                
                if (!canvas) {
                    showSnackbar('Could not create crop. Try a different image.', 'error');
                    return;
                }

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

        // Consolidate Click Handling: Box triggers Input
        if (uploadBox && fileInput) {
            uploadBox.style.cursor = 'pointer';
            uploadBox.addEventListener('click', function(e) {
                // If the element is marked for delete, clicking it should unmark it first
                if (element.classList.contains('marked-for-delete')) {
                    const removeBtn = element.querySelector('.remove-image-btn');
                    if (removeBtn) removeBtn.click(); // Trigger the removal toggle logic
                    return;
                }

                // Only click if we didn't click an action button
                if (!e.target.closest('.action-btn')) {
                    fileInput.click();
                }
            });
        }

        if (fileInput) {
            fileInput.addEventListener('change', function() {
                if (this.files && this.files[0]) {
                    const file = this.files[0];
                    const validExtensions = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'];
                    const errorContainer = element.querySelector('.form-error-text');

                    if (!validExtensions.includes(file.type)) {
                        showSnackbar('Unsupported file type. Please upload a JPG, PNG, WEBP, or GIF image.', 'error');
                        if (errorContainer) {
                            const msgSpan = errorContainer.querySelector('.error-msg');
                            if (msgSpan) {
                                msgSpan.textContent = 'Unsupported file type.';
                            } else {
                                errorContainer.textContent = 'Unsupported file type.';
                            }
                            errorContainer.classList.remove('hidden');
                        }
                        this.value = ''; // Clear the input
                        return;
                    }

                    // Clear error if valid
                    if (errorContainer) {
                        const msgSpan = errorContainer.querySelector('.error-msg');
                        if (msgSpan) msgSpan.textContent = '';
                        errorContainer.classList.add('hidden');
                    }

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
                        if (removeBtn) {
                            removeBtn.classList.remove('hidden');
                        }
                    };
                    reader.readAsDataURL(file);
                }
            });
        }

        if (cropBtn) {
            cropBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                if (fileInput && fileInput.files && fileInput.files[0]) {
                    const reader = new FileReader();
                    reader.onload = (e) => openCropModal(e.target.result, fileInput.id);
                    reader.readAsDataURL(fileInput.files[0]);
                } else if (previewImg && previewImg.src && !previewImg.src.includes('placeholder')) {
                    openCropModal(previewImg.src, fileInput.id);
                }
            });
        }

        if (removeBtn) {
            removeBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // Detection logic: Primary vs Gallery
                const isPrimary = element.id === 'primary-upload-box' || element.querySelector('#primary-upload-box');
                
                if (isPrimary) {
                    // For Primary: Toggle "Clear" intent
                    const isMarked = element.classList.toggle('marked-for-delete');
                    
                    if (isMarked) {
                        showSnackbar('Marked cover for removal.', 'info');
                        // We still empty the input so it's not sent if intended to clear
                        // But we might want to store the old value if undoing is needed
                        // For simplicity, primary clear is usually immediate in many UIs,
                        // but here we mark it visually.
                    } else {
                        showSnackbar('Cover removal cancelled.', 'success');
                    }
                    return;
                }

                // Gallery image removal: Toggle "Marked for Delete"
                const deleteCheckbox = element.querySelector('input[type="checkbox"][name$="-DELETE"]');
                if (deleteCheckbox) {
                    const isCurrentlyMarked = element.classList.contains('marked-for-delete');
                    
                    if (!isCurrentlyMarked) {
                        // Mark it
                        element.classList.add('marked-for-delete');
                        deleteCheckbox.checked = true;
                        showSnackbar('Marked for deletion.', 'info');
                    } else {
                        // Unmark it
                        element.classList.remove('marked-for-delete');
                        deleteCheckbox.checked = false;
                        showSnackbar('Deletion cancelled.', 'success');
                    }
                } else {
                    // It's a newly added form that hasn't been saved yet
                    element.classList.add('removing');
                    setTimeout(() => element.remove(), 200);
                }
            });
        }

        // Drag and Drop
        if (uploadBox && fileInput) {
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                uploadBox.addEventListener(eventName, e => {
                    e.preventDefault();
                    e.stopPropagation();
                }, false);
            });

            uploadBox.addEventListener('dragenter', () => uploadBox.classList.add('drag-over'), false);
            uploadBox.addEventListener('dragover', () => uploadBox.classList.add('drag-over'), false);
            uploadBox.addEventListener('dragleave', () => uploadBox.classList.remove('drag-over'), false);
            uploadBox.addEventListener('drop', function(e) {
                uploadBox.classList.remove('drag-over');
                const dt = e.dataTransfer;
                if (dt.files && dt.files.length) {
                    const file = dt.files[0];
                    const validExtensions = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'];
                    const errorContainer = element.querySelector('.form-error-text');

                    if (!validExtensions.includes(file.type)) {
                        showSnackbar('Unsupported file type. Please upload a JPG, PNG, WEBP, or GIF image.', 'error');
                        if (errorContainer) {
                            const msgSpan = errorContainer.querySelector('.error-msg');
                            if (msgSpan) {
                                msgSpan.textContent = 'Unsupported file type.';
                            } else {
                                errorContainer.textContent = 'Unsupported file type.';
                            }
                            errorContainer.classList.remove('hidden');
                        }
                        return;
                    }

                    // Clear error if valid
                    if (errorContainer) {
                        const msgSpan = errorContainer.querySelector('.error-msg');
                        if (msgSpan) msgSpan.textContent = '';
                        errorContainer.classList.add('hidden');
                    }

                    fileInput.files = dt.files;
                    const event = new Event('change', { bubbles: true });
                    fileInput.dispatchEvent(event);
                }
            });
        }
    }

    // Initialize
    document.querySelectorAll('.image-interaction-wrapper').forEach(wrapper => {
        initImageInteraction(wrapper);
    });
});
