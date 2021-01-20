from unittest import TestCase
from investing_algorithm_framework.core.context import \
    AlgorithmContextInitializer
from investing_algorithm_framework.core.context import AlgorithmContext
from investing_algorithm_framework.core.data_providers import DataProvider


class MyDataProvider(DataProvider):

    def get_data(self, algorithm_context):
        return 'data'

    def get_id(self) -> str:
        return self.__class__.__name__


class MyInitializer(AlgorithmContextInitializer):
    called = False

    def initialize(self, algorithm_context: AlgorithmContext) -> None:
        MyInitializer.called = True


class AlgorithmContextInitializer(TestCase):

    def test_initializer(self) -> None:
        self.assertFalse(MyInitializer.called)
        context = AlgorithmContext(
            algorithm_id='my_algorithm',
            data_providers=[MyDataProvider()],
            initializer=MyInitializer(),
            cycles=1
        )
        context.start()
        self.assertTrue(MyInitializer.called)
