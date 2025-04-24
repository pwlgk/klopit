# app/projects/routes.py
from flask import (
    render_template, redirect, url_for, flash, request, abort,
    current_app # Хотя current_app больше не нужен в шаблонах, оставим на всякий случай
)
from flask_login import login_required, current_user
from sqlalchemy import or_ # Для сложных запросов SQLAlchemy
from app.extensions import db
from app.projects import bp
from app.models import ( # Импортируем все нужные модели и Enum
    Project, Task, User, Role, File, Comment,
    TaskStatus, TaskPriority, project_members
)
from app.projects.forms import ( # Импортируем все нужные формы
    ProjectForm, TaskForm, CommentForm, AddMemberForm
)
from app.utils.notifications import ( # Импортируем функции уведомлений
    notify_task_assigned, notify_new_comment, notify_user_added_to_project
)
import traceback # Для отладки ошибок

# === Маршруты Проектов ===

@bp.route('/')
@login_required
def list_projects():
    """Отображает список проектов, где пользователь владелец или участник."""
    # Эффективный запрос для получения всех доступных проектов
    # Используем outerjoin и distinct для корректной работы с many-to-many
    accessible_projects_query = Project.query.outerjoin(
        project_members, (Project.id == project_members.c.project_id)
    ).filter(
        or_(
            Project.owner_id == current_user.id,
            project_members.c.user_id == current_user.id
        )
    ).distinct().order_by(Project.created_at.desc())

    all_accessible_projects = accessible_projects_query.all()

    return render_template('project_list.html', title='Мои проекты', projects=all_accessible_projects)


@bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_project():
    """Обрабатывает создание нового проекта."""
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(name=form.name.data,
                          description=form.description.data,
                          owner_id=current_user.id) # Владелец - текущий пользователь
        # Владелец автоматически становится участником (опционально, но логично)
        # project.members.append(current_user) # Можно добавить, если нужно
        try:
            db.session.add(project)
            db.session.commit()
            flash(f'Проект "{project.name}" успешно создан!', 'success')
            return redirect(url_for('projects.view_project', project_id=project.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при создании проекта: {e}', 'danger')
            print(f"Create project error: {e}")
            traceback.print_exc()

    # Отображаем шаблон с формой (для GET или если форма не валидна)
    return render_template('create_project.html', title='Новый проект', form=form)


@bp.route('/<int:project_id>')
@login_required
def view_project(project_id):
    """Отображает детали конкретного проекта."""
    project = Project.query.get_or_404(project_id)

    # Проверка доступа (владелец или участник)
    if not current_user.can_access_project(project):
        abort(403)

    tasks = project.tasks.order_by(Task.status.asc(), Task.priority.desc(), Task.created_at.desc()).all()
    project_members = project.members.order_by(User.username).all()

    # Создаем экземпляры форм для передачи в шаблон
    comment_form = CommentForm()
    add_member_form = AddMemberForm()

    return render_template('project_detail.html',
                           title=project.name,
                           project=project,
                           tasks=tasks,
                           project_members=project_members,
                           comment_form=comment_form,
                           add_member_form=add_member_form
                           )


@bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    """Обрабатывает редактирование существующего проекта."""
    project = Project.query.get_or_404(project_id)

    # ТОЛЬКО Владелец может редактировать проект
    if project.owner_id != current_user.id:
        abort(403)

    form = ProjectForm(obj=project) # Заполняем форму текущими данными проекта

    if form.validate_on_submit():
        project.name = form.name.data
        project.description = form.description.data
        try:
            db.session.commit() # Сохраняем изменения в БД
            flash(f'Проект "{project.name}" успешно обновлен!', 'success')
            return redirect(url_for('projects.view_project', project_id=project.id))
        except Exception as e:
             db.session.rollback()
             flash(f'Ошибка при обновлении проекта: {e}', 'danger')
             print(f"Edit project error: {e}")
             traceback.print_exc()

    # Отображаем шаблон с формой (для GET или если форма не валидна)
    form_action = url_for('projects.edit_project', project_id=project.id)
    return render_template('edit_project.html', title=f'Редактирование: {project.name}',
                           form=form, project=project, form_action=form_action)


@bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    """Обрабатывает удаление проекта."""
    project = Project.query.get_or_404(project_id)

     # ТОЛЬКО Владелец может удалять проект
    if project.owner_id != current_user.id:
        abort(403)

    project_name = project.name
    try:
        # Удаляем проект (связанные задачи, файлы, комменты удалятся через cascade)
        # Записи в project_members удалятся через cascade
        db.session.delete(project)
        db.session.commit()
        flash(f'Проект "{project_name}" был удален.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении проекта: {e}', 'danger')
        print(f"Delete project error: {e}")
        traceback.print_exc()
        return redirect(url_for('projects.view_project', project_id=project_id)) # Вернуть на страницу проекта в случае ошибки

    # Перенаправляем на список проектов
    return redirect(url_for('projects.list_projects'))


# === Маршруты Задач ===

@bp.route('/<int:project_id>/tasks/new', methods=['GET', 'POST'])
@login_required
def create_task(project_id):
    """Создание новой задачи в рамках проекта."""
    project = Project.query.get_or_404(project_id)

    # Проверка доступа (владелец или участник)
    if not current_user.can_access_project(project):
        abort(403)

    # Фильтруем QuerySelectField для исполнителей
    assignee_query = User.query.filter(
        or_(User.id == project.owner_id, User.projects_member_of.any(Project.id == project.id))
    ).order_by(User.username)

    # Явная инициализация формы в зависимости от метода
    if request.method == 'POST':
        form = TaskForm(request.form)
        form.assignee_id.query = assignee_query # Устанавливаем query для POST
    else: # GET request
        form = TaskForm()
        form.assignee_id.query = assignee_query # Устанавливаем query для GET
        # Ставим значения по умолчанию в .data для GET
        form.status.data = TaskStatus.TODO.name
        form.priority.data = TaskPriority.MEDIUM.name

    print(f"Handling request for create_task (Project ID: {project_id}), Method: {request.method}") # Отладка

    if form.validate_on_submit():
        print(">>> Form validation PASSED") # Отладка
        assignee_user = form.assignee_id.data
        status_name = form.status.data
        priority_name = form.priority.data
        print(f"    Status Name: {status_name}, Priority Name: {priority_name}") # Отладка

        try:
            # Преобразуем строки обратно в Enum
            status_enum = TaskStatus[status_name]
            priority_enum = TaskPriority[priority_name]

            task = Task(title=form.title.data,
                        description=form.description.data,
                        status=status_enum,
                        priority=priority_enum,
                        due_date=form.due_date.data,
                        project_id=project.id,
                        creator_id=current_user.id,
                        assignee_id=assignee_user.id if assignee_user else None)

            print(f"    Task object to save: {task.__dict__}") # Отладка
            db.session.add(task)
            db.session.flush() # Получаем ID для уведомления

            # Отправка уведомления о назначении (если назначен исполнитель)
            if task.assignee_id:
                # assignee_user уже содержит объект User
                notify_task_assigned(task, current_user, assignee_user)

            db.session.commit() # Коммитим все вместе
            print(">>> DB commit SUCCESSFUL") # Отладка
            flash(f'Задача "{task.title}" успешно создана!', 'success')
            return redirect(url_for('projects.view_project', project_id=project.id))

        except KeyError:
            print(f"!!! KeyError: Invalid Enum name received: status='{status_name}', priority='{priority_name}'") # Отладка
            flash('Получено неверное значение статуса или приоритета.', 'danger')
        except Exception as e:
            db.session.rollback()
            print(f"!!! DB Error on commit: {e}", flush=True) # Отладка
            traceback.print_exc() # Отладка
            flash(f'Ошибка при сохранении задачи: {e}', 'danger')

    elif request.method == 'POST': # Валидация не прошла
        print(">>> Form validation FAILED") # Отладка
        print(f"    Form errors: {form.errors}") # Отладка

    print("Rendering create_task.html template") # Отладка
    return render_template('create_task.html', title='Новая задача', form=form, project=project)


@bp.route('/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    """Редактирование существующей задачи."""
    task = Task.query.get_or_404(task_id)
    project = task.project

    # Проверка доступа (владелец или участник)
    # (Можно добавить и исполнителя: or task.assignee_id == current_user.id)
    if not current_user.can_access_project(project):
        abort(403)

    # Сохраняем старого исполнителя ДО обновления
    old_assignee_id = task.assignee_id

    # Фильтруем QuerySelectField для исполнителей
    assignee_query = User.query.filter(
        or_(User.id == project.owner_id, User.projects_member_of.any(Project.id == project.id))
    ).order_by(User.username)

    # Явная инициализация формы в зависимости от метода
    if request.method == 'POST':
        # Инициализируем из POST, но сохраняем obj для возможного рендеринга при ошибке
        form = TaskForm(request.form, obj=task)
        form.assignee_id.query = assignee_query # Устанавливаем query для POST
    else: # GET request
         # Инициализируем из объекта БД для GET
        form = TaskForm(obj=task)
        form.assignee_id.query = assignee_query # Устанавливаем query для GET
        # Устанавливаем текущего исполнителя для QuerySelectField
        form.assignee_id.data = task.assignee

    print(f"Handling request for edit_task (Task ID: {task_id}), Method: {request.method}") # Отладка

    if form.validate_on_submit():
        print(">>> Form validation PASSED (Edit)") # Отладка
        assignee_user = form.assignee_id.data
        status_name = form.status.data
        priority_name = form.priority.data
        print(f"    Status Name (Edit): {status_name}, Priority Name (Edit): {priority_name}") # Отладка

        try:
            # Преобразуем строки обратно в Enum
            status_enum = TaskStatus[status_name]
            priority_enum = TaskPriority[priority_name]

            # Обновляем поля задачи
            task.title = form.title.data
            task.description = form.description.data
            task.status = status_enum
            task.priority = priority_enum
            task.due_date = form.due_date.data
            new_assignee_id = assignee_user.id if assignee_user else None
            task.assignee_id = new_assignee_id

            print(f"    Task object to update: {task.__dict__}") # Отладка

            # Отправка уведомления, если исполнитель ИЗМЕНИЛСЯ и он НЕ старый
            if new_assignee_id != old_assignee_id and new_assignee_id is not None:
                 notify_task_assigned(task, current_user, assignee_user)

            db.session.commit() # Коммитим все изменения
            print(">>> DB commit SUCCESSFUL (Edit)") # Отладка
            flash(f'Задача "{task.title}" успешно обновлена!', 'success')
            return redirect(url_for('projects.view_project', project_id=project.id))

        except KeyError:
            print(f"!!! KeyError (Edit): Invalid Enum name received: status='{status_name}', priority='{priority_name}'") # Отладка
            flash('Получено неверное значение статуса или приоритета.', 'danger')
        except Exception as e:
            db.session.rollback()
            print(f"!!! DB Error on commit (Edit): {e}", flush=True) # Отладка
            traceback.print_exc() # Отладка
            flash(f'Ошибка при обновлении задачи: {e}', 'danger')

    elif request.method == 'POST': # Валидация не прошла
        print(">>> Form validation FAILED (Edit)") # Отладка
        print(f"    Form errors: {form.errors}") # Отладка

    print("Rendering edit_task.html template") # Отладка
    # Передаем form_action всегда, т.к. рендеринг может быть и после POST
    form_action = url_for('projects.edit_task', task_id=task.id)
    return render_template('edit_task.html', title=f'Редактирование: {task.title}',
                           form=form, task=task, project=project, form_action=form_action)


@bp.route('/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    """Удаление задачи."""
    task = Task.query.get_or_404(task_id)
    project = task.project

    # Проверка доступа (владелец или участник)
    # (Можно изменить на: if project.owner_id != current_user.id)
    if not current_user.can_access_project(project):
        abort(403)

    project_id = task.project_id # Сохраняем ID проекта для редиректа
    task_title = task.title
    try:
        db.session.delete(task)
        db.session.commit()
        flash(f'Задача "{task_title}" удалена.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении задачи: {e}', 'danger')
        print(f"Delete task error: {e}")
        traceback.print_exc()

    return redirect(url_for('projects.view_project', project_id=project_id))


# --- Маршрут для добавления комментария к задаче ---
@bp.route('/task/<int:task_id>/comment', methods=['POST'])
@login_required
def add_comment(task_id):
    task = Task.query.get_or_404(task_id)
    project = task.project

    # Проверка прав (владелец или участник)
    if not current_user.can_access_project(project):
        flash('У вас нет прав для комментирования этой задачи.', 'warning')
        return redirect(request.referrer or url_for('projects.view_project', project_id=project.id))

    # Инициализируем форму данными из запроса
    form = CommentForm(request.form)

    if form.validate(): # Используем validate(), т.к. метод POST
        comment = Comment(body=form.body.data,
                          user_id=current_user.id,
                          task_id=task.id)
        try:
            db.session.add(comment)
            db.session.flush() # Получаем comment.id и можем достучаться до comment.author

            # Отправка уведомлений о комментарии
            notify_new_comment(comment, task)

            db.session.commit() # Коммитим все
            flash('Комментарий добавлен.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при добавлении комментария: {e}', 'danger')
            print(f"Comment Add Error: {e}")
            traceback.print_exc()
    else:
        # Если форма не валидна, выводим ошибки
        for field, errors in form.errors.items():
            for error in errors:
                # Можно извлечь label поля, если оно определено в форме
                # label = getattr(form, field).label.text if hasattr(getattr(form, field), 'label') else field
                flash(f"Ошибка в комментарии: {error}", 'danger') # Упрощенный вывод

    # Перенаправляем обратно на страницу проекта, к якорю задачи
    return redirect(url_for('projects.view_project', project_id=project.id, _anchor=f'task-{task.id}'))


# --- ОПЦИОНАЛЬНО: Быстрое изменение статуса (например, для Kanban) ---
@bp.route('/tasks/<int:task_id>/status', methods=['POST'])
@login_required
def update_task_status(task_id):
    """Обновляет статус задачи через AJAX (ожидает JSON)."""
    task = Task.query.get_or_404(task_id)
    project = task.project

    # Права доступа (владелец, участник или исполнитель)
    if not current_user.can_access_project(project) and task.assignee_id != current_user.id:
        abort(403)

    # Ожидаем JSON вида {"status": "IN_PROGRESS"}
    if not request.is_json:
         abort(415, description="Ожидается JSON запрос.") # Unsupported Media Type

    new_status_name = request.json.get('status')
    if not new_status_name:
         abort(400, description="Отсутствует поле 'status' в JSON.") # Bad Request

    try:
        new_status_enum = TaskStatus[new_status_name] # Преобразуем имя статуса в Enum
        task.status = new_status_enum
        db.session.commit()
        # Возвращаем JSON ответ
        return {'message': 'Статус обновлен', 'new_status_name': new_status_enum.name, 'new_status_value': new_status_enum.value}, 200
    except KeyError:
        abort(400, description=f"Неверный статус: '{new_status_name}'")
    except Exception as e:
        db.session.rollback()
        print(f"Update task status error: {e}")
        traceback.print_exc()
        abort(500, description="Ошибка при обновлении статуса задачи.") # Internal Server Error


# === Маршруты Управления Участниками ===

@bp.route('/<int:project_id>/members/add', methods=['POST'])
@login_required
def add_member(project_id):
    """Добавление участника в проект по Email."""
    project = Project.query.get_or_404(project_id)

    # ТОЛЬКО Владелец может добавлять
    if project.owner_id != current_user.id:
        abort(403)

    form = AddMemberForm(request.form) # Берем email из формы

    if form.validate():
        user_to_add = User.query.filter(User.email.ilike(form.email.data)).first() # Регистронезависимый поиск

        if not user_to_add:
            flash(f'Пользователь с email {form.email.data} не найден.', 'warning')
        elif user_to_add.id == project.owner_id:
             flash('Владелец проекта уже является участником.', 'info')
        # Проверяем, является ли уже участником
        elif user_to_add.is_member_of(project):
             flash(f'Пользователь {user_to_add.username} уже является участником проекта.', 'info')
        else:
            # Добавляем пользователя в участники
            project.members.append(user_to_add)
            try:
                # Отправка уведомления пользователю
                notify_user_added_to_project(user_to_add, project, current_user)
                db.session.commit() # Коммитим все
                flash(f'Пользователь {user_to_add.username} добавлен в проект.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Ошибка при добавлении участника: {e}', 'danger')
                print(f"Add member error: {e}")
                traceback.print_exc()
    else:
         # Вывод ошибок валидации формы
        for field, errors in form.errors.items():
            for error in errors:
                 # label = getattr(form, field).label.text if hasattr(getattr(form, field), 'label') else field
                flash(f"Ошибка в email: {error}", 'danger') # Упрощенный вывод

    return redirect(url_for('projects.view_project', project_id=project.id, _anchor='members'))


@bp.route('/<int:project_id>/members/<int:user_id>/remove', methods=['POST'])
@login_required
def remove_member(project_id, user_id):
    """Удаление участника из проекта."""
    project = Project.query.get_or_404(project_id)

    # ТОЛЬКО Владелец может удалять
    if project.owner_id != current_user.id:
        abort(403)

    # Нельзя удалить самого владельца
    if user_id == project.owner_id:
         flash('Нельзя удалить владельца из проекта.', 'warning')
         return redirect(url_for('projects.view_project', project_id=project.id, _anchor='members'))

    # Ищем пользователя среди участников
    user_to_remove = project.members.filter(project_members.c.user_id == user_id).first()

    if user_to_remove:
        project.members.remove(user_to_remove)
        try:
            # TODO: Нужно ли уведомление об удалении?
            db.session.commit()
            flash(f'Пользователь {user_to_remove.username} удален из проекта.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при удалении участника: {e}', 'danger')
            print(f"Remove member error: {e}")
            traceback.print_exc()
    else:
        flash('Указанный пользователь не является участником этого проекта.', 'warning')

    return redirect(url_for('projects.view_project', project_id=project.id, _anchor='members'))