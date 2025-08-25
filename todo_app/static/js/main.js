document.addEventListener('DOMContentLoaded', () => {
    const tasksContainer = document.getElementById('tasks-container');
    const filterButtons = document.querySelectorAll('.filter-button');
    const sortSelect = document.getElementById('sortSelect');
    const searchInput = document.getElementById('searchInput');

    // ---------- UI helpers ----------
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
        const MAX_TOASTS = 3;
        while (toastRoot.children.length >= MAX_TOASTS) {
            toastRoot.firstChild.remove();
        }
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.setAttribute('role', 'alert');
        toast.textContent = message;
        toastRoot.appendChild(toast);
        setTimeout(() => {
            toast.style.transition = 'opacity 0.4s ease-out, transform 0.4s ease-out';
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-6px)';
            setTimeout(() => toast.remove(), 400);
        }, timeoutMs);
    }

    const debounce = (fn, wait = 300) => {
        let timeoutId;
        return (...args) => {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => fn(...args), wait);
        };
    };

    // ---------- State ----------
    const state = {
        currentFilter: 'all',
        currentSort: 'asc',
        currentPage: 1,
        perPage: 15,
        totalPages: 1,
    };

    const getSearchQuery = () => ((searchInput && searchInput.value) || '').trim();

    const buildSearchParams = () => {
        const params = new URLSearchParams({
            filter: state.currentFilter,
            sort: state.currentSort,
            page: String(state.currentPage),
            per_page: String(state.perPage),
        });
        const q = getSearchQuery();
        if (q) params.set('q', q);
        return params;
    };

    const buildTasksUrl = () => {
        const params = buildSearchParams();
        return `/tasks_data?${params.toString()}`;
    };
    // ----------- URL sync helpers -----------
    function syncUrl() {
        const params = buildSearchParams();
        const newUrl = `${window.location.pathname}?${params.toString()}`;
        history.pushState(null, '', newUrl);
    }

    function applyUrlToState() {
        const params = new URLSearchParams(window.location.search);
        const filter = params.get('filter');
        if (filter) state.currentFilter = filter;
        const sort = params.get('sort');
        if (sort) state.currentSort = sort;
        const page = parseInt(params.get('page') || '1', 10);
        if (!Number.isNaN(page) && page > 0) state.currentPage = page;
        const perPage = parseInt(params.get('per_page') || '', 10);
        if (!Number.isNaN(perPage) && perPage > 0) state.perPage = perPage;
        const q = params.get('q');
        if (searchInput && q !== null) searchInput.value = q;
    }

    function reflectStateToUI() {
        // Обновление фильтров
        filterButtons.forEach((btn) => {
            if (btn.getAttribute('data-filter') === state.currentFilter) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        if (sortSelect) sortSelect.value = state.currentSort;
    }

    // Применяем параметры URL при первой загрузке
    applyUrlToState();
    reflectStateToUI();

    // Поддержка кнопок «Назад/Вперёд»
    window.addEventListener('popstate', () => {
        applyUrlToState();
        reflectStateToUI();
        fetchTasksAndUpdate();
    });
    // Allow cancelling outdated list fetches (e.g., fast typing)
    let tasksFetchController = null;

    // ---------- Network/Form helpers ----------
    function setFormBusy(form, busy, buttonSelector = 'button') {
        if (busy) {
            form.setAttribute('aria-busy', 'true');
            form.querySelectorAll(buttonSelector).forEach((btn) => {
                btn.disabled = true;
            });
        } else {
            form.removeAttribute('aria-busy');
            form.querySelectorAll(buttonSelector).forEach((btn) => {
                btn.disabled = false;
            });
        }
    }

    async function handleResponseToast(response, {
        successMessage,
        successType = 'success',
        errorMessage,
        errorType = 'error',
    } = {}) {
        const contentType = response.headers.get('Content-Type') || '';
        if (contentType.includes('application/json')) {
            let data = null;
            try {
                data = await response.json();
            } catch (_) {
                
            }
            if (response.ok) {
                showToast((data && data.message) || successMessage || 'Операция выполнена', successType);
                return { ok: true, data };
            }
            showToast((data && data.message) || errorMessage || 'Ошибка при отправке формы', errorType);
            return { ok: false, data };
        }
        if (response.ok) {
            showToast(successMessage || 'Операция выполнена', successType);
            return { ok: true };
        }
        showToast(errorMessage || 'Ошибка при отправке формы', errorType);
        return { ok: false };
    }

    async function postFormWithToast(form, toastCfg = {}, actionOverride) {
        const response = await fetch(actionOverride || form.action || window.location.href, {
            method: 'POST',
            body: new FormData(form),
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        return handleResponseToast(response, toastCfg);
    }

    const syncPaginationState = () => {
        const pag = document.querySelector('.pagination');
        if (!pag) {
            state.currentPage = 1;
            state.totalPages = 1;
            return;
        }
        const serverPage = Number(pag.getAttribute('data-page')) || 1;
        state.currentPage = Math.max(1, serverPage);
        const totalPages = Number(pag.getAttribute('data-total-pages')) || 1;
        state.totalPages = Math.max(1, totalPages);
    };

    const fetchTasksAndUpdate = async () => {
        if (!tasksContainer) return;
        // Abort previous fetch if still in-flight
        if (tasksFetchController) tasksFetchController.abort();
        tasksFetchController = new AbortController();
        const url = buildTasksUrl();
        document.body.classList.add('loading');
        try {
            const response = await fetch(url, {
                headers: { Accept: 'text/html' },
                cache: 'no-store',
                signal: tasksFetchController.signal,
            });
            if (!response.ok) throw new Error('Ошибка при получении задач');
            const html = await response.text();
            tasksContainer.innerHTML = html;
            syncPaginationState();
            // Обновить состояние панели выбора при каждой перерисовке
            updateSelectedCount();
        } catch (error) {
            if (error && error.name === 'AbortError') return; // ожидаемо при отмене
            console.error(error);
            showToast('Не удалось загрузить список задач', 'error');
        } finally {
            document.body.classList.remove('loading');
        }
    };

    function navigateAndReload() {
        syncUrl();
        fetchTasksAndUpdate();
    }

    // ---------- Filters/Sort/Search ----------
    filterButtons.forEach((button) => {
        button.addEventListener('click', () => {
            state.currentFilter = button.getAttribute('data-filter') || 'all';
            state.currentPage = 1;
            reflectStateToUI();
            navigateAndReload();
        });
    });

    if (sortSelect) {
        sortSelect.addEventListener('change', () => {
            state.currentSort = sortSelect.value || 'asc';
            state.currentPage = 1;
            navigateAndReload();
        });
    }

    if (searchInput) {
        const onSearch = debounce(() => {
            state.currentPage = 1;
            navigateAndReload();
        }, 300);
        searchInput.addEventListener('input', onSearch);
    }

    // ---------- Delegated forms handling ----------
    const formConfigs = [
        {
            selector: 'form.bulk-delete-form',
            confirm: 'Удалить выбранные задачи?',
            successMessage: 'Задачи удалены',
            successType: 'warning',
            errorMessage: 'Не удалось удалить выбранные задачи',
            errorType: 'error',
        },
        {
            selector: 'form.mark-done-form',
            successMessage: 'Задача отмечена выполненной',
            successType: 'success',
            errorMessage: 'Ошибка при отметке выполнения',
            errorType: 'error',
        },
        {
            selector: 'form.delete-form',
            confirm: 'Вы точно хотите удалить?',
            successMessage: 'Задача удалена',
            successType: 'warning',
            errorMessage: 'Ошибка при удалении задачи',
            errorType: 'error',
        },
        {
            selector: 'form.edit-task-form',
            successMessage: 'Задача обновлена',
            successType: 'info',
            errorMessage: 'Ошибка при редактировании задачи',
            errorType: 'error',
        },
    ];

    const getFormConfig = (form) => formConfigs.find((cfg) => form.matches(cfg.selector));

    document.addEventListener('submit', async (e) => {
        const form = e.target;
        if (!(form instanceof HTMLFormElement)) return;
        const cfg = getFormConfig(form);
        if (!cfg) return;
        e.preventDefault();
        if (cfg.confirm && !confirm(cfg.confirm)) return;

        setFormBusy(form, true);
        try {
            const result = await postFormWithToast(form, {
                successMessage: cfg.successMessage,
                successType: cfg.successType,
                errorMessage: cfg.errorMessage,
                errorType: cfg.errorType,
            });
            if (result && result.ok) {
                await fetchTasksAndUpdate();
            }
        } catch (err) {
            console.error(err);
            showToast('Ошибка сети. Попробуйте ещё раз.', 'error');
        } finally {
            setFormBusy(form, false);
        }
    });

    // ---------- Edit/Cancellation toggles (delegated) ----------
    document.addEventListener('click', (e) => {
        const editBtn = e.target.closest && e.target.closest('button.edit-button');
        if (editBtn) {
            const id = editBtn.getAttribute('data-id');
            const viewDiv = document.getElementById(`view-${id}`);
            const editForm = document.getElementById(`edit-${id}`);
            if (viewDiv && editForm) {
                viewDiv.style.display = 'none';
                editForm.style.display = 'block';
                const inputEl = document.getElementById(`title-input-${id}`);
                if (inputEl) {
                    // Сохранить исходное значение, чтобы можно было восстановить при отмене
                    inputEl.dataset.originalValue = inputEl.value;
                    inputEl.focus();
                    const len = inputEl.value.length;
                    inputEl.setSelectionRange(len, len);
                }
            }
            return;
        }

        const cancelBtn = e.target.closest && e.target.closest('button.cancel-button');
        if (cancelBtn) {
            const id = cancelBtn.getAttribute('data-id');
            const viewDiv = document.getElementById(`view-${id}`);
            const editForm = document.getElementById(`edit-${id}`);
            if (viewDiv && editForm) {
                const inputEl = document.getElementById(`title-input-${id}`);
                if (inputEl && inputEl.dataset.originalValue !== undefined) {
                    inputEl.value = inputEl.dataset.originalValue;
                }
                editForm.style.display = 'none';
                viewDiv.style.display = 'grid';
            }
            return;
        }

        // Pagination controls
        const prevBtn = e.target.closest && e.target.closest('.pagination .page-prev');
        const nextBtn = e.target.closest && e.target.closest('.pagination .page-next');
        if (prevBtn || nextBtn) {
            const totalPages = state.totalPages || 1;
            const setPage = (page) => {
                state.currentPage = Math.max(1, Math.min(totalPages, page));
                navigateAndReload();
            };
            if (prevBtn) setPage(state.currentPage - 1);
            if (nextBtn) setPage(state.currentPage + 1);
        }
    });

    // ---------- Bulk selection (delegated) ----------
    function updateSelectedCount() {
        const bulkForm = document.querySelector('form.bulk-delete-form');
        if (!bulkForm) return;
        const taskCheckboxes = Array.from(tasksContainer.querySelectorAll('.task-select'));
        const selectedIds = taskCheckboxes.filter((cb) => cb.checked).map((cb) => cb.getAttribute('data-id'));
        const countTop = document.getElementById('selected-count-top');
        if (countTop) countTop.textContent = selectedIds.length ? `Выбрано: ${selectedIds.length}` : '';
        const topIds = document.getElementById('bulk-ids-top');
        if (topIds) topIds.value = selectedIds.join(',');
        const bulkDeleteBtn = bulkForm.querySelector('button.delete-button');
        if (bulkDeleteBtn) bulkDeleteBtn.disabled = selectedIds.length === 0;
        const selectAllCb = document.getElementById('select-all-top');
        if (selectAllCb) selectAllCb.checked = taskCheckboxes.length > 0 && selectedIds.length === taskCheckboxes.length;
    }

    document.addEventListener('change', (e) => {
        const target = e.target;
        if (!(target instanceof HTMLElement)) return;
        if (target.matches && target.matches('.task-select')) {
            updateSelectedCount();
            return;
        }
        if (target.id === 'select-all-top' && 'checked' in target) {
            const checked = target.checked;
            tasksContainer.querySelectorAll('.task-select').forEach((cb) => {
                cb.checked = checked;
            });
            updateSelectedCount();
        }
    });

    // ---------- Add new task (async/await) ----------
    const addTaskForm = document.getElementById('add-task-form');
    if (addTaskForm) {
        addTaskForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            setFormBusy(addTaskForm, true, 'button[type="submit"]');
            try {
                const result = await postFormWithToast(addTaskForm, {
                    successMessage: 'Задача добавлена',
                    successType: 'success',
                    errorMessage: 'Не удалось добавить задачу. Проверьте данные.',
                    errorType: 'error',
                }, addTaskForm.action || window.location.href);
                if (result && result.ok) {
                    addTaskForm.reset();
                    await fetchTasksAndUpdate();
                }
            } catch (err) {
                console.error('Ошибка при добавлении задачи:', err);
                showToast('Ошибка сети. Попробуйте ещё раз.', 'error');
            } finally {
                setFormBusy(addTaskForm, false, 'button[type="submit"]');
            }
        });
    }

    // ---------- Initial load ----------
    updateSelectedCount();
    fetchTasksAndUpdate();
});

