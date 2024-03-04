import logging
from typing import List
from investing_algorithm_framework.domain import OrderStatus, OrderSide, \
    Trade, PeekableQueue, ApiException

logger = logging.getLogger(__name__)


class TradeService:
    """
    Service for managing trades
    """

    def __init__(
        self,
        portfolio_service,
        order_service,
        position_service,
        market_data_source_service
    ):
        self.portfolio_service = portfolio_service
        self.order_service = order_service
        self.market_data_source_service = market_data_source_service
        self.position_service = position_service

    def get_open_trades(self, target_symbol=None, market=None) -> List[Trade]:
        """
        Get open trades method

        :param target_symbol: str representing the target symbol
        :param market: str representing the market
        :return: list of Trade objects
        """

        portfolios = self.portfolio_service.get_all()
        trades = []

        for portfolio in portfolios:

            if target_symbol is not None:
                buy_orders = self.order_service.get_all({
                    "status": OrderStatus.CLOSED.value,
                    "order_side": OrderSide.BUY.value,
                    "portfolio_id": portfolio.id,
                    "target_symbol": target_symbol
                })
                sell_orders = self.order_service.get_all({
                    "status": OrderStatus.OPEN.value,
                    "order_side": OrderSide.SELL.value,
                    "portfolio_id": portfolio.id,
                    "target_symbol": target_symbol
                })
            else:
                buy_orders = self.order_service.get_all({
                    "status": OrderStatus.CLOSED.value,
                    "order_side": OrderSide.BUY.value,
                    "portfolio_id": portfolio.id
                })
                sell_orders = self.order_service.get_all({
                    "status": OrderStatus.OPEN.value,
                    "order_side": OrderSide.SELL.value,
                    "portfolio_id": portfolio.id
                })

            buy_orders = [
                buy_order for buy_order in buy_orders
                if buy_order.get_trade_closed_at() is None
            ]
            sell_amount = sum([order.amount for order in sell_orders])

            # Subtract the amount of the open sell orders
            # from the amount of the buy orders
            buy_orders_queue = PeekableQueue()

            for buy_order in buy_orders:
                buy_orders_queue.enqueue(buy_order)

            while sell_amount > 0 and not buy_orders_queue.is_empty():
                first_buy_order = buy_orders_queue.peek()
                available = first_buy_order.get_filled() \
                    - first_buy_order.get_trade_closed_amount()

                if available > sell_amount:
                    remaining = available - sell_amount
                    sell_amount = 0
                    first_buy_order.set_filled(remaining)
                else:
                    sell_amount = sell_amount - available
                    buy_orders_queue.dequeue()

            for buy_order in buy_orders_queue:
                symbol = buy_order.get_symbol()

                try:
                    ticker = self.market_data_source_service.get_ticker(
                        symbol=symbol, market=market
                    )
                except Exception as e:
                    logger.error(e)
                    raise ApiException(
                        f"Error getting ticker data for "
                        f"trade {buy_order.get_target_symbol()}"
                        f"-{buy_order.get_trading_symbol()}. Make sure you "
                        f"have registered a ticker market data source for "
                        f"{buy_order.get_target_symbol()}"
                        f"-{buy_order.get_trading_symbol()} "
                        f"for market {portfolio.market}"
                    )

                amount = buy_order.get_filled()
                closed_amount = buy_order.get_trade_closed_amount()

                if closed_amount is not None:
                    amount = amount - closed_amount

                trades.append(
                    Trade(
                        buy_order_id=buy_order.id,
                        target_symbol=buy_order.get_target_symbol(),
                        trading_symbol=buy_order.get_trading_symbol(),
                        amount=amount,
                        open_price=buy_order.get_price(),
                        opened_at=buy_order.get_created_at(),
                        current_price=ticker["bid"]
                    )
                )

        return trades

    def get_trades(self, market=None) -> List[Trade]:
        """
        Get trades method

        :param market: str representing the market
        :param portfolio_id: str representing the portfolio id
        :return: list of Trade objects
        """

        portfolios = self.portfolio_service.get_all()
        trades = []

        for portfolio in portfolios:
            buy_orders = self.order_service.get_all({
                "status": OrderStatus.CLOSED.value,
                "order_side": OrderSide.BUY.value,
                "portfolio_id": portfolio.id
            })

            for buy_order in buy_orders:
                symbol = buy_order.get_symbol()
                ticker = self.market_data_source_service.get_ticker(
                    symbol=symbol, market=market
                )
                trades.append(
                    Trade(
                        buy_order_id=buy_order.id,
                        target_symbol=buy_order.get_target_symbol(),
                        trading_symbol=buy_order.get_trading_symbol(),
                        amount=buy_order.get_amount(),
                        open_price=buy_order.get_price(),
                        closed_price=buy_order.get_trade_closed_price(),
                        closed_at=buy_order.get_trade_closed_at(),
                        opened_at=buy_order.get_created_at(),
                        current_price=ticker["bid"]
                    )
                )

        return trades

    def get_closed_trades(self, portfolio_id=None) -> List[Trade]:
        """
        Get closed trades method

        :param portfolio_id: str representing the portfolio id
        :return: list of Trade objects
        """
        buy_orders = self.order_service.get_all({
            "status": OrderStatus.CLOSED.value,
            "order_side": OrderSide.BUY.value,
            "portfolio_id": portfolio_id
        })
        return [
            Trade(
                buy_order_id=order.id,
                target_symbol=order.get_target_symbol(),
                trading_symbol=order.get_trading_symbol(),
                amount=order.get_amount(),
                open_price=order.get_price(),
                closed_price=order.get_trade_closed_price(),
                closed_at=order.get_trade_closed_at(),
                opened_at=order.get_created_at()
            ) for order in buy_orders
            if order.get_trade_closed_at() is not None
        ]

    def close_trade(self, trade, market=None):
        """
        Close trade method

        :param trade: Trade object
        :param market: str representing the market

        :raises ApiException: if trade is already closed
        """
        if trade.closed_at is not None:
            raise ApiException("Trade already closed.")

        order = self.order_service.get(trade.buy_order_id)

        if order.get_filled() <= 0:
            raise ApiException(
                "Buy order belonging to the trade has no amount."
            )

        portfolio = self.portfolio_service\
            .find({"position": order.position_id})
        position = self.position_service.find(
            {"portfolio": portfolio.id, "symbol": order.get_target_symbol()}
        )
        amount = order.get_amount()

        if position.get_amount() < amount:
            logger.warning(
                f"Order amount {amount} is larger then amount "
                f"of available {position.symbol} "
                f"position: {position.get_amount()}, "
                f"changing order amount to size of position"
            )
            amount = position.get_amount()

        symbol = f"{order.get_target_symbol().upper()}" \
                 f"/{order.get_trading_symbol().upper()}"
        ticker = self.market_data_source_service.get_ticker(
            symbol=symbol, market=market
        )
        self.order_service.create_limit_order(
            target_symbol=order.target_symbol,
            amount=amount,
            order_side=OrderSide.SELL.value,
            price=ticker["bid"],
        )

    def count(self, query_params=None) -> int:
        """
        Count method

        :param query_params: dict representing the query parameters
        :return: int representing the count
        """

        if query_params is None:
            query_params = {}
        else:
            query_param_keys = query_params.keys()

            # Check if there are only allowed query parameters
            if not all(
                key in ["portfolio_id", "target_symbol", "status"]
                for key in query_param_keys
            ):
                raise ApiException("Invalid trade query parameters")

        query_params["order_side"] = OrderSide.BUY.value
        status = query_params.get("status")

        if status is not None:
            query_params.pop("status")

        buy_orders = self.order_service.get_all(query_params)

        if status is not None:
            if status == OrderStatus.CLOSED.value:
                buy_orders = [
                    buy_order for buy_order in buy_orders
                    if buy_order.get_trade_closed_at() is not None
                ]
            else:
                buy_orders = [
                    buy_order for buy_order in buy_orders
                    if buy_order.get_trade_closed_at() is None
                ]

        return len(buy_orders)
