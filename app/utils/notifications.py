# app/utils/notifications.py
from app.models import Notification, User
from app.extensions import db
from flask import url_for

def add_notification(recipient_id, message, related_url=None):
    """Создает и сохраняет уведомление для пользователя."""
    if not recipient_id:
        print("WARNING: Tried to send notification without recipient_id")
        return

    # Проверяем, существует ли пользователь (опционально, но полезно)
    recipient = User.query.get(recipient_id)
    if not recipient:
        print(f"WARNING: Recipient user with ID {recipient_id} not found for notification.")
        return

    try:
        notification = Notification(user_id=recipient_id,
                                    message=message,
                                    related_url=related_url)
        db.session.add(notification)
        print(f"Notification created for User {recipient_id}: {message}") # Отладка
    except Exception as e:
        print(f"ERROR creating notification for User {recipient_id}: {e}")

# --- Примеры сообщений ---
def notify_task_assigned(task, assigner, assignee):
    """Уведомляет пользователя о назначении задачи."""
    if assignee and assigner.id != assignee.id: # Не уведомляем себя
        msg = f"Пользователь @{assigner.username} назначил вам задачу: '{task.title}'"
        url = url_for('projects.view_project', project_id=task.project_id, _anchor=f'task-{task.id}')
        add_notification(assignee.id, msg, url)

def notify_new_comment(comment, task):
    """Уведомляет участников задачи о новом комментарии."""
    recipients = set() # Используем set для уникальности ID
    commenter_id = comment.user_id

    # Уведомить владельца проекта (если он не автор комментария)
    if task.project.owner_id != commenter_id:
        recipients.add(task.project.owner_id)

    # Уведомить исполнителя задачи (если назначен и не автор комментария)
    if task.assignee_id and task.assignee_id != commenter_id:
        recipients.add(task.assignee_id)

    # Уведомить создателя задачи (если он не владелец, не исполнитель и не автор комментария)
    if task.creator_id not in [task.project.owner_id, task.assignee_id, commenter_id]:
         recipients.add(task.creator_id)


    msg = f"Новый комментарий от @{comment.author.username} к задаче '{task.title}'"
    url = url_for('projects.view_project', project_id=task.project_id, _anchor=f'task-{task.id}')

    for user_id in recipients:
        add_notification(user_id, msg, url)


def notify_user_added_to_project(user_added, project, adder):
    """Уведомляет пользователя о добавлении в проект."""
    if user_added.id != adder.id: # Не уведомляем того, кто добавлял
        msg = f"Пользователь @{adder.username} добавил вас в проект '{project.name}'"
        url = url_for('projects.view_project', project_id=project.id)
        add_notification(user_added.id, msg, url)