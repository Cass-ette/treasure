"""语言切换接口."""
from flask import Blueprint, request, jsonify

bp = Blueprint('locale', __name__)


@bp.route('/locale/set', methods=['POST'])
def set_locale():
    lang = request.form.get('lang')
    if lang not in ('zh', 'en'):
        return jsonify(ok=False, error='invalid lang'), 400
    resp = jsonify(ok=True)
    resp.set_cookie('locale', lang, max_age=365 * 24 * 3600, samesite='Lax')
    return resp
