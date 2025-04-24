# app/files/__init__.py
from flask import Blueprint

bp = Blueprint('files', __name__) # Префикс URL зададим при регистрации

from app.files import routes