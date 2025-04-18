
from flask import Blueprint

bp = Blueprint('auth', __name__)
bp.template_folder = 'templates'

from app.auth import routers