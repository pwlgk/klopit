# app/files/routes.py
import os
from flask import (
    render_template, redirect, url_for, flash, request, abort,
    current_app, send_from_directory
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename 
from app.extensions import db
from app.files import bp
from app.models import File, Task, Project # Импортируем модели

# --- Загрузка Файла (Привязка к ЗАДАЧЕ) ---
@bp.route('/upload/task/<int:task_id>', methods=['POST'])
@login_required
def upload_task_file(task_id):
    task = Task.query.get_or_404(task_id)
    project = task.project

    # --- Проверка прав ---
    # Загружать может владелец проекта или исполнитель задачи
    if project.owner_id != current_user.id and task.assignee_id != current_user.id:
        abort(403)

    # Проверяем, есть ли файл в запросе
    if 'file' not in request.files:
        flash('Файл не найден в запросе.', 'warning')
        return redirect(request.referrer or url_for('projects.view_project', project_id=project.id))

    file = request.files['file']

    # Если пользователь не выбрал файл, браузер может отправить пустое имя
    if file.filename == '':
        flash('Файл не выбран.', 'warning')
        return redirect(request.referrer or url_for('projects.view_project', project_id=project.id))

    # Проверяем файл и сохраняем
    if file and File.is_allowed(file.filename):
        original_fname = file.filename
        storage_fname = File.generate_storage_filename(original_fname)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], storage_fname)

        try:
            # Создаем папку uploads, если её нет
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            # Сохраняем файл на диск
            file.save(filepath)

            # Создаем запись в БД
            db_file = File(storage_filename=storage_fname,
                           original_filename=original_fname,
                           user_id=current_user.id,
                           task_id=task.id) # Привязываем к задаче
            db.session.add(db_file)
            db.session.commit()
            flash(f'Файл "{original_fname}" успешно загружен.', 'success')

        except Exception as e:
            db.session.rollback()
            # Удаляем частично загруженный файл, если он есть
            if os.path.exists(filepath):
                os.remove(filepath)
            flash(f'Ошибка при загрузке файла: {e}', 'danger')
            print(f"File Upload Error: {e}") # Логирование ошибки
            import traceback
            traceback.print_exc()

    else:
        # Если расширение не разрешено
        allowed_ext_str = ", ".join(current_app.config.get('ALLOWED_EXTENSIONS', []))
        flash(f'Недопустимый тип файла. Разрешены: {allowed_ext_str}', 'warning')

    # Возвращаемся на страницу проекта
    return redirect(url_for('projects.view_project', project_id=project.id))


# --- Скачивание Файла ---
@bp.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    file_record = File.query.get_or_404(file_id)

    # --- Проверка прав ---
    # Доступ имеет владелец проекта, исполнитель задачи (если файл к задаче), или загрузивший пользователь
    can_access = False
    if file_record.task: # Файл привязан к задаче
        project = file_record.task.project
        if project.owner_id == current_user.id or \
           file_record.task.assignee_id == current_user.id or \
           file_record.user_id == current_user.id:
           can_access = True
    elif file_record.project: # Файл привязан к проекту (позже)
        project = file_record.project
        if project.owner_id == current_user.id or \
           file_record.user_id == current_user.id: # Или участники проекта позже
           can_access = True
    elif file_record.user_id == current_user.id: # Файл не привязан, но загружен пользователем
         can_access = True # Возможно, такое не должно быть разрешено

    if not can_access:
        abort(403)

    # Используем send_from_directory для безопасной отправки файла
    try:
        return send_from_directory(
            current_app.config['UPLOAD_FOLDER'],
            file_record.storage_filename,
            as_attachment=True, # Скачать как вложение
            download_name=file_record.original_filename # Использовать оригинальное имя
        )
    except FileNotFoundError:
        abort(404, description="Файл не найден на сервере.")


# --- Удаление Файла ---
@bp.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    file_record = File.query.get_or_404(file_id)

    # --- Проверка прав ---
    # Удалять может владелец проекта, к которому относится файл (через задачу), или сам загрузивший
    can_delete = False
    project_id_redirect = None
    if file_record.task:
        project = file_record.task.project
        project_id_redirect = project.id
        if project.owner_id == current_user.id or file_record.user_id == current_user.id:
            can_delete = True
    elif file_record.project: # Если файл к проекту
        project = file_record.project
        project_id_redirect = project.id
        if project.owner_id == current_user.id or file_record.user_id == current_user.id:
            can_delete = True
    elif file_record.user_id == current_user.id: # Если не привязан
         can_delete = True 

    if not can_delete:
        abort(403)

    original_fname = file_record.original_filename
    filepath = file_record.filepath

    try:
        # Сначала удаляем запись из БД
        db.session.delete(file_record)
        db.session.commit() # Коммитим удаление из БД

        # Затем удаляем физический файл
        if os.path.exists(filepath):
            os.remove(filepath)
            flash(f'Файл "{original_fname}" успешно удален.', 'success')
        else:
            flash(f'Запись о файле "{original_fname}" удалена, но сам файл не найден на сервере.', 'warning')

    except Exception as e:
        # Если удаление из БД прошло, но удаление файла - нет, откатывать БД не нужно
        # Если ошибка при удалении из БД, откатываем
        db.session.rollback()
        flash(f'Ошибка при удалении файла: {e}', 'danger')
        print(f"File Deletion Error: {e}") # Логирование ошибки
        import traceback
        traceback.print_exc()

    # Редирект обратно на страницу проекта (или задачи)
    if project_id_redirect:
         return redirect(url_for('projects.view_project', project_id=project_id_redirect))
    else:
        # Если не знаем куда, идем на dashboard (или обработать лучше)
        return redirect(request.referrer or url_for('dashboard.index'))