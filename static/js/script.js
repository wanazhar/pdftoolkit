/**
 * PDF Toolkit Client-Side Logic
 * Modern UI interactions and API handling
 */

document.addEventListener('DOMContentLoaded', () => {
    // Setup UI feedback and Toast notifications
    createToastContainer();
    initializeForms();
});

/**
 * Global form initialization
 */
function initializeForms() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const button = form.querySelector('button[type="submit"]');
        if (button) {
            button.setAttribute('data-original-text', button.innerHTML);
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                handleFileUpload(form);
            });
        }
    });
}

/**
 * Generalized file upload and processing handler
 * @param {HTMLFormElement} form
 */
async function handleFileUpload(form) {
    const formData = new FormData(form);
    const endpoint = form.action;
    const submitBtn = form.querySelector('button[type="submit"]');

    try {
        validateFormFiles(formData);
        toggleLoading(submitBtn, true);

        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorMsg = await response.text();
            throw new Error(errorMsg || `Server responded with ${response.status}`);
        }

        // Handle successful response (usually a file blob)
        const blob = await response.blob();
        const contentDisposition = response.headers.get('content-disposition');
        let filename = 'processed_file';

        if (contentDisposition && contentDisposition.includes('filename=')) {
            filename = contentDisposition.split('filename=')[1].replace(/["']/g, '');
        } else {
            // Fallback extension based on mime type
            const mime = blob.type;
            if (mime === 'application/zip') filename += '.zip';
            if (mime === 'application/pdf') filename += '.pdf';
            if (mime === 'text/plain') filename += '.txt';
        }

        triggerDownload(blob, filename);
        showToast('Success!', `Your file ${filename} has been processed.`, 'success');

    } catch (error) {
        console.error('Processing error:', error);
        showToast('Operation Failed', error.message, 'danger');
    } finally {
        toggleLoading(submitBtn, false);
    }
}

/**
 * Validate files before sending to server
 * @param {FormData} formData
 */
function validateFormFiles(formData) {
    const fileFields = ['pdf', 'pdfs', 'images'];
    let files = [];

    fileFields.forEach(field => {
        const fieldFiles = formData.getAll(field);
        if (fieldFiles.length > 0) files = files.concat(fieldFiles);
    });

    if (files.length === 0) return;

    files.forEach(file => {
        if (!file.name) return; // Skip empty inputs

        // Size check (100MB)
        if (file.size > 100 * 1024 * 1024) {
            throw new Error(`File ${file.name} exceeds 100MB limit.`);
        }

        // Extension check
        const ext = file.name.split('.').pop().toLowerCase();
        const isPdf = ['pdf'].includes(ext);
        const isImg = ['jpg', 'jpeg', 'png', 'webp'].includes(ext);

        // This is a simple client-side check. Server performs definitive validation.
    });
}

/**
 * Toggle button loading state
 */
function toggleLoading(button, isLoading) {
    button.disabled = isLoading;
    if (isLoading) {
        button.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            Processing...
        `;
    } else {
        button.innerHTML = button.getAttribute('data-original-text');
    }
}

/**
 * Trigger browser file download
 */
function triggerDownload(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

/**
 * Toast Notifications System
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    document.body.appendChild(container);
}

function showToast(title, message, type = 'primary') {
    const container = document.getElementById('toast-container');
    const toastId = 'toast-' + Date.now();

    const toastHTML = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header bg-${type} text-white">
                <strong class="me-auto">${title}</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', toastHTML);
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 5000 });
    toast.show();

    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}
