from tests.resources import TestBase
from investing_algorithm_framework import TimeUnit
from investing_algorithm_framework.extensions import scheduler


def worker_one(_):
    pass


def worker_two(_):
    pass


class Test(TestBase):

    def setUp(self) -> None:
        super(Test, self).setUp()
        self.algo_app.algorithm._workers = []
        self.algo_app.algorithm.schedule(worker_one, None, TimeUnit.SECONDS, 1)
        self.algo_app.algorithm.schedule(worker_two, None, TimeUnit.SECONDS, 1)

    def test_stop_context(self) -> None:
        self.algo_app.algorithm.start()
        self.assertTrue(self.algo_app.algorithm.running)
        self.assertEqual(2, len(scheduler.get_jobs()))
        self.algo_app.algorithm.stop()
        self.assertFalse(self.algo_app.algorithm.running)
        self.assertEqual(0, len(scheduler.get_jobs()))
