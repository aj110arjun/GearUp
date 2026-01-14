/**
 * User Profile Functionality
 * Includes image cropping, social media links, and form validation
 */

document.addEventListener('DOMContentLoaded', function() {
    // --- Date of Birth formatting ---
    const displayInput = document.getElementById('id_date_of_birth_display');
    const hiddenInput = document.getElementById('id_date_of_birth');
    
    if (displayInput && hiddenInput) {
        // Convert existing value from YYYY-MM-DD to DD/MM/YYYY
        if (hiddenInput.value) {
            const parts = hiddenInput.value.split('-');
            if (parts.length === 3) {
                displayInput.value = parts[2] + '/' + parts[1] + '/' + parts[0];
            }
        }
        
        // Auto-format as user types
        displayInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, ''); // Remove non-digits
            
            if (value.length > 8) value = value.slice(0, 8);
            
            // Add slashes automatically
            if (value.length >= 4) {
                value = value.slice(0, 2) + '/' + value.slice(2, 4) + '/' + value.slice(4);
            } else if (value.length >= 2) {
                value = value.slice(0, 2) + '/' + value.slice(2);
            }
            
            e.target.value = value;
            
            // Update hidden field in YYYY-MM-DD format
            if (value.length === 10) {
                const parts = value.split('/');
                const day = parts[0];
                const month = parts[1];
                const year = parts[2];
                hiddenInput.value = year + '-' + month + '-' + day;
            } else {
                hiddenInput.value = '';
            }
        });
    }

    // --- Social Media Links Initialization ---
    updateSocialLink('twitter', document.getElementById('id_twitter')?.value || '');
    updateSocialLink('instagram', document.getElementById('id_instagram')?.value || '');
    updateSocialLink('facebook', document.getElementById('id_facebook')?.value || '');
    updateSocialLink('linkedin', document.getElementById('id_linkedin')?.value || '');

    // --- Form validation ---
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', function(e) {
            const firstNameInput = document.getElementById('id_first_name');
            const lastNameInput = document.getElementById('id_last_name');
            const phoneInput = document.getElementById('id_phone_number');
            const locationInput = document.getElementById('id_location');
            
            const firstNameError = document.getElementById('first_name_error');
            const lastNameError = document.getElementById('last_name_error');
            const phoneError = document.getElementById('phone_number_error');
            const locationError = document.getElementById('location_error');
            const imageError = document.getElementById('profile_image_error');

            // Clear previous errors
            [firstNameError, lastNameError, phoneError, locationError, imageError].forEach(err => err?.classList.remove('show'));
            [firstNameInput, lastNameInput, phoneInput, locationInput].forEach(inp => inp?.classList.remove('error-border'));
            document.querySelectorAll('[id$="_backend_error"]').forEach(err => err.classList.remove('show'));
            
            let isValid = true;

            // First Name validation
            const firstNameValue = firstNameInput.value.trim();
            if (!firstNameValue) {
                firstNameError.querySelector('.error-msg').textContent = 'First name is required.';
                firstNameError.classList.add('show');
                isValid = false;
            } else if (!/^[a-zA-Z0-9\s]+$/.test(firstNameValue)) {
                firstNameError.querySelector('.error-msg').textContent = 'First name should only contain letters, numbers, and spaces.';
                firstNameError.classList.add('show');
                isValid = false;
            }

            // Last Name validation
            const lastNameValue = lastNameInput.value.trim();
            if (!lastNameValue) {
                lastNameError.querySelector('.error-msg').textContent = 'Last name is required.';
                lastNameError.classList.add('show');
                isValid = false;
            } else if (!/^[a-zA-Z0-9\s]+$/.test(lastNameValue)) {
                lastNameError.querySelector('.error-msg').textContent = 'Last name should only contain letters, numbers, and spaces.';
                lastNameError.classList.add('show');
                isValid = false;
            }

            // Phone validation (Optional)
            const phoneValue = phoneInput.value.trim();
            if (phoneValue && !/^[6-9]\d{9}$/.test(phoneValue)) {
                phoneError.querySelector('.error-msg').textContent = 'Phone number must be 10 digits starting with 6, 7, 8, or 9.';
                phoneError.classList.add('show');
                isValid = false;
            }
            
            // Location validation (Optional)
            const locationValue = locationInput.value.trim();
            if (locationValue) {
                if (locationValue.length < 3) {
                    locationError.querySelector('.error-msg').textContent = 'Location must be at least 3 characters long.';
                    locationError.classList.add('show');
                    isValid = false;
                } else if (!/^[a-zA-Z0-9\s,.-]+$/.test(locationValue)) {
                    locationError.querySelector('.error-msg').textContent = 'Location contains invalid characters.';
                    locationError.classList.add('show');
                    isValid = false;
                }
            }
            
            if (!isValid) {
                e.preventDefault();
                // Scroll to the first error
                const firstError = document.querySelector('.form-error-text.show');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                return;
            }

            const submitButton = document.getElementById('submitButton');
            submitButton.disabled = true;
            submitButton.innerHTML = `
                <i class="fas fa-spinner fa-spin"></i>
                <span>Saving Changes...</span>
            `;
        });
    }

    // Clear errors when user starts interacting
    ['id_first_name', 'id_last_name', 'id_phone_number', 'id_location'].forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            ['input', 'change', 'blur'].forEach(eventType => {
                input.addEventListener(eventType, function() {
                    const baseId = id.replace('id_', '');
                    const errorDiv = document.getElementById(baseId + '_error');
                    const backendErrorDiv = document.getElementById(baseId + '_backend_error');
                    if (errorDiv) errorDiv.classList.remove('show');
                    if (backendErrorDiv) backendErrorDiv.classList.remove('show');
                });
            });
        }
    });

    // Final safety: Remove any residual error states on full page load
    document.querySelectorAll('.form-error-text').forEach(err => {
        if (!err.id.includes('backend')) {
            err.classList.remove('show');
        }
    });
});

// --- GLOBAL FUNCTIONS ---

// Cropper.js variables
let cropper = null;
let currentImageInput = null;

// Image cropping elements
const cropModal = document.getElementById('crop-modal');
const cropImage = document.getElementById('crop-image');
const aspectRatio = document.getElementById('aspect-ratio');
const zoomSlider = document.getElementById('zoom-slider');
const cancelCrop = document.getElementById('cancel-crop');
const applyCrop = document.getElementById('apply-crop');

// Handle image upload and open crop modal
function handleImageUpload(input) {
    const imageError = document.getElementById('profile_image_error');
    const backendImageError = document.getElementById('profile_image_backend_error');
    
    if (imageError) imageError.classList.remove('show');
    if (backendImageError) backendImageError.classList.remove('show');

    if (input.files && input.files[0]) {
        const file = input.files[0];
        const validExtensions = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'];
        
        if (!validExtensions.includes(file.type)) {
            if (imageError) {
                imageError.querySelector('.error-msg').textContent = 'Unsupported file type. Please upload a JPG, PNG, WEBP, or GIF image.';
                imageError.classList.add('show');
            }
            input.value = ''; // Clear the input
            return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            currentImageInput = input;
            openCropModal(e.target.result);
        }
        reader.readAsDataURL(file);
    }
}

// Open crop modal for existing images
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('crop-existing-image') || 
        e.target.closest('.crop-existing-image')) {
        const button = e.target.classList.contains('crop-existing-image') ? 
                       e.target : e.target.closest('.crop-existing-image');
        const imageUrl = button.getAttribute('data-image-url');
        openCropModal(imageUrl);
    }
});

// Open crop modal function
function openCropModal(imageSrc) {
    if (!cropImage || !cropModal) return;
    
    cropImage.src = imageSrc;
    cropModal.classList.remove('hidden');
    
    if (cropper) {
        cropper.destroy();
    }
    
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

// Update aspect ratio
aspectRatio?.addEventListener('change', updateAspectRatio);

function updateAspectRatio() {
    if (!cropper || !aspectRatio) return;
    const ratio = aspectRatio.value;
    if (ratio === 'free') {
        cropper.setAspectRatio(NaN);
    } else {
        cropper.setAspectRatio(eval(ratio));
    }
}

// Zoom functionality
zoomSlider?.addEventListener('input', function() {
    cropper?.zoomTo(parseFloat(this.value));
});

// Cancel crop
cancelCrop?.addEventListener('click', function() {
    cropModal?.classList.add('hidden');
    if (cropper) {
        cropper.destroy();
        cropper = null;
    }
});

// Apply crop
applyCrop?.addEventListener('click', function() {
    if (cropper) {
        const canvas = cropper.getCroppedCanvas({
            width: 300,
            height: 300,
        });
        
        canvas.toBlob(function(blob) {
            const file = new File([blob], 'profile-image.jpg', { type: 'image/jpeg' });
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            
            if (currentImageInput) {
                currentImageInput.files = dataTransfer.files;
                updateProfilePreview(URL.createObjectURL(file));
            }
            
            cropModal.classList.add('hidden');
            cropper.destroy();
            cropper = null;
        }, 'image/jpeg', 0.9);
    }
});

// Update profile preview function
function updateProfilePreview(imageSrc) {
    const preview = document.getElementById('profile-preview');
    const defaultPreview = document.getElementById('profile-preview-default');
    const sidebarImage = document.getElementById('sidebar-profile-image');
    const sidebarDefault = document.getElementById('sidebar-default-image');
    
    if (defaultPreview) defaultPreview.classList.add('hidden');
    if (preview) {
        preview.src = imageSrc;
        preview.classList.remove('hidden');
    }
    
    if (sidebarImage) {
        sidebarImage.src = imageSrc;
    } else if (sidebarDefault) {
        const newSidebarImage = document.createElement('img');
        newSidebarImage.id = 'sidebar-profile-image';
        newSidebarImage.src = imageSrc;
        newSidebarImage.alt = 'Profile Picture';
        newSidebarImage.className = 'w-28 h-28 rounded-2xl object-cover border-4 border-emerald-100 shadow-2xl';
        sidebarDefault.parentNode.replaceChild(newSidebarImage, sidebarDefault);
    }
}

function removeProfilePicture() {
    window.showConfirmModal({
        title: 'Remove Profile Picture?',
        message: 'Are you sure you want to remove your profile picture?',
        confirmText: 'Remove',
        cancelText: 'Cancel',
        variant: 'danger',
        onConfirm: () => {
            const removeInput = document.createElement('input');
            removeInput.type = 'hidden';
            removeInput.name = 'remove_profile_image';
            removeInput.value = 'true';
            
            const form = document.getElementById('profileForm');
            if (form) {
                form.appendChild(removeInput);
                form.submit();
            }
        }
    });
}

// Social Media Link Functions
function updateSocialLink(platform, username) {
    const socialPreview = document.getElementById('socialPreview');
    const socialLinksContainer = document.getElementById('socialLinksContainer');
    
    if (!socialLinksContainer) return;
    
    socialLinksContainer.innerHTML = '';
    const socialInputs = ['twitter', 'instagram', 'facebook', 'linkedin'];
    let hasContent = false;
    
    socialInputs.forEach(plat => {
        const input = document.getElementById(`id_${plat}`);
        if (input) {
            const uName = input.value.trim();
            if (uName) {
                hasContent = true;
                socialLinksContainer.appendChild(createSocialLinkElement(plat, uName));
            }
        }
    });
    
    if (hasContent) {
        socialPreview?.classList.remove('hidden');
    } else {
        socialPreview?.classList.add('hidden');
    }
    
    updateSocialIcon(platform, username);
}

function updateSocialIcon(platform, username) {
    const iconContainer = document.querySelector(`#id_${platform} ~ .social-link`);
    if (iconContainer) {
        iconContainer.style.display = username.trim() ? 'block' : 'none';
    }
}

function openSocialLink(platform, username) {
    if (!username.trim()) return;
    
    let url = '';
    const cleanUsername = username.trim().replace('@', '').replace('https://', '').replace('http://', '');
    
    switch(platform) {
        case 'twitter': url = `https://twitter.com/${cleanUsername}`; break;
        case 'instagram': url = `https://instagram.com/${cleanUsername}`; break;
        case 'facebook': url = `https://facebook.com/${cleanUsername}`; break;
        case 'linkedin': 
            url = cleanUsername.includes('linkedin.com') ? `https://${cleanUsername}` : `https://linkedin.com/in/${cleanUsername}`;
            break;
    }
    
    if (url) window.open(url, '_blank');
}

function createSocialLinkElement(platform, username) {
    const linkDiv = document.createElement('div');
    linkDiv.className = 'flex items-center space-x-2 px-3 py-2 bg-gray-100 rounded-lg social-link';
    linkDiv.onclick = () => openSocialLink(platform, username);
    
    const icons = {
        'twitter': 'fab fa-twitter text-blue-400',
        'instagram': 'fab fa-instagram text-pink-500',
        'facebook': 'fab fa-facebook text-blue-600',
        'linkedin': 'fab fa-linkedin text-blue-700'
    };
    
    const platformNames = {
        'twitter': 'Twitter',
        'instagram': 'Instagram',
        'facebook': 'Facebook',
        'linkedin': 'LinkedIn'
    };
    
    linkDiv.innerHTML = `
        <i class="${icons[platform]}"></i>
        <span class="text-sm font-medium text-gray-700">${platformNames[platform]}</span>
        <span class="text-xs text-gray-500">${username}</span>
    `;
    
    return linkDiv;
}
