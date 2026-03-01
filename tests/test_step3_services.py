"""Step 3 & 4 tests: services and utils"""
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


def test_allowed_file_valid():
    from app.utils.helpers import allowed_file
    assert allowed_file('photo.jpg') is True
    assert allowed_file('image.PNG') is True
    assert allowed_file('file.gif') is True


def test_allowed_file_invalid():
    from app.utils.helpers import allowed_file
    assert allowed_file('doc.pdf') is False
    assert allowed_file('noextension') is False
    assert allowed_file('script.exe') is False


def test_is_market_day_weekend():
    from app.services.fund_service import FundService
    from datetime import date
    sat = date(2024, 1, 6)   # 周六
    sun = date(2024, 1, 7)   # 周日
    assert FundService.is_market_day(sat) is False
    assert FundService.is_market_day(sun) is False


def test_is_market_day_weekday():
    from app.services.fund_service import FundService
    from datetime import date
    mon = date(2024, 1, 8)   # 周一（非节假日）
    assert FundService.is_market_day(mon) is True


def test_calculate_returns_no_positions(db_session):
    """calculate_returns 在无持仓时不报错"""
    from app.services.calculation import calculate_returns
    from app.models import Fund
    from datetime import datetime
    f = Fund(code='888888', name='测试', nav_date=datetime.now())
    db_session.session.add(f)
    db_session.session.commit()
    # 不应抛出异常
    calculate_returns(f.id, 1.0, 1.1, _db=db_session)


def test_calculation_service_importable():
    from app.services.calculation import CalculationService
    assert CalculationService is not None


def test_scheduler_importable():
    from app.services.scheduler import start_scheduler, batch_update_all_funds
    assert callable(start_scheduler)
    assert callable(batch_update_all_funds)
