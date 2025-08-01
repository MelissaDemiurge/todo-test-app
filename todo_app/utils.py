from flask import request, redirect, url_for

def ajax_required(FormClass):
    def decorator(view_func):
        def wrapped_view(*args, **kwargs):
            form = FormClass()
            if form.validate_on_submit():
                return view_func(form, *args, **kwargs) or redirect(url_for('tasks.index'))
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return '', 204
                return redirect(url_for('tasks.index'))
        wrapped_view.__name__ = view_func.__name__
        return wrapped_view
    return decorator