document.addEventListener('DOMContentLoaded', function() {
    // Обработка удаления словарей
    document.querySelectorAll('.delete-dictionary').forEach(btn => {
        btn.addEventListener('click', function() {
            const dictionaryId = this.dataset.id;

            if (confirm('Вы уверены, что хотите удалить этот словарь? Это действие нельзя отменить.')) {
                fetch(`/delete-dictionary/${dictionaryId}`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.closest('tr').remove();
                        showAlert('Словарь успешно удалён', 'success');
                    } else {
                        showAlert('Ошибка при удалении: ' + data.message, 'danger');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showAlert('Произошла ошибка', 'danger');
                });
            }
        });
    });

    function showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show mt-3`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.querySelector('.card-body').prepend(alertDiv);

        setTimeout(() => {
            alertDiv.classList.remove('show');
            setTimeout(() => alertDiv.remove(), 150);
        }, 3000);
    }
});
