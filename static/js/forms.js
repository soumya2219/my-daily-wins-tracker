// Entry Form JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Auto-resize textareas
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
        
        // Initialize height
        textarea.style.height = 'auto';
        textarea.style.height = (textarea.scrollHeight) + 'px';
    });

    // Color picker for category form
    const colorInput = document.getElementById('id_color');
    if (colorInput) {
        colorInput.addEventListener('change', function() {
            const preview = document.querySelector('.color-preview');
            if (preview) {
                preview.style.backgroundColor = this.value;
            }
        });
    }

    // Character counter for text fields
    const textInputs = document.querySelectorAll('input[type="text"], textarea');
    textInputs.forEach(input => {
        const maxLength = input.getAttribute('maxlength');
        if (maxLength) {
            const counter = document.createElement('div');
            counter.className = 'text-muted small text-end mt-1';
            counter.id = input.id + '_counter';
            input.parentNode.appendChild(counter);
            
            function updateCounter() {
                const remaining = maxLength - input.value.length;
                counter.textContent = `${input.value.length}/${maxLength} characters`;
                counter.style.color = remaining < 20 ? '#dc3545' : '#6c757d';
            }
            
            input.addEventListener('input', updateCounter);
            updateCounter();
        }
    });

    // Form validation enhancement
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let hasErrors = false;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    hasErrors = true;
                } else {
                    field.classList.remove('is-invalid');
                    field.classList.add('is-valid');
                }
            });
            
            if (hasErrors) {
                e.preventDefault();
                const firstError = form.querySelector('.is-invalid');
                if (firstError) {
                    firstError.focus();
                }
            }
        });
    });
});

// Entry List JavaScript
function initializeEntryList() {
    // Search functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                filterEntries(this.value.toLowerCase());
            }, 300);
        });
    }

    // Filter functionality
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            filterButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            filterEntries('', this.dataset.filter);
        });
    });

    // Smooth scrolling for pagination
    const paginationLinks = document.querySelectorAll('.pagination a');
    paginationLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (this.getAttribute('href') !== '#') {
                setTimeout(() => {
                    document.querySelector('.container').scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }, 100);
            }
        });
    });
}

function filterEntries(searchTerm, filterType = '') {
    const entries = document.querySelectorAll('.entry-card');
    entries.forEach(entry => {
        const title = entry.querySelector('.card-title')?.textContent.toLowerCase() || '';
        const content = entry.querySelector('.entry-excerpt')?.textContent.toLowerCase() || '';
        const matchesSearch = !searchTerm || title.includes(searchTerm) || content.includes(searchTerm);
        
        let matchesFilter = true;
        if (filterType && filterType !== 'all') {
            const entryType = entry.dataset.entryType;
            matchesFilter = entryType === filterType;
        }
        
        entry.style.display = matchesSearch && matchesFilter ? 'block' : 'none';
    });
}

// Entry Detail JavaScript
function initializeEntryDetail() {
    // Smooth scrolling for navigation
    const navLinks = document.querySelectorAll('a[href^="#"]');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Print functionality
    const printBtn = document.getElementById('printBtn');
    if (printBtn) {
        printBtn.addEventListener('click', function() {
            window.print();
        });
    }
}

// Category Form JavaScript
function initializeCategoryForm() {
    const colorInput = document.getElementById('id_color');
    const colorPreview = document.querySelector('.color-preview');
    
    if (colorInput && colorPreview) {
        // Update preview on color change
        colorInput.addEventListener('input', function() {
            colorPreview.style.backgroundColor = this.value;
        });
        
        // Initialize preview
        colorPreview.style.backgroundColor = colorInput.value;
    }

    // Category name validation
    const nameInput = document.getElementById('id_name');
    if (nameInput) {
        nameInput.addEventListener('input', function() {
            const value = this.value.trim();
            const isValid = value.length >= 2 && value.length <= 50;
            
            this.classList.toggle('is-valid', isValid && value.length > 0);
            this.classList.toggle('is-invalid', !isValid && value.length > 0);
        });
    }
}

// Modal JavaScript
function initializeModals() {
    // Auto-focus first input in modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('shown.bs.modal', function() {
            const firstInput = this.querySelector('input, textarea, select');
            if (firstInput) {
                firstInput.focus();
            }
        });
    });

    // Clear form when modal is hidden
    modals.forEach(modal => {
        modal.addEventListener('hidden.bs.modal', function() {
            const form = this.querySelector('form');
            if (form) {
                form.reset();
                form.querySelectorAll('.is-valid, .is-invalid').forEach(el => {
                    el.classList.remove('is-valid', 'is-invalid');
                });
            }
        });
    });
}

// Global functions
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Initialize based on page content
document.addEventListener('DOMContentLoaded', function() {
    // Initialize based on what's present on the page
    if (document.querySelector('.entry-card')) {
        initializeEntryList();
    }
    
    if (document.querySelector('.entry-detail-container')) {
        initializeEntryDetail();
    }
    
    if (document.querySelector('#id_color')) {
        initializeCategoryForm();
    }
    
    if (document.querySelectorAll('.modal').length > 0) {
        initializeModals();
    }
    
    // Global form enhancements
    const allForms = document.querySelectorAll('form');
    allForms.forEach(form => {
        // Prevent double submission
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                setTimeout(() => {
                    submitBtn.disabled = false;
                }, 3000);
            }
        });
    });
});

// Delete entry function for entry list page
function deleteEntry(entryId) {
    // Create a Bootstrap modal for confirmation
    const modalHtml = `
        <div class="modal fade" id="deleteConfirmModal" tabindex="-1">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title">🗑️ Delete Entry</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>Are you sure you want to delete this entry?</p>
                        <p class="text-muted mb-0"><strong>This action cannot be undone.</strong></p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-danger" id="confirmDeleteBtn">Delete Entry</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('deleteConfirmModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show the modal
    const modalElement = document.getElementById('deleteConfirmModal');
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
    
    // Function to clean up modal completely
    function cleanupModal() {
        modal.dispose();
        modalElement.remove();
        // Remove any leftover backdrops
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => backdrop.remove());
        // Remove modal-open class from body
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    }
    
    // Handle confirm button click
    document.getElementById('confirmDeleteBtn').addEventListener('click', function() {
        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                         document.querySelector('meta[name="csrf-token"]')?.content ||
                         getCookie('csrftoken');
        
        // Disable button and show loading
        this.disabled = true;
        this.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Deleting...';
        
        fetch(`/entries/${entryId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
            }
        })
        .then(response => {
            if (response.ok || response.redirected) {
                // Close modal and redirect
                cleanupModal();
                window.location.href = '/entries/';
            } else {
                alert('Error deleting entry. Please try again.');
                this.disabled = false;
                this.innerHTML = 'Delete Entry';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error deleting entry. Please try again.');
            this.disabled = false;
            this.innerHTML = 'Delete Entry';
        });
    });
    
    // Clean up modal and backdrop when hidden
    modalElement.addEventListener('hidden.bs.modal', function() {
        cleanupModal();
    });
}

// Helper function to get cookie value
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}