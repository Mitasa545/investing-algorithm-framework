from flask_sqlalchemy import SQLAlchemy
from flask import Flask

db = SQLAlchemy()


def create_all_tables():
    db.create_all()


def initialize_db(app: Flask):
    db.init_app(app)
    db.app = app

from investing_algorithm_framework.core.models.order_side import OrderSide
from investing_algorithm_framework.core.models.time_unit import TimeUnit
from investing_algorithm_framework.core.models.portfolio import Portfolio
from investing_algorithm_framework.core.models.position import Position
from investing_algorithm_framework.core.models.order import Order

__all__ = [
    "db",
    "Portfolio",
    "Position",
    'Order',
    'OrderSide',
    "TimeUnit",
    "create_all_tables",
    "initialize_db"
]
