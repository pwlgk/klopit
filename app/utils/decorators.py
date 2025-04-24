# app/utils/decorators.py
from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    """
    Декоратор для view-функций, требующий прав администратора.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            # Если пользователь не аутентифицирован или не админ, возвращаем 403 Forbidden
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Можно добавить другие декораторы, например, для проверки прав на проект/задачу
# def permission_required(permission):
#     def decorator(f):
#         @wraps(f)
#         def decorated_function(*args, **kwargs):
#             if not current_user.can(permission):
#                 abort(403)
#             return f(*args, **kwargs)
#         return decorator
#     return decorator