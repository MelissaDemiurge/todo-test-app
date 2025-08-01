document.addEventListener('DOMContentLoaded', function() {
    // 1. Автоматическое скрытие flash-сообщений через несколько секунд (без изменений)
    const flashMessages = document.querySelector('.flashes');
    if (flashMessages) {
        setTimeout(() => {
            flashMessages.style.transition = 'opacity 0.5s ease-out';
            flashMessages.style.opacity = '0';
            setTimeout(() => flashMessages.remove(), 500);
        }, 5000);
    }

    // 2. Находим элементы панели фильтрации и поиска
    const tasksContainer = document.getElementById('tasks-container');
    const filterButtons = document.querySelectorAll('.filter-button');
    const sortSelect = document.getElementById('sortSelect');
    const searchInput = document.getElementById('searchInput');

    // Текущее состояние фильтра и сортировки (будем хранить, чтобы включать в запросы)
    let currentFilter = 'all';
    let currentSort = 'asc';

    // 3. Функция AJAX-запроса для получения отфильтрованного списка задач
    function fetchTasksAndUpdate() {
        // Строим URL запроса с учетом фильтра, сортировки и поискового запроса
        let url = `/tasks_data?filter=${currentFilter}&sort=${currentSort}`;
        const query = searchInput.value.trim();
        if (query) {
            url += `&q=${encodeURIComponent(query)}`;
        }

        // Отправляем GET-запрос на сервер (AJAX)
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Ошибка сети при получении задач');
                }
                return response.text();  // сервер возвращает HTML-код списка задач
            })
            .then(html => {
                // Заменяем содержимое контейнера списка задач новым HTML
                tasksContainer.innerHTML = html;
                // Заново привязываем обработчики для новых элементов списка
                attachTaskActions();
            })
            .catch(error => {
                console.error('Ошибка при обновлении списка задач:', error);
            });
    }

    // 4. Обработчики кликов по кнопкам фильтров
    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            currentFilter = button.getAttribute('data-filter');  // читаем тип фильтра (all/done/undone)
            // Обновляем визуально выделение активной кнопки
            filterButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            // Получаем и отображаем отфильтрованный список
            fetchTasksAndUpdate();
        });
    });

    // 5. Обработчик изменения сортировки (выбор в select)
    sortSelect.addEventListener('change', () => {
        currentSort = sortSelect.value;
        fetchTasksAndUpdate();
    });

    // 6. Обработчик ввода в поле поиска (с задержкой - "debounce")
    let searchTimeout;
    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        // Немного задерживаем запрос (300 мс) чтобы не дергать сервер на каждую букву
        searchTimeout = setTimeout(() => {
            fetchTasksAndUpdate();
        }, 300);
    });

    // 7. Функция для привязки AJAX-обработчиков к действиям задач (выполнить, удалить, редактировать)
    function attachTaskActions() {
        // a) Отметка задачи выполненной
        document.querySelectorAll('form.mark-done-form').forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                const formData = new FormData(form);
                fetch(form.action, { method: 'POST', body: formData, redirect: 'manual' })
                    .then(response => {
                        if (response.status < 400) {  // Обрабатываем 302 как успех
                            return fetchTasksAndUpdate();
                        } else {
                            throw new Error('Ошибка при отметке выполнения');
                        }
                    })
                    .catch(err => console.error(err));
            });
        });

        // b) Удаление задачи
        document.querySelectorAll('form.delete-form').forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                if (!confirm('Вы точно хотите удалить?')) {
                    return;
                }
                const formData = new FormData(form);
                fetch(form.action, { method: 'POST', body: formData, redirect: 'manual' })
                    .then(response => {
                        if (response.status < 400) {  // Обрабатываем 302 как успех
                            return fetchTasksAndUpdate();
                        } else {
                            throw new Error('Ошибка при удалении задачи');
                        }
                    })
                    .catch(err => console.error(err));
            });
        });

        // c) Сохранение отредактированной задачи
        document.querySelectorAll('form.edit-task-form').forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                const formData = new FormData(form);
                fetch(form.action, { method: 'POST', body: formData, redirect: 'manual' })
                    .then(response => {
                        if (response.status < 400) {  // Обрабатываем 302 как успех
                            return fetchTasksAndUpdate();
                        } else {
                            throw new Error('Ошибка при редактировании задачи');
                        }
                    })
                    .catch(err => console.error(err));
            });
        });

        // d) Кнопки "Редактировать" – показать форму редактирования вместо текста
        document.querySelectorAll('button.edit-button').forEach(button => {
            button.addEventListener('click', () => {
                const id = button.getAttribute('data-id');      // получаем ID задачи из атрибута
                const viewDiv = document.getElementById(`view-${id}`);   // текущий блок просмотра
                const editForm = document.getElementById(`edit-${id}`);  // соответствующая форма редактирования
                if (viewDiv && editForm) {
                    viewDiv.style.display = 'none';    // скрываем текстовый блок
                    editForm.style.display = 'block';  // показываем форму редактирования
                }
            });
        });

        // e) Кнопки "Отмена" – закрыть форму редактирования, вернуть вид просмотра
        document.querySelectorAll('button.cancel-button').forEach(button => {
            button.addEventListener('click', () => {
                const id = button.getAttribute('data-id');
                const viewDiv = document.getElementById(`view-${id}`);
                const editForm = document.getElementById(`edit-${id}`);
                if (viewDiv && editForm) {
                    editForm.style.display = 'none';
                    viewDiv.style.display = 'flex';  // возвращаем как flex (было flex-контейнером)
                }
            });
        });
    }

    // Привязываем обработчики к уже загруженному при старте списку задач
    attachTaskActions();

    // 8. AJAX-отправка формы добавления новой задачи
    const addTaskForm = document.getElementById('add-task-form');
    if (addTaskForm) {
        addTaskForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(addTaskForm);
            fetch(addTaskForm.action || window.location.href, {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
                .then(response => {
                    console.log('Status for add:', response.status);
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