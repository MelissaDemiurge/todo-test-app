document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelector('.flashes');
    if (flashMessages) {
        setTimeout(() => {
            flashMessages.style.transition = 'opacity 0.5s ease-out';
            flashMessages.style.opacity = '0';
            setTimeout(() => flashMessages.remove(), 500);
        }, 5000);
    }
});

function editTask(index) {
    const viewDiv = document.getElementById(`view-${index}`);
    const editForm = document.getElementById(`edit-${index}`);
    if (viewDiv && editForm) {
        viewDiv.style.display = 'none';
        editForm.style.display = 'block';
    }
}

function cancelEdit(index) {
    const viewDiv = document.getElementById(`view-${index}`);
    const editForm = document.getElementById(`edit-${index}`);
    if (viewDiv && editForm) {
        editForm.style.display = 'none';
        viewDiv.style.display = 'flex';
    }
}
