from abc import ABC, abstractmethod


class ProcessActionStrategy(ABC):
    @abstractmethod
    def execute(self, datasets_task):
        pass


class ProcessActionContext:
    def __init__(self):
        self._strategy = None

    @property
    def strategy(self):
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: ProcessActionStrategy):
        self._strategy = strategy

    def perform_action(self, datasets_task):
        self._strategy.execute(datasets_task)
