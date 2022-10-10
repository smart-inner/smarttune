from abc import ABCMeta, abstractmethod

class ModelBase(object, metaclass=ABCMeta):

    @abstractmethod
    def _reset(self):
        pass
