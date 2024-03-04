import decimal
import logging
from typing import List

from investing_algorithm_framework.domain import OrderStatus, OrderFee, \
    Position, Order, Portfolio, OrderType, OrderSide, ApiException, \
    BACKTESTING_FLAG, BACKTESTING_INDEX_DATETIME, MarketService
from investing_algorithm_framework.services import MarketCredentialService, \
    MarketDataSourceService, PortfolioService, PositionService, TradeService, \
    OrderService, ConfigurationService, StrategyOrchestratorService, \
    PortfolioConfigurationService

logger = logging.getLogger("investing_algorithm_framework")


class Algorithm:

    def __init__(
        self,
        configuration_service,
        portfolio_configuration_service,
        portfolio_service,
        position_service,
        order_service,
        market_service,
        strategy_orchestrator_service,
        market_credential_service,
        market_data_source_service,
        trade_service
    ):
        self.portfolio_service: PortfolioService = portfolio_service
        self.position_service: PositionService = position_service
        self.order_service: OrderService = order_service
        self.market_service: MarketService = market_service
        self.configuration_service: ConfigurationService \
            = configuration_service
        self.portfolio_configuration_service: PortfolioConfigurationService \
            = portfolio_configuration_service
        self.strategy_orchestrator_service: StrategyOrchestratorService \
            = strategy_orchestrator_service
        self._market_data_sources = {}
        self._strategies = []
        self._market_credential_service: MarketCredentialService \
            = market_credential_service
        self._market_data_source_service: MarketDataSourceService \
            = market_data_source_service
        self.trade_service: TradeService = trade_service

    def start(self, number_of_iterations=None, stateless=False):

        if not stateless:
            self.strategy_orchestrator_service.start(
                algorithm=self,
                number_of_iterations=number_of_iterations
            )

    @property
    def config(self):
        return self.configuration_service.config

    @property
    def running(self) -> bool:
        return self.strategy_orchestrator_service.running

    def run_jobs(self):
        self.strategy_orchestrator_service.run_pending_jobs()

    def create_order(
        self,
        target_symbol,
        price,
        order_type,
        order_side,
        amount,
        market=None,
        execute=True,
        validate=True,
        sync=True
    ):
        portfolio = self.portfolio_service.find({"market": market})
        order_data = {
            "target_symbol": target_symbol,
            "price": price,
            "amount": amount,
            "order_type": order_type,
            "order_side": order_side,
            "portfolio_id": portfolio.id,
            "status": OrderStatus.CREATED.value,
            "trading_symbol": portfolio.trading_symbol,
        }

        if BACKTESTING_FLAG in self.configuration_service.config \
                and self.configuration_service.config[BACKTESTING_FLAG]:
            order_data["created_at"] = \
                self.configuration_service.config[BACKTESTING_INDEX_DATETIME]

        return self.order_service.create(
            order_data, execute=execute, validate=validate, sync=sync
        )

    def create_limit_order(
        self,
        target_symbol,
        price,
        order_side,
        amount=None,
        percentage_of_portfolio=None,
        percentage_of_position=None,
        precision=None,
        market=None,
        execute=True,
        validate=True,
        sync=True
    ):
        portfolio = self.portfolio_service.find({"market": market})

        if percentage_of_portfolio is not None:
            if not OrderSide.BUY.equals(order_side):
                raise ApiException(
                    "Percentage of portfolio is only supported for BUY orders."
                )

            percentage_of_portfolio = percentage_of_portfolio
            net_size = portfolio.get_net_size()
            size = net_size * percentage_of_portfolio / 100
            amount = size / price

        elif percentage_of_position is not None:

            if not OrderSide.SELL.equals(order_side):
                raise ApiException(
                    "Percentage of position is only supported for SELL orders."
                )

            position = self.position_service.find(
                {
                    "symbol": target_symbol,
                    "portfolio": portfolio.id
                }
            )
            amount = position.get_amount() * (percentage_of_position / 100)

        if precision is not None:
            amount = self.round_down(amount, precision)

        order_data = {
            "target_symbol": target_symbol,
            "price": price,
            "amount": amount,
            "order_type": OrderType.LIMIT.value,
            "order_side": OrderSide.from_value(order_side).value,
            "portfolio_id": portfolio.id,
            "status": OrderStatus.CREATED.value,
            "trading_symbol": portfolio.trading_symbol,
        }

        if BACKTESTING_FLAG in self.configuration_service.config \
                and self.configuration_service.config[BACKTESTING_FLAG]:
            order_data["created_at"] = \
                self.configuration_service.config[BACKTESTING_INDEX_DATETIME]

        return self.order_service.create(
            order_data, execute=execute, validate=validate, sync=sync
        )

    def create_market_order(
        self,
        target_symbol,
        order_side,
        amount,
        market=None,
        execute=False,
        validate=False,
        sync=True
    ):

        if market is None:
            portfolio = self.portfolio_service.get_all()[0]
        else:
            portfolio = self.portfolio_service.find({"market": market})
        order_data = {
            "target_symbol": target_symbol,
            "amount": amount,
            "order_type": OrderType.MARKET.value,
            "order_side": OrderSide.from_value(order_side).value,
            "portfolio_id": portfolio.id,
            "status": OrderStatus.CREATED.value,
            "trading_symbol": portfolio.trading_symbol,
        }

        if BACKTESTING_FLAG in self.configuration_service.config \
                and self.configuration_service.config[BACKTESTING_FLAG]:
            order_data["created_at"] = \
                self.configuration_service.config[BACKTESTING_INDEX_DATETIME]

        return self.order_service.create(
            order_data, execute=execute, validate=validate, sync=sync
        )

    def get_portfolio(self, market=None) -> Portfolio:

        if market is None:
            return self.portfolio_service.find({})

        return self.portfolio_service.find({{"market": market}})

    def get_unallocated(self, market=None) -> float:

        if market:
            portfolio = self.portfolio_service.find({{"market": market}})
        else:
            portfolio = self.portfolio_service.find({})

        trading_symbol = portfolio.trading_symbol
        return self.position_service.find(
            {"portfolio": portfolio.id, "symbol": trading_symbol}
        ).get_amount()

    def get_total_size(self):
        """
        Returns the total size of the portfolio.
        """
        return self.get_unallocated() + self.get_allocated()

    def reset(self):
        self._workers = []
        self._running_workers = []

    def get_order(
        self,
        reference_id=None,
        market=None,
        target_symbol=None,
        trading_symbol=None,
        order_side=None,
        order_type=None
    ) -> Order:
        query_params = {}

        if reference_id:
            query_params["reference_id"] = reference_id

        if target_symbol:
            query_params["target_symbol"] = target_symbol

        if trading_symbol:
            query_params["trading_symbol"] = trading_symbol

        if order_side:
            query_params["order_side"] = order_side

        if order_type:
            query_params["order_type"] = order_type

        if market:
            portfolio = self.portfolio_service.find({"market": market})
            positions = self.position_service.get_all(
                {"portfolio": portfolio.id}
            )
            query_params["position"] = [position.id for position in positions]

        return self.order_service.find(query_params)

    def get_orders(
        self,
        target_symbol=None,
        status=None,
        order_type=None,
        order_side=None,
        market=None
    ) -> List[Order]:

        if market is None:
            portfolio = self.portfolio_service.get_all()[0]
        else:
            portfolio = self.portfolio_service.find({"market": market})

        positions = self.position_service.get_all({"portfolio": portfolio.id})
        return self.order_service.get_all(
            {
                "position": [position.id for position in positions],
                "target_symbol": target_symbol,
                "status": status,
                "order_type": order_type,
                "order_side": order_side
            }
        )

    def get_order_fee(self, order_id) -> OrderFee:
        return self.order_service.get_order_fee(order_id)

    def get_positions(
        self,
        market=None,
        identifier=None,
        amount_gt=None,
        amount_gte=None,
        amount_lt=None,
        amount_lte=None
    ) -> List[Position]:
        query_params = {}

        if market is not None:
            query_params["market"] = market

        if identifier is not None:
            query_params["identifier"] = identifier

        if amount_gt is not None:
            query_params["amount_gt"] = amount_gt

        if amount_gte is not None:
            query_params["amount_gte"] = amount_gte

        if amount_lt is not None:
            query_params["amount_lt"] = amount_lt

        if amount_lte is not None:
            query_params["amount_lte"] = amount_lte

        portfolios = self.portfolio_service.get_all(query_params)

        if not portfolios:
            raise ApiException("No portfolio found.")

        portfolio = portfolios[0]
        return self.position_service.get_all(
            {"portfolio": portfolio.id}
        )

    def get_position(self, symbol, market=None, identifier=None) -> Position:
        query_params = {}

        if market is not None:
            query_params["market"] = market

        if identifier is not None:
            query_params["identifier"] = identifier

        portfolios = self.portfolio_service.get_all(query_params)

        if not portfolios:
            raise ApiException("No portfolio found.")

        portfolio = portfolios[0]

        try:
            return self.position_service.find(
                {"portfolio": portfolio.id, "symbol": symbol}
            )
        except ApiException:
            return None

    def has_position(
        self,
        symbol,
        market=None,
        identifier=None,
        amount_gt=0,
        amount_gte=None,
        amount_lt=None,
        amount_lte=None
    ):
        return self.position_exists(
            symbol,
            market,
            identifier,
            amount_gt,
            amount_gte,
            amount_lt,
            amount_lte
        )

    def position_exists(
            self,
            symbol,
            market=None,
            identifier=None,
            amount_gt=None,
            amount_gte=None,
            amount_lt=None,
            amount_lte=None
    ) -> bool:
        query_params = {}

        if market is not None:
            query_params["market"] = market

        if identifier is not None:
            query_params["identifier"] = identifier

        if amount_gt is not None:
            query_params["amount_gt"] = amount_gt

        if amount_gte is not None:
            query_params["amount_gte"] = amount_gte

        if amount_lt is not None:
            query_params["amount_lt"] = amount_lt

        if amount_lte is not None:
            query_params["amount_lte"] = amount_lte

        query_params["symbol"] = symbol
        return self.position_service.exists(query_params)

    def get_position_percentage_of_portfolio(
        self, symbol, market=None, identifier=None
    ) -> float:
        """
        Returns the percentage of the current total value of the portfolio
        that is allocated to a position. This is calculated by dividing
        the current value of the position by the total current value
        of the portfolio.
        """

        query_params = {}

        if market is not None:
            query_params["market"] = market

        if identifier is not None:
            query_params["identifier"] = identifier

        portfolios = self.portfolio_service.get_all(query_params)

        if not portfolios:
            raise ApiException("No portfolio found.")

        portfolio = portfolios[0]
        position = self.position_service.find(
            {"portfolio": portfolio.id, "symbol": symbol}
        )
        full_symbol = f"{position.symbol.upper()}/" \
                      f"{portfolio.trading_symbol.upper()}"
        ticker = self._market_data_source_service.get_ticker(
            symbol=full_symbol, market=market
        )
        total = self.get_unallocated() + self.get_allocated()
        return (position.amount * ticker["bid"] / total) * 100

    def get_position_percentage_of_portfolio_by_net_size(
            self, symbol, market=None, identifier=None
    ) -> float:
        """
        Returns the percentage of the portfolio that is allocated to a
        position. This is calculated by dividing the cost of the position
        by the total net size of the portfolio.

        The total net size of the portfolio is the initial balance of the
        portfolio plus the all the net gains of your trades.
        """
        query_params = {}

        if market is not None:
            query_params["market"] = market

        if identifier is not None:
            query_params["identifier"] = identifier

        portfolios = self.portfolio_service.get_all(query_params)

        if not portfolios:
            raise ApiException("No portfolio found.")

        portfolio = portfolios[0]
        position = self.position_service.find(
            {"portfolio": portfolio.id, "symbol": symbol}
        )
        net_size = portfolio.get_net_size()
        return (position.cost / net_size) * 100

    def close_position(self, symbol, market=None, identifier=None):
        portfolio = self.portfolio_service.find(
            {"market": market, "identifier": identifier}
        )
        position = self.position_service.find(
            {"portfolio": portfolio.id, "symbol": symbol}
        )

        if position.get_amount() == 0:
            return

        for order in self.order_service \
                .get_all(
                    {
                        "position": position.id,
                        "status": OrderStatus.OPEN.value
                    }
                ):
            self.order_service.cancel_order(order)

        symbol = f"{symbol.upper()}/{portfolio.trading_symbol.upper()}"
        ticker = self._market_data_source_service.get_ticker(
            symbol=symbol, market=market
        )
        self.create_limit_order(
            target_symbol=position.symbol,
            amount=position.get_amount(),
            order_side=OrderSide.SELL.value,
            price=ticker["bid"],
        )

    def add_strategies(self, strategies):
        self.strategy_orchestrator_service.add_strategies(strategies)

    def add_tasks(self, tasks):
        self.strategy_orchestrator_service.add_tasks(tasks)

    @property
    def strategies(self):
        return self.strategy_orchestrator_service.get_strategies()

    def get_strategy(self, strategy_id):
        for strategy in self.strategy_orchestrator_service.get_strategies():
            if strategy.worker_id == strategy_id:
                return strategy

        return None

    def get_allocated(self, market=None, identifier=None) -> float:

        if self.portfolio_configuration_service.count() > 1 \
                and identifier is None and market is None:
            raise ApiException(
                "Multiple portfolios found. Please specify a "
                "portfolio identifier."
            )

        if market is not None and identifier is not None:
            portfolio_configurations = self.portfolio_configuration_service \
                .get_all()

        else:
            query_params = {
                "market": market,
                "identifier": identifier
            }
            portfolio_configurations = [self.portfolio_configuration_service
                                        .find(query_params)]

        portfolios = []

        for portfolio_configuration in portfolio_configurations:
            portfolio = self.portfolio_service.find(
                {"identifier": portfolio_configuration.identifier}
            )
            portfolio.configuration = portfolio_configuration
            portfolios.append(portfolio)

        allocated = 0

        for portfolio in portfolios:
            positions = self.position_service.get_all(
                {"portfolio": portfolio.id}
            )

            for position in positions:
                if portfolio.trading_symbol == position.symbol:
                    continue

                symbol = f"{position.symbol.upper()}/" \
                         f"{portfolio.trading_symbol.upper()}"
                ticker = self._market_data_source_service.get_ticker(
                    symbol=symbol, market=market,
                )
                allocated = allocated + \
                    (position.get_amount() * ticker["bid"])

        return allocated

    def get_unfilled(self, market=None, identifier=None) -> float:

        if self.portfolio_configuration_service.count() > 1 \
                and identifier is None and market is None:
            raise ApiException(
                "Multiple portfolios found. Please specify a "
                "portfolio identifier."
            )

        if market is not None and identifier is not None:
            portfolio_configurations = self.portfolio_configuration_service \
                .get_all()

        else:
            query_params = {
                "market": market,
                "identifier": identifier
            }
            portfolio_configurations = [self.portfolio_configuration_service
                                        .find(query_params)]

        portfolios = []

        for portfolio_configuration in portfolio_configurations:
            portfolio = self.portfolio_service.find(
                {"identifier": portfolio_configuration.identifier}
            )
            portfolios.append(portfolio)

        unfilled = 0

        for portfolio in portfolios:
            orders = self.order_service.get_all(
                {"status": OrderStatus.OPEN.value, "portfolio": portfolio.id}
            )
            unfilled = unfilled + sum(
                [order.get_amount() * order.get_price() for order in orders]
            )

        return unfilled

    def get_portfolio_configurations(self):
        return self.portfolio_configuration_service.get_all()

    def has_open_buy_orders(self, target_symbol, identifier=None, market=None):
        query_params = {}

        if identifier is not None:
            portfolio = self.portfolio_service.find(
                {"identifier": identifier}
            )
            query_params["portfolio"] = portfolio.id

        if market is not None:
            portfolio = self.portfolio_service.find(
                {"market": market}
            )
            query_params["portfolio"] = portfolio.id

        query_params["target_symbol"] = target_symbol
        query_params["order_side"] = OrderSide.BUY.value
        query_params["status"] = OrderStatus.OPEN.value
        return self.order_service.exists(query_params)

    def has_open_sell_orders(self, target_symbol, identifier=None,
                             market=None):
        query_params = {}

        if identifier is not None:
            portfolio = self.portfolio_service.find(
                {"identifier": identifier}
            )
            query_params["portfolio"] = portfolio.id

        if market is not None:
            portfolio = self.portfolio_service.find(
                {"market": market}
            )
            query_params["portfolio"] = portfolio.id

        query_params["target_symbol"] = target_symbol
        query_params["order_side"] = OrderSide.SELL.value
        query_params["status"] = OrderStatus.OPEN.value
        return self.order_service.exists(query_params)

    def has_open_orders(
        self, target_symbol=None, identifier=None, market=None
    ):
        query_params = {}

        if identifier is not None:
            portfolio = self.portfolio_service.find(
                {"identifier": identifier}
            )
            query_params["portfolio"] = portfolio.id

        if market is not None:
            portfolio = self.portfolio_service.find(
                {"market": market}
            )
            query_params["portfolio"] = portfolio.id

        if target_symbol is not None:
            query_params["target_symbol"] = target_symbol

        query_params["status"] = OrderStatus.OPEN.value
        return self.order_service.exists(query_params)

    def check_pending_orders(self):
        self.order_service.check_pending_orders()

    def get_trades(self, market=None):
        return self.trade_service.get_trades(market)

    def get_closed_trades(self):
        return self.trade_service.get_closed_trades()

    def round_down(self, value, amount_of_decimals):

        if self.count_decimals(value) <= amount_of_decimals:
            return value

        with decimal.localcontext() as ctx:
            d = decimal.Decimal(value)
            ctx.rounding = decimal.ROUND_DOWN
            return float(round(d, amount_of_decimals))

    def count_decimals(self, number):
        decimal_str = str(number)
        if '.' in decimal_str:
            return len(decimal_str.split('.')[1])
        else:
            return 0

    def get_open_trades(self, target_symbol=None, market=None):
        return self.trade_service.get_open_trades(target_symbol, market)

    def close_trade(self, trade, market=None):
        self.trade_service.close_trade(trade, market)

    def get_number_of_positions(self):
        """
        Returns the number of positions that have a positive amount.
        """
        return self.position_service.count({"amount_gt": 0})

    def has_trading_symbol_position_available(
        self,
        amount_gt=None,
        amount_gte=None,
        percentage_of_portfolio=None,
        market=None
    ):
        """
        Checks if there is a position available for the trading symbol of the
        portfolio. If the amount_gt or amount_gte parameters are specified,
        the amount of the position must be greater than the specified amount.
        If the percentage_of_portfolio parameter is specified, the amount of
        the position must be greater than the net_size of the
        portfolio.

        :param amount_gt: The amount of the position must be greater than
        this amount.
        :param amount_gte: The amount of the position must be greater than
        or equal to this amount.
        :param percentage_of_portfolio: The amount of the position must be
        greater than the net_size of the portfolio.
        :param market: The market of the portfolio.
        :return: True if there is a trading symbol position available with the
        specified parameters, False otherwise.
        """
        portfolio = self.portfolio_service.find({"market": market})
        position = self.position_service.find(
            {"portfolio": portfolio.id, "symbol": portfolio.trading_symbol}
        )

        if amount_gt is not None:
            return position.get_amount() > amount_gt

        if amount_gte is not None:
            return position.get_amount() >= amount_gte

        if percentage_of_portfolio is not None:
            net_size = portfolio.get_net_size()
            return position.get_amount() >= net_size \
                * percentage_of_portfolio / 100

        return position.get_amount() > 0
