from tests.resources import TestBase, TestOrderAndPositionsObjectsMixin
from investing_algorithm_framework.core.models import SQLLitePortfolio, db


class Test(TestBase, TestOrderAndPositionsObjectsMixin):

    def setUp(self):
        super(Test, self).setUp()
        self.start_algorithm()

    def test(self) -> None:
        order = self.algo_app.algorithm\
            .create_limit_sell_order(
                self.TARGET_SYMBOL_A, self.BASE_SYMBOL_A_PRICE, 10
            )

        self.assert_is_limit_order(order)

    def tearDown(self) -> None:
        db.session.query(SQLLitePortfolio).delete()
        db.session.commit()
        super(Test, self).tearDown()

    def test_with_execution(self) -> None:
        order = self.algo_app.algorithm \
            .create_limit_buy_order(
                self.TARGET_SYMBOL_A,
                self.BASE_SYMBOL_A_PRICE,
                10,
                execute=True
        )
        order.set_executed()

        order = self.algo_app.algorithm\
            .create_limit_sell_order(
                self.TARGET_SYMBOL_A,
                self.BASE_SYMBOL_A_PRICE,
                10,
                execute=True
            )

        self.assert_is_limit_order(order)

        order.set_executed()

        self.assert_is_limit_order(order, executed=True)
