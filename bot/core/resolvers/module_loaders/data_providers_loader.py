from typing import List

from bot.core.exceptions import ImproperlyConfigured
from bot.core.configuration import settings
from bot.core.resolvers import ClassCollector
from bot.core.data.data_providers import DataProvider


class DataProvidersLoader:

    def __init__(self):
        """
        Constructor will load the settings and check if the settings are configured. In the case the settings are not
        configured it will throw an exception.
        """
        self._settings = settings

    def load_modules(self) -> List[DataProvider]:
        """
        Function that will load the specified DataProvider instances. It will throw an exception if no
        DataProviders are specified. If third party plugins are used, it will try to load them. When it fails to load
        the plugins it will throw an error.
        """

        bot_name = self._settings.BOT_PROJECT_NAME

        class_collector = ClassCollector(bot_name, DataProvider)

        if len(class_collector.instances) == 0:
            raise ImproperlyConfigured(
                "There are no data providers configured. Make sure you implement data providers or use a plugin"
            )

        return class_collector.instances


