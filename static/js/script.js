function showLoading(formId) {
    const form = document.getElementById(formId);
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
}

function hideLoading(formId) {
    const form = document.getElementById(formId);
    const button = form.querySelector('button[type="submit"]');
    button.disabled = false;
    button.innerHTML = button.getAttribute('data-original-text');
}

function showError(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.querySelector('.container').prepend(alertDiv);
}

function validateFile(file) {
    // Check file type
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        throw new Error('Only PDF files are allowed');
    }
    
    // Check file size (100MB max)
    if (file.size > 100 * 1024 * 1024) {
        throw new Error('File size must be less than 100MB');
    }
}

async function uploadFile(endpoint, formId) {
    const form = document.getElementById(formId);
    const formData = new FormData(form);
    
    try {
        // Validate all files
        const files = formData.getAll('pdfs').length > 0 ? 
            formData.getAll('pdfs') : 
            formData.getAll('pdf');
        
        files.forEach(validateFile);
        
        showLoading(formId);
        
        const response = await fetch(endpoint, {
            method: "POST",
            body: formData
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || 'Operation failed');
        }
        
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = response.headers.get('content-disposition')?.split('filename=')[1] || 'processed.pdf';
        link.click();
        URL.revokeObjectURL(url);
        
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading(formId);
    }
}

// Initialize all forms
document.addEventListener('DOMContentLoaded', () => {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const button = form.querySelector('button[type="submit"]');
        button.setAttribute('data-original-text', button.innerHTML);
        
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            uploadFile(form.action, form.id);
        });
    });
});