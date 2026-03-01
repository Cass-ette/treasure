"""Step 5 & 6 tests: routes and app factory"""
import pytest
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    from app import create_app
    return create_app('app.config.TestConfig')


@pytest.fixture
def db_session(app):
    from app.extensions import db
    with app.app_context():
        db.create_all()
        yield db
        db.session.rollback()
        db.drop_all()


@pytest.fixture
def client(app, db_session):
    return app.test_client()


@pytest.fixture
def admin_user(db_session):
    from app.models import User
    u = User(
        username='admin',
        password=generate_password_hash('admin123', method='pbkdf2:sha256'),
        is_main_account=True,
    )
    db_session.session.add(u)
    db_session.session.commit()
    return u


@pytest.fixture
def logged_in_client(client, admin_user):
    client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    return client


# ── App factory ──────────────────────────────────────────────────────────────

def test_app_creates_successfully(app):
    assert app is not None
    assert app.testing is True


def test_db_creates_tables(db_session):
    from app.models import User, Fund, Position
    # 如果没有抛出异常，说明表创建成功
    assert User.query.count() == 0
    assert Fund.query.count() == 0


# ── Auth blueprint ────────────────────────────────────────────────────────────

def test_login_page_get(client):
    rv = client.get('/login')
    assert rv.status_code == 200
    assert '登录'.encode() in rv.data


def test_login_success(client, admin_user):
    rv = client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    assert rv.status_code == 200


def test_login_wrong_password(client, admin_user):
    rv = client.post('/login', data={'username': 'admin', 'password': 'wrong'}, follow_redirects=True)
    assert '用户名或密码错误'.encode() in rv.data


def test_logout(logged_in_client):
    rv = logged_in_client.get('/logout', follow_redirects=True)
    assert rv.status_code == 200


def test_protected_route_redirects_when_not_logged_in(client):
    rv = client.get('/dashboard', follow_redirects=False)
    assert rv.status_code == 302  # redirect to login


# ── Dashboard blueprint ───────────────────────────────────────────────────────

def test_dashboard_accessible_when_logged_in(logged_in_client):
    rv = logged_in_client.get('/dashboard')
    assert rv.status_code == 200


def test_root_redirects_to_dashboard(logged_in_client):
    rv = logged_in_client.get('/')
    assert rv.status_code == 200  # follows to dashboard


# ── Funds blueprint ───────────────────────────────────────────────────────────

def test_manage_funds_page(logged_in_client):
    rv = logged_in_client.get('/manage_funds')
    assert rv.status_code == 200


def test_crawl_fund_nav_page(logged_in_client):
    rv = logged_in_client.get('/crawl_fund_nav')
    assert rv.status_code == 200


def test_get_fund_info_invalid_code(logged_in_client):
    rv = logged_in_client.get('/get_fund_info?code=abc')
    assert rv.status_code == 200
    import json
    data = json.loads(rv.data)
    assert data['success'] is False


def test_get_fund_30_day_average_missing_id(logged_in_client):
    rv = logged_in_client.get('/get_fund_30_day_average')
    import json
    data = json.loads(rv.data)
    assert data['success'] is False


# ── Positions blueprint ───────────────────────────────────────────────────────

def test_manage_positions_page(logged_in_client):
    rv = logged_in_client.get('/manage_positions')
    assert rv.status_code == 200


# ── Image blueprint ───────────────────────────────────────────────────────────

def test_upload_image_page(logged_in_client):
    rv = logged_in_client.get('/image/upload')
    assert rv.status_code == 200


def test_image_history_page(logged_in_client):
    rv = logged_in_client.get('/image/history')
    assert rv.status_code == 200


# ── Accounts blueprint ────────────────────────────────────────────────────────

def test_update_principal_redirects_get(logged_in_client):
    # POST only route, GET should 405
    rv = logged_in_client.get('/update_sub_account_principal')
    assert rv.status_code == 405


def test_update_principal_non_admin_blocked(client, db_session):
    from app.models import User
    sub = User(
        username='sub1',
        password=generate_password_hash('sub123', method='pbkdf2:sha256'),
        is_main_account=False,
        principal=1000.0,
    )
    db_session.session.add(sub)
    db_session.session.commit()
    client.post('/login', data={'username': 'sub1', 'password': 'sub123'})
    rv = client.post('/update_sub_account_principal', data={'account_id': sub.id, 'principal': '2000'}, follow_redirects=True)
    assert rv.status_code == 200
    # 本金不应被更改
    from app.extensions import db
    with client.application.app_context():
        user = User.query.filter_by(username='sub1').first()
        assert user.principal == 1000.0
