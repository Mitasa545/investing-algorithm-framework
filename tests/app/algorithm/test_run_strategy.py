import os

from investing_algorithm_framework import create_app, TradingStrategy, TimeUnit, \
    PortfolioConfiguration, RESOURCE_DIRECTORY
from tests.resources import TestBase, random_string, MarketServiceStub


class StrategyOne(TradingStrategy):
    time_unit = TimeUnit.SECOND
    interval = 2

    def apply_strategy(self, algorithm, market_data):
        pass


class StrategyTwo(TradingStrategy):
    time_unit = TimeUnit.SECOND
    interval = 2

    def apply_strategy(self, algorithm, market_data):
        pass


class Test(TestBase):

    def setUp(self) -> None:
        super(Test, self).setUp()
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

    def test_with_strategy_object(self):
        app = create_app(config={RESOURCE_DIRECTORY: self.resource_dir})
        app.container.market_service.override(MarketServiceStub(None))
        app.container.portfolio_configuration_service().clear()
        app.add_portfolio_configuration(
            PortfolioConfiguration(
                market="BINANCE",
                trading_symbol="USDT",
            )
        )
        app.add_strategy(StrategyOne)
        app.add_strategy(StrategyTwo)
        app.run(number_of_iterations=2)
        self.assertFalse(app.running)
        strategy_orchestration_service = app.algorithm\
            .strategy_orchestrator_service
        self.assertTrue(strategy_orchestration_service.has_run("StrategyOne"))
        self.assertTrue(strategy_orchestration_service.has_run("StrategyTwo"))

    def test_with_decorator(self):
        app = create_app(config={RESOURCE_DIRECTORY: self.resource_dir})
        app.container.market_service.override(MarketServiceStub(None))
        app.container.portfolio_configuration_service().clear()
        app.add_portfolio_configuration(
            PortfolioConfiguration(
                market="BINANCE",
                trading_symbol="USDT",
            )
        )

        @app.strategy(time_unit=TimeUnit.SECOND, interval=1)
        def run_strategy(algorithm, market_data):
            pass

        app.run(number_of_iterations=1)
        strategy_orchestration_service = app.algorithm\
            .strategy_orchestrator_service
        self.assertTrue(strategy_orchestration_service.has_run("run_strategy"))

    def test_stateless(self):
        app = create_app(stateless=True)
        app.container.market_service.override(MarketServiceStub(None))
        app.container.portfolio_configuration_service().clear()
        app.add_portfolio_configuration(
            PortfolioConfiguration(
                market="BITVAVO",
                trading_symbol="EUR"
            )
        )
        app.add_strategy(StrategyOne)
        app.add_strategy(StrategyTwo)
        app.run(
            number_of_iterations=2,
            payload={"ACTION": "RUN_STRATEGY"},
        )
        strategy_orchestration_service = app.algorithm\
            .strategy_orchestrator_service
        self.assertTrue(strategy_orchestration_service.has_run("StrategyOne"))
        self.assertTrue(strategy_orchestration_service.has_run("StrategyTwo"))
