from flask import Blueprint

bp = Blueprint('errors', __name__)
bp.template_folder = 'templates'

from app.errors import handlers