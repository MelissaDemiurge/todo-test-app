document.addEventListener('DOMContentLoaded', function () {
    // 1. Авто-скрытие flash-сообщений
    const flashMessages = document.querySelector('.flashes');
    if (flashMessages) {
        setTimeout(() => {
            flashMessages.style.transition = 'opacity 0.5s ease-out';
            flashMessages.style.opacity = '0';
            setTimeout(() => flashMessages.remove(), 500);
        }, 5000);
    }

    const tasksContainer = document.getElementById('tasks-container');
    const filterButtons = document.querySelectorAll('.filter-button');
    const sortSelect = document.getElementById('sortSelect');
    const searchInput = document.getElementById('searchInput');
    let currentFilter = 'all';
    let currentSort = 'asc';

    function fetchTasksAndUpdate() {
        let url = `/tasks_data?filter=${currentFilter}&sort=${currentSort}`;
        const query = searchInput.value.trim();
        if (query) {
            url += `&q=${encodeURIComponent(query)}`;
        }

        fetch(url)
            .then(response => {
                if (!response.ok) throw new Error('Ошибка при получении задач');
                return response.text();
            })
            .then(html => {
                tasksContainer.innerHTML = html;
                attachTaskActions(); // привязать обработчики к новым элементам
            })
            .catch(error => console.error(error));
    }

    // 2. Обновление фильтра/сортировки/поиска
    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            currentFilter = button.getAttribute('data-filter');
            filterButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            fetchTasksAndUpdate();
        });
    });

    sortSelect.addEventListener('change', () => {
        currentSort = sortSelect.value;
        fetchTasksAndUpdate();
    });

    let searchTimeout;
    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            fetchTasksAndUpdate();
        }, 300);
    });

    // 3. Универсальный обработчик AJAX-отправки форм
    function setupAjaxForm(selector, options = {}) {
        document.querySelectorAll(selector).forEach(form => {
            form.addEventListener('submit', e => {
                e.preventDefault();
                if (options.confirm && !confirm(options.confirm)) {
                    return;
                }
                const formData = new FormData(form);
                fetch(form.action, {
                    method: 'POST',
                    body: formData,
                    redirect: 'manual'
                })
                    .then(response => {
                        if (response.status < 400) {
                            return fetchTasksAndUpdate();
                        } else {
                            throw new Error(options.errorMessage || 'Ошибка при отправке формы');
                        }
                    })
                    .catch(err => console.error(err));
            });
        });
    }

    function attachTaskActions() {
        setupAjaxForm('form.mark-done-form', {
            errorMessage: 'Ошибка при отметке выполнения'
        });
        setupAjaxForm('form.delete-form', {
            confirm: 'Вы точно хотите удалить?',
            errorMessage: 'Ошибка при удалении задачи'
        });
        setupAjaxForm('form.edit-task-form', {
            errorMessage: 'Ошибка при редактировании задачи'
        });

        // Показ формы редактирования
        document.querySelectorAll('button.edit-button').forEach(button => {
            button.addEventListener('click', () => {
                const id = button.getAttribute('data-id');
                const viewDiv = document.getElementById(`view-${id}`);
                const editForm = document.getElementById(`edit-${id}`);
                if (viewDiv && editForm) {
                    viewDiv.style.display = 'none';
                    editForm.style.display = 'block';
                }
            });
        });

        // Отмена редактирования
        document.querySelectorAll('button.cancel-button').forEach(button => {
            button.addEventListener('click', () => {
                const id = button.getAttribute('data-id');
                const viewDiv = document.getElementById(`view-${id}`);
                const editForm = document.getElementById(`edit-${id}`);
                if (viewDiv && editForm) {
                    editForm.style.display = 'none';
                    viewDiv.style.display = 'flex';
                }
            });
        });
    }

    // 4. Привязка к уже загруженному списку
    attachTaskActions();

    // 5. AJAX-добавление новой задачи
    const addTaskForm = document.getElementById('add-task-form');
    if (addTaskForm) {
        addTaskForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const formData = new FormData(addTaskForm);
            fetch(addTaskForm.action || window.location.href, {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
                .then(response => {
                    if (response.status === 204) {
                        addTaskForm.reset();
                        fetchTasksAndUpdate();
                    } else {
                        return response.text().then(html => {
                            const parser = new DOMParser();
                            const doc = parser.parseFromString(html, 'text/html');
                            const errorSpan = doc.querySelector('.error');
                            const flashMessage = doc.querySelector('.flashes li');
                            let errorMsg = 'Не удалось добавить задачу. Проверьте данные.';
                            if (errorSpan) {
                                errorMsg = errorSpan.textContent;
                            } else if (flashMessage) {
                                errorMsg = flashMessage.textContent;
                            }
                            alert(errorMsg);
                        });
                    }
                })
                .catch(err => console.error('Ошибка при добавлении задачи:', err));
        });
    }
});
