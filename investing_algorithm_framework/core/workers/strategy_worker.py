from flask_apscheduler import APScheduler

from investing_algorithm_framework.core.exceptions import OperationalException
from investing_algorithm_framework.core.models import TimeUnit, db, \
    TradingDataTypes
from investing_algorithm_framework.utils import random_string


class Strategy:

    def __init__(
        self,
        decorated=None,
        worker_id=None,
        time_unit=None,
        interval=None,
        data_provider_identifier=None,
        trading_data_type=None,
        trading_data_types=None,
        target_symbol=None,
        target_symbols=None,
        trading_symbol=None,
    ):
        self.data_provider_identifier = data_provider_identifier
        self.trading_data_types = trading_data_types
        self.target_symbol = target_symbol
        self.target_symbols = target_symbols
        self.trading_symbol = trading_symbol
        self.trading_data_type = None
        self.trading_data_types = None

        if trading_data_type is not None:
            self.trading_data_type = TradingDataTypes\
                .from_value(trading_data_type)

        if trading_data_types is not None:
            types = [TradingDataTypes.from_value(trading_data_type)
                     for trading_data_type in trading_data_types]

            self.trading_data_types = types

        from investing_algorithm_framework.core.context import algorithm

        self.decorated = decorated
        self.worker_id = worker_id

        if self.worker_id is None:

            if self.decorated:
                self.worker_id = self.decorated.__name__

                if self.decorated.__name__ in algorithm.workers:
                    self.id = random_string(10)
            else:
                self.id = random_string(10)

        if time_unit is None:
            raise OperationalException(
                "Time unit for strategy is not specified"
            )

        if isinstance(time_unit, TimeUnit):
            self.time_unit = time_unit.value
        else:
            self.time_unit = TimeUnit.from_string(time_unit).value

        if interval is None:
            raise OperationalException(
                "Time interval for strategy is not specified"
            )

        self.interval = interval

        if self.target_symbol is None and self.target_symbols is None \
                and (self.trading_data_type is not None
                     or self.trading_data_types is not None):
            raise OperationalException(
                "No target symbol or target symbols specified "
                "for trading data type"
            )

        algorithm.add_strategy(self)

    def add_to_scheduler(self, app_scheduler: APScheduler):
        if TimeUnit.SECONDS.equals(self.time_unit):
            app_scheduler.add_job(
                id=self.worker_id,
                name=self.worker_id,
                func=self.__call__,
                trigger="interval",
                seconds=self.interval
            )
        elif TimeUnit.MINUTE.equals(self.time_unit):
            app_scheduler.add_job(
                id=self.worker_id,
                name=self.worker_id,
                func=self.__call__,
                trigger="interval",
                minutes=self.interval
            )
        elif TimeUnit.HOUR.equals(self.time_unit):
            app_scheduler.add_job(
                id=self.worker_id,
                name=self.worker_id,
                func=self.__call__,
                trigger="interval",
                minutes=(self.interval * 60)
            )

    def run_strategy(
        self,
        algorithm_context,
        ticker,
        tickers,
        order_book,
        order_books,
        **kwargs
    ):
        raise NotImplementedError("Run strategy method is not implemented")

    def __call__(
        self,
        time_unit: TimeUnit = TimeUnit.MINUTE.value,
        interval=10,
        data_provider_identifier=None,
        trading_data_type=None,
        trading_data_types=None,
        target_symbol=None,
        target_symbols=None,
        trading_symbol=None
    ):
        from investing_algorithm_framework import current_app as app
        data = {}

        if self.data_provider_identifier is not None:
            data = app.algorithm.get_data(
                data_provider_identifier=self.data_provider_identifier,
                trading_data_type=self.trading_data_type,
                trading_data_types=self.trading_data_types,
                target_symbols=self.target_symbols,
                target_symbol=self.target_symbol,
                trading_symbol=self.trading_symbol
            )

        # Run the decorated function in app context
        with db.app.app_context():

            if self.decorated:

                if data is not None:
                    self.decorated(app.algorithm, **data)
                else:
                    self.decorated(app.algorithm)
            else:
                self.run_strategy(app.algorithm, **data)
