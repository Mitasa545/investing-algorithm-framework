import os

from investing_algorithm_framework import create_app, RESOURCE_DIRECTORY, \
    PortfolioConfiguration, Algorithm, MarketCredential
from tests.resources import TestBase, MarketServiceStub


class Test(TestBase):

    def count_decimals(self, number):
        decimal_str = str(number)
        if '.' in decimal_str:
            return len(decimal_str.split('.')[1])
        else:
            return 0

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
                trading_symbol="USDT"
            )
        )
        self.app.container.market_service.override(MarketServiceStub(None))
        self.app.add_algorithm(Algorithm())
        self.app.add_market_credential(
            MarketCredential(
                market="binance",
                api_key="api_key",
                secret_key="secret_key"
            )
        )
        self.app.initialize()

    def test_round_down(self):
        new_value = self.app.algorithm.round_down(1, 3)
        self.assertEqual(
            0, self.count_decimals(new_value)
        )
        self.assertEqual(1, new_value)
        new_value = self.app.algorithm.round_down(1.23456789, 2)
        self.assertEqual(
            2, self.count_decimals(new_value)
        )
        self.assertEqual(1.23, new_value)
        new_value = self.app.algorithm.round_down(1.987654321, 3)
        self.assertEqual(
            3, self.count_decimals(new_value)
        )
        self.assertEqual(1.987, new_value)
        new_value = self.app.algorithm.round_down(1.987654321, 4)
        self.assertEqual(
            4, self.count_decimals(new_value)
        )
        self.assertEqual(1.9876, new_value)
        new_value = self.app.algorithm.round_down(1.987654321, 5)
        self.assertEqual(
            5, self.count_decimals(new_value)
        )
        self.assertEqual(1.98765, new_value)
        new_value = self.app.algorithm.round_down(1.987654321, 6)
        self.assertEqual(
            6, self.count_decimals(new_value)
        )
        self.assertEqual(1.987654, new_value)
        new_value = self.app.algorithm.round_down(1.987654321, 7)
        self.assertEqual(
            7, self.count_decimals(new_value)
        )
        self.assertEqual(1.9876543, new_value)
        new_value = self.app.algorithm.round_down(1.987654321, 8)
        self.assertEqual(
            8, self.count_decimals(new_value)
        )
        self.assertEqual(1.98765432, new_value)
        new_value = self.app.algorithm.round_down(1.987654321, 9)
        self.assertEqual(
            9, self.count_decimals(new_value)
        )
        self.assertEqual(1.987654321, new_value)
        new_value = self.app.algorithm.round_down(1.987654321, 10)
        self.assertEqual(
            9, self.count_decimals(new_value)
        )
        self.assertEqual(1.987654321, new_value)
