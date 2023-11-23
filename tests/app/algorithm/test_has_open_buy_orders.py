import os
from decimal import Decimal

from investing_algorithm_framework import create_app, RESOURCE_DIRECTORY, \
    PortfolioConfiguration
from tests.resources import TestBase, MarketServiceStub


class Test(TestBase):

    def setUp(self) -> None:
        self.resource_dir = os.path.abspath(
            os.path.join(
                os.path.join(
                    os.path.join(
                        os.path.join(
                            os.path.realpath(__file__),
                            os.pardir
                        ),
                        os.pardir
                    ),
                    os.pardir
                ),
                "resources"
            )
        )
        self.app = create_app(config={RESOURCE_DIRECTORY: self.resource_dir})
        self.app.add_portfolio_configuration(
            PortfolioConfiguration(
                market="binance",
                api_key="test",
                secret_key="test",
                trading_symbol="USDT"
            )
        )
        self.app.container.market_service.override(MarketServiceStub())
        self.app.initialize()

    def test_has_open_buy_orders(self):
        self.app.run(number_of_iterations=1, sync=False)
        trading_symbol_position = self.app.algorithm.get_position("USDT")
        self.assertEqual(Decimal(1000), trading_symbol_position.get_amount())
        self.assertFalse(self.app.algorithm.position_exists(symbol="BTC"))
        self.app.algorithm.create_limit_order(
            target_symbol="BTC",
            amount=1,
            price=10,
            order_side="BUY",
        )
        order_service = self.app.container.order_service()
        self.assertTrue(self.app.algorithm.has_open_buy_orders("BTC"))
        order_service.check_pending_orders()
        self.assertFalse(self.app.algorithm.has_open_buy_orders("BTC"))
