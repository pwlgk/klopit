# app/reports/__init__.py
from flask import Blueprint

bp = Blueprint('reports', __name__, template_folder='templates')

from app.reports import routes # Импорт в конце