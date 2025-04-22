from flask import render_template, request
from app import db
from app.errors import bp
from app.api.errors import error_responce as api_error_responce

def wants_json_responce():
    return request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']

@bp.errorhandler(404)
def not_found_error(error):
    if wants_json_responce():
        return api_error_responce(404)
    return render_template('404.html'), 404

@bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if wants_json_responce():
        return api_error_responce(500)
    return render_template('500.html'), 500