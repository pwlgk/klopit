# app/files/__init__.py
from flask import Blueprint

bp = Blueprint('files', __name__)

from app.files import routes