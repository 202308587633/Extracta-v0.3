from abc import ABC, abstractmethod

class BaseParser(ABC):
    @abstractmethod
    def parse(self, soup, base_url):
        pass