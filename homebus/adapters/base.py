from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ActionMeta:
    name: str
    description: str
    params_schema: dict
    returns_schema: dict


class AdapterBase(ABC):

    @abstractmethod
    async def execute(self, action: str, params: dict) -> dict:
        ...

    @abstractmethod
    async def health_check(self) -> dict:
        ...

    @abstractmethod
    def list_actions(self) -> list[ActionMeta]:
        ...
