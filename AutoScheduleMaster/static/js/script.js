// Generic utilities and shared functionality

// Flash message timeout
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss flash messages after 5 seconds
    setTimeout(function() {
        const flashMessages = document.querySelectorAll('.alert-dismissible');
        flashMessages.forEach(function(message) {
            // Use Bootstrap's dismiss method if available
            const bsAlert = bootstrap.Alert.getOrCreateInstance(message);
            if (bsAlert) {
                bsAlert.close();
            } else {
                // Fallback to manual removal
                message.style.opacity = '0';
                setTimeout(function() {
                    message.remove();
                }, 500);
            }
        });
    }, 5000);

    // Initialize all tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

    // Initialize all popovers
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
});

// Confirm delete operation
function confirmDelete(formId, entityName) {
    if (confirm(`Are you sure you want to delete this ${entityName}? This action cannot be undone.`)) {
        document.getElementById(formId).submit();
    }
    return false;
}

// Toggle form visibility
function toggleForm(formId) {
    const form = document.getElementById(formId);
    if (form.style.display === 'none' || form.style.display === '') {
        form.style.display = 'block';
    } else {
        form.style.display = 'none';
    }
}

// Format time from HH:MM format to a more readable form
function formatTime(timeStr) {
    if (!timeStr) return '';
    
    const [hours, minutes] = timeStr.split(':');
    const hour = parseInt(hours, 10);
    const minute = parseInt(minutes, 10);
    
    // Convert 24-hour format to 12-hour format with AM/PM
    let period = 'AM';
    let hour12 = hour;
    
    if (hour >= 12) {
        period = 'PM';
        hour12 = hour === 12 ? 12 : hour - 12;
    }
    
    if (hour12 === 0) {
        hour12 = 12;
    }
    
    return `${hour12}:${minute.toString().padStart(2, '0')} ${period}`;
}

// Format date strings
function formatDate(dateStr) {
    if (!dateStr) return '';
    
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}
