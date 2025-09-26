from abc import ABC, abstractmethod


class BaseEmailProvider(ABC):
    @abstractmethod
    def list_messages(self, limit=50):
        pass
