document.addEventListener('DOMContentLoaded', function() {
    // Add event listener to the class selection dropdown
    const classSelect = document.getElementById('class-select');
    if (classSelect) {
        classSelect.addEventListener('change', function() {
            const classId = this.value;
            if (classId) {
                window.location.href = `/view-timetable/${classId}`;
            }
        });
    }

    // Add event listener to the Generate button
    const generateBtn = document.getElementById('generate-timetable');
    if (generateBtn) {
        generateBtn.addEventListener('click', function() {
            const classId = document.getElementById('class-select').value;
            if (!classId) {
                alert('Please select a class first');
                return;
            }
            
            if (confirm('This will clear any existing timetable for this class. Are you sure you want to continue?')) {
                const form = document.getElementById('generate-form');
                form.action = `/generate-timetable/${classId}`;
                form.submit();
            }
        });
    }

    // Add event listener to the Export PDF button
    const exportBtn = document.getElementById('export-pdf');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            exportTimetableToPDF();
        });
    }

    // Add event listener to tab changes to ensure timetable is properly rendered
    const timetableTabs = document.querySelectorAll('a[data-bs-toggle="tab"]');
    timetableTabs.forEach(function(tab) {
        tab.addEventListener('shown.bs.tab', function(e) {
            // Re-render any timetable in the shown tab if needed
            const targetSection = e.target.getAttribute('href');
            // Any additional rendering logic can go here
        });
    });
});

// Function to export the timetable as PDF
function exportTimetableToPDF() {
    // Get the class ID and name
    const classSelect = document.getElementById('class-select');
    const classId = classSelect.value;
    const className = classSelect.options[classSelect.selectedIndex].text;
    
    if (!classId) {
        alert('Please select a class first');
        return;
    }
    
    // Create a new jsPDF instance
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF('landscape', 'mm', 'a4');
    
    // Set document properties
    doc.setProperties({
        title: `Timetable for ${className}`,
        subject: 'School Timetable',
        author: 'Timetable Generator',
        keywords: 'timetable, schedule, school'
    });
    
    // Add the document title
    doc.setFontSize(16);
    doc.text(`Timetable for ${className}`, 15, 15);
    
    // Get all section tabs
    const sectionTabs = document.querySelectorAll('.nav-link[data-bs-toggle="tab"]');
    let yOffset = 25;
    
    // For each section, add its timetable to the PDF
    sectionTabs.forEach((tab, index) => {
        const sectionId = tab.getAttribute('href').substring(1);
        const sectionName = tab.textContent.trim();
        const timetableElement = document.getElementById(sectionId);
        
        // Add a new page if this is not the first section
        if (index > 0) {
            doc.addPage();
            doc.setFontSize(16);
            doc.text(`Timetable for ${className} - Section ${sectionName}`, 15, 15);
            yOffset = 25;
        } else {
            // Add section title for the first section on the first page
            doc.setFontSize(14);
            doc.text(`Section ${sectionName}`, 15, yOffset);
            yOffset += 10;
        }
        
        // Clone the timetable to avoid styles affecting the real DOM
        const timetableClone = timetableElement.cloneNode(true);
        
        // Get the timetable table
        const timetableTable = timetableClone.querySelector('table');
        
        // Use html2canvas to convert the table to an image
        html2canvas(timetableTable, {
            scale: 1,
            logging: false,
            useCORS: true
        }).then(canvas => {
            // Add the table image to the PDF
            const imgData = canvas.toDataURL('image/png');
            const imgWidth = doc.internal.pageSize.getWidth() - 30;
            const imgHeight = canvas.height * imgWidth / canvas.width;
            
            doc.addImage(imgData, 'PNG', 15, yOffset, imgWidth, imgHeight);
            
            // If this is the last section, save the PDF
            if (index === sectionTabs.length - 1) {
                doc.save(`timetable_${className.replace(/\s+/g, '_')}.pdf`);
            }
        });
    });
}

// Function to show conflict details
function showConflictDetails(conflicts) {
    // Create and display a modal with conflict information
    const modalElement = document.getElementById('conflict-modal');
    const modal = new bootstrap.Modal(modalElement);
    
    // Populate the modal with conflict information
    const modalBody = modalElement.querySelector('.modal-body');
    modalBody.innerHTML = '';
    
    if (conflicts.length === 0) {
        modalBody.innerHTML = '<p class="text-success">No conflicts found!</p>';
    } else {
        const list = document.createElement('ul');
        list.classList.add('list-group');
        
        conflicts.forEach(conflict => {
            const item = document.createElement('li');
            item.classList.add('list-group-item');
            item.textContent = conflict;
            list.appendChild(item);
        });
        
        modalBody.appendChild(list);
    }
    
    // Show the modal
    modal.show();
}
