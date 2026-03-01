"""Step 2 tests: model layer"""
import pytest


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


def test_user_model(db_session):
    from app.models import User
    from werkzeug.security import generate_password_hash
    u = User(username='tester', password=generate_password_hash('pass', method='pbkdf2:sha256'), is_main_account=True)
    db_session.session.add(u)
    db_session.session.commit()
    found = User.query.filter_by(username='tester').first()
    assert found is not None
    assert found.is_main_account is True
    assert found.principal == 0.0


def test_fund_model(db_session):
    from app.models import Fund
    from datetime import datetime
    f = Fund(code='000001', name='测试基金', fund_type='混合型', latest_nav=1.5678, nav_date=datetime.now())
    db_session.session.add(f)
    db_session.session.commit()
    found = Fund.query.filter_by(code='000001').first()
    assert found.name == '测试基金'
    assert found.latest_nav == 1.5678


def test_position_model(db_session):
    from app.models import User, Fund, Position
    from werkzeug.security import generate_password_hash
    from datetime import datetime
    u = User(username='u1', password=generate_password_hash('p', method='pbkdf2:sha256'))
    f = Fund(code='000002', name='基金B', nav_date=datetime.now())
    db_session.session.add_all([u, f])
    db_session.session.commit()
    p = Position(user_id=u.id, fund_id=f.id, shares=1000.0, cost_price=1.23)
    db_session.session.add(p)
    db_session.session.commit()
    assert Position.query.count() == 1
    assert Position.query.first().shares == 1000.0


def test_fund_nav_history_model(db_session):
    from app.models import Fund, FundNavHistory
    from datetime import datetime
    f = Fund(code='000003', name='基金C', nav_date=datetime.now())
    db_session.session.add(f)
    db_session.session.commit()
    h = FundNavHistory(fund_id=f.id, nav=1.234, date=datetime(2025, 1, 1))
    db_session.session.add(h)
    db_session.session.commit()
    assert FundNavHistory.query.count() == 1


def test_all_models_importable():
    from app.models import User, Fund, Position, Profit, FundNavHistory, Transaction, Agreement
    assert all([User, Fund, Position, Profit, FundNavHistory, Transaction, Agreement])
