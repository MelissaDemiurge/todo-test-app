from flask import request, redirect, url_for, jsonify
from functools import wraps

def is_ajax():
    """Проверка, является ли запрос AJAX (по заголовку X-Requested-With)."""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

def ok(message='Операция выполнена', **extra):
    """Успешный JSON-ответ 200 с унифицированной схемой."""
    payload = {"success": True, "message": message}
    if extra:
        payload.update(extra)
    return jsonify(payload), 200

def bad_request(message='Ошибка', **extra):
    """Ошибочный JSON-ответ 400 с унифицированной схемой."""
    payload = {"success": False, "message": message}
    if extra:
        payload.update(extra)
    return jsonify(payload), 400

def first_error(form, default_message='Некорректные данные формы'):
    """Вернуть первый текст ошибки из form.errors либо default_message."""
    error_messages = []
    for field_errors in getattr(form, 'errors', {}).values():
        for error in field_errors:
            error_messages.append(error)
    return error_messages[0] if error_messages else default_message

def ajax_required(FormClass):
    """Декоратор для POST-обработчиков с поддержкой AJAX.
    - Обычные формы: редирект на список при успехе/ошибке.
    - AJAX: 200 JSON при успехе (если обработчик ничего не вернул — {success: true}),
            400 JSON при ошибке вида {success: false, message}.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            form = FormClass()
            is_ajax_req = is_ajax()

            # Если форма невалидна до вызова обработчика
            if not form.validate_on_submit():
                if is_ajax_req:
                    error_text = first_error(form, 'Некорректные данные формы')
                    return bad_request(error_text)
                # Для обычных POST — редирект на список
                return redirect(url_for('tasks.index'))

            # Форма валидна — даём обработчику шанс внести бизнес-ошибки
            result = view_func(form, *args, **kwargs)
            # Если обработчик что-то явно вернул —
            # для AJAX возвращаем как есть, для обычного запроса делаем редирект
            if result is not None:
                if is_ajax_req:
                    return result
                return redirect(url_for('tasks.index'))

            # Если обработчик добавил ошибки вручную (например, дубликаты)
            if getattr(form, 'errors', None):
                if is_ajax_req:
                    error_text = first_error(form, 'Ошибка обработки формы')
                    return bad_request(error_text)
                return redirect(url_for('tasks.index'))

            # Успешный AJAX — JSON по умолчанию, если обработчик сам ничего не вернул
            if is_ajax_req:
                return jsonify({"success": True}), 200
            # Успешный обычный POST — редирект на список
            return redirect(url_for('tasks.index'))

        return wrapped_view
    return decorator