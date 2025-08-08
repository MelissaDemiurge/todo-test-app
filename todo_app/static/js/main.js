document.addEventListener('DOMContentLoaded', function () {

    const tasksContainer = document.getElementById('tasks-container');
    function ensureToastRoot() {
        let root = document.getElementById('toast-root');
        if (!root) {
            root = document.createElement('div');
            root.id = 'toast-root';
            root.className = 'toast-container';
            root.setAttribute('aria-live', 'polite');
            root.setAttribute('aria-atomic', 'true');
            document.body.appendChild(root);
        }
        return root;
    }
    function showToast(message, type = 'info', timeoutMs = 3000) {
        const toastRoot = ensureToastRoot();
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        toastRoot.appendChild(toast);
        setTimeout(() => {
            toast.style.transition = 'opacity 0.4s ease-out, transform 0.4s ease-out';
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-6px)';
            setTimeout(() => toast.remove(), 400);
        }, timeoutMs);
    }
    const filterButtons = document.querySelectorAll('.filter-button');
    const sortSelect = document.getElementById('sortSelect');
    const searchInput = document.getElementById('searchInput');
    let currentFilter = 'all';
    let currentSort = 'asc';

    // Полный рефреш списка вместо сложных микропатчей — надёжнее
    let currentPage = 1;
    const perPage = 15;

    function fetchTasksAndUpdate() {
        let url = `/tasks_data?filter=${currentFilter}&sort=${currentSort}&page=${currentPage}&per_page=${perPage}`;
        const query = searchInput.value.trim();
        if (query) {
            url += `&q=${encodeURIComponent(query)}`;
        }

        fetch(url, { headers: { 'Accept': 'text/html' }, cache: 'no-store' })
            .then(response => {
                if (!response.ok) throw new Error('Ошибка при получении задач');
                return response.text();
            })
            .then(html => {
                tasksContainer.innerHTML = html;
                attachTaskActions(); // привязать обработчики к новым элементам
                // Синхронизируем текущую страницу по данным сервера
                const pag = document.querySelector('.pagination');
                if (pag) {
                    const serverPage = Number(pag.getAttribute('data-page')) || 1;
                    currentPage = Math.max(1, serverPage);
                }
                attachPagination();
            })
            .catch(error => console.error(error));
    }

    // Фильтрация/сортировка/поиск
    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            currentFilter = button.getAttribute('data-filter');
            filterButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            currentPage = 1;
            fetchTasksAndUpdate();
        });
    });

    sortSelect.addEventListener('change', () => {
        currentSort = sortSelect.value;
        currentPage = 1;
        fetchTasksAndUpdate();
    });

    let searchTimeout;
    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentPage = 1;
            fetchTasksAndUpdate();
        }, 300);
    });

    // Универсальный обработчик AJAX-отправки форм (mark done/delete/edit)
    function setupAjaxForm(selector, options = {}) {
        const mergedOptions = {
            successType: 'success',
            errorType: 'error',
            ...options
        };
        document.querySelectorAll(selector).forEach(form => {
            form.addEventListener('submit', e => {
                e.preventDefault();
                if (mergedOptions.confirm && !confirm(mergedOptions.confirm)) {
                    return;
                }
                const formData = new FormData(form);
                fetch(form.action, {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                })
                    .then(async response => {
                        const contentType = response.headers.get('Content-Type') || '';
                        if (response.ok && contentType.includes('application/json')) {
                            const data = await response.json();
                            showToast((data && data.message) || mergedOptions.successMessage || 'Операция выполнена', mergedOptions.successType);
                            return fetchTasksAndUpdate();
                        }
                        if (!response.ok && contentType.includes('application/json')) {
                            const data = await response.json();
                            showToast(data.message || (mergedOptions.errorMessage || 'Ошибка при отправке формы'), mergedOptions.errorType);
                            return;
                        }
                        // Fallback
                        if (response.ok) {
                            showToast(mergedOptions.successMessage || 'Операция выполнена', mergedOptions.successType);
                            return fetchTasksAndUpdate();
                        } else {
                            showToast(mergedOptions.errorMessage || 'Ошибка при отправке формы', mergedOptions.errorType);
                        }
                    })
                    .catch(err => console.error(err));
            });
        });
    }

    function attachTaskActions() {
        // Массовое удаление и выбор — подключаем только если есть панель
        const bulkForm = document.querySelector('form.bulk-delete-form');
        if (bulkForm) {
            setupAjaxForm('form.bulk-delete-form', {
                confirm: 'Удалить выбранные задачи?',
                successMessage: 'Задачи удалены',
                successType: 'warning',
                errorMessage: 'Не удалось удалить выбранные задачи'
            });

            const taskCheckboxes = Array.from(document.querySelectorAll('.task-select'));
            const selectAllTop = document.getElementById('select-all-top');
            const countTop = document.getElementById('selected-count-top');
            const bulkDeleteBtn = bulkForm.querySelector('button.delete-button');

            function updateSelectedCount() {
                const selected = taskCheckboxes.filter(cb => cb.checked).map(cb => cb.getAttribute('data-id'));
                if (countTop) countTop.textContent = selected.length ? `Выбрано: ${selected.length}` : '';
                const topIds = document.getElementById('bulk-ids-top');
                if (topIds) topIds.value = selected.join(',');
                if (bulkDeleteBtn) bulkDeleteBtn.disabled = selected.length === 0;
            }

            function setAll(checked) {
                taskCheckboxes.forEach(cb => cb.checked = checked);
                updateSelectedCount();
            }

            taskCheckboxes.forEach(cb => cb.addEventListener('change', updateSelectedCount));
            if (selectAllTop) selectAllTop.addEventListener('change', () => setAll(selectAllTop.checked));
            updateSelectedCount();
        }

        setupAjaxForm('form.mark-done-form', {
            successMessage: 'Задача отмечена выполненной',
            successType: 'success',  // зелёный
            errorMessage: 'Ошибка при отметке выполнения',
            errorType: 'error'       // красный
        });
        setupAjaxForm('form.delete-form', {
            confirm: 'Вы точно хотите удалить?',
            successMessage: 'Задача удалена',
            successType: 'warning',  // жёлтый
            errorMessage: 'Ошибка при удалении задачи',
            errorType: 'error'
        });
        setupAjaxForm('form.edit-task-form', {
            successMessage: 'Задача обновлена',
            successType: 'info',     // синий
            errorMessage: 'Ошибка при редактировании задачи',
            errorType: 'error'
        });

        // Показ формы редактирования для выбранной задачи
        document.querySelectorAll('button.edit-button').forEach(button => {
            button.addEventListener('click', () => {
                const id = button.getAttribute('data-id');
                const viewDiv = document.getElementById(`view-${id}`);
                const editForm = document.getElementById(`edit-${id}`);
                if (viewDiv && editForm) {
                    viewDiv.style.display = 'none';
                    editForm.style.display = 'block';
                    const inputEl = document.getElementById(`title-input-${id}`);
                    if (inputEl) {
                        inputEl.focus();
                        inputEl.setSelectionRange(inputEl.value.length, inputEl.value.length);
                    }
                }
            });
        });

        // Отмена редактирования и возврат к виду задачи
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

    // Привязка к уже загруженному списку и первичная загрузка (подстраховка)
    attachTaskActions();
    fetchTasksAndUpdate();

    // AJAX-добавление новой задачи
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
                .then(async response => {
                    const contentType = response.headers.get('Content-Type') || '';
                    if (response.ok && contentType.includes('application/json')) {
                        const data = await response.json();
                        addTaskForm.reset();
                        showToast((data && data.message) || 'Задача добавлена', 'success');
                        fetchTasksAndUpdate();
                        return;
                    }
                    if (!response.ok && contentType.includes('application/json')) {
                        const data = await response.json();
                        showToast(data.message || 'Не удалось добавить задачу. Проверьте данные.', 'error');
                        return;
                    }
                    // Fallback
                    if (response.ok) {
                        addTaskForm.reset();
                        showToast('Задача добавлена', 'success');
                        fetchTasksAndUpdate();
                    } else {
                        showToast('Не удалось добавить задачу. Проверьте данные.', 'error');
                    }
                })
                .catch(err => console.error('Ошибка при добавлении задачи:', err));
        });
    }

    function attachPagination() {
        const container = document.querySelector('.pagination');
        if (!container) return;
        const totalPages = Math.max(1, Number(container.getAttribute('data-total-pages')) || 1);
        const prevBtn = container.querySelector('.page-prev');
        const nextBtn = container.querySelector('.page-next');
        const setPage = (page) => {
            currentPage = Math.max(1, Math.min(totalPages, page));
            fetchTasksAndUpdate();
        };
        if (prevBtn) {
            prevBtn.addEventListener('click', () => setPage(currentPage - 1));
        }
        if (nextBtn) {
            nextBtn.addEventListener('click', () => setPage(currentPage + 1));
        }
    }
});

