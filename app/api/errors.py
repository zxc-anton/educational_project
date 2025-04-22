from werkzeug.http import HTTP_STATUS_CODES
from app.api import bp
from werkzeug.exceptions import HTTPException

def error_responce(status_code, message=None):
    payload = {'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error')}
    if message:
        payload['message'] = message
    return payload, status_code

@bp.errorhandler(HTTPException)
def handle_exception(e):
    return error_responce(e.code)

def bad_request(message):
    return error_responce(400, message)


