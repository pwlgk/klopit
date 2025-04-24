# app/reports/routes.py
from flask import render_template, abort, current_app, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, case, or_ # Добавили or_
from app.reports import bp
from app.models import Project, Task, TaskStatus, TaskPriority, User # Добавили User
from app.extensions import db
import json # Для безопасной передачи данных в JS

@bp.route('/')
@login_required
def index():
    """Главная страница раздела отчетов."""
    # Получаем список проектов, доступных пользователю
    projects = Project.query.filter(
        or_(Project.owner_id == current_user.id, Project.members.any(User.id == current_user.id))
    ).order_by(Project.name).all()
    return render_template('reports_index.html', title='Отчеты', projects=projects)


@bp.route('/project/<int:project_id>')
@login_required
def project_report(project_id):
    """Отображает статистику и графики по задачам для конкретного проекта."""
    project = Project.query.get_or_404(project_id)

    # --- Проверка прав доступа ---
    # Отчет доступен владельцу или участнику проекта
    if not current_user.can_access_project(project):
        abort(403) # Запрещаем доступ

    # --- Сбор статистики ---
    # 1. По статусам
    status_stats_query = db.session.query(
            Task.status, func.count(Task.id).label('count')
        ).filter(
            Task.project_id == project.id
        ).group_by(
            Task.status
        ).all()

    status_stats = {status: 0 for status in TaskStatus} # Инициализируем нулями
    total_tasks = 0
    for status_enum, count in status_stats_query:
        if status_enum in status_stats: # Убедимся, что статус из Enum
            status_stats[status_enum] = count
        total_tasks += count # Считаем общее количество

    # 2. По приоритетам
    priority_stats_query = db.session.query(
            Task.priority, func.count(Task.id).label('count')
         ).filter(
             Task.project_id == project.id
         ).group_by(
             Task.priority
         ).all()

    priority_stats = {prio: 0 for prio in TaskPriority} # Инициализируем нулями
    for prio_enum, count in priority_stats_query:
         if prio_enum in priority_stats: # Убедимся, что приоритет из Enum
            priority_stats[prio_enum] = count
        # total_tasks уже посчитан выше

    # 3. Рассчитаем процент выполнения (если есть задачи)
    completion_percentage = 0
    if total_tasks > 0:
        done_count = status_stats.get(TaskStatus.DONE, 0)
        completion_percentage = round((done_count / total_tasks) * 100)

    # --- Подготовка данных для JS (графики) ---
    # Используем имена Enum как ключи и значения Enum для меток
    chart_status_data = {s.name: status_stats.get(s, 0) for s in TaskStatus}
    chart_priority_data = {p.name: priority_stats.get(p, 0) for p in TaskPriority}
    status_enum_values = {s.name: s.value for s in TaskStatus}
    priority_enum_values = {p.name: p.value for p in TaskPriority}

    # Передаем все данные в шаблон
    return render_template('project_report.html',
                           title=f'Отчет по проекту: {project.name}',
                           project=project,
                           stats=status_stats, # Статистика для таблицы
                           total_tasks=total_tasks,
                           completion_percentage=completion_percentage,
                           # --- Данные для графиков Chart.js ---
                           # Безопасно передаем через json.dumps или фильтр |tojson
                           chart_status_data_json=json.dumps(chart_status_data),
                           chart_priority_data_json=json.dumps(chart_priority_data),
                           status_enum_values_json=json.dumps(status_enum_values),
                           priority_enum_values_json=json.dumps(priority_enum_values)
                           )

