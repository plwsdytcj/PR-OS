from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.simulation.schemas import SimulationReport


class StressTestAdapter(ABC):
    engine_name: str

    @abstractmethod
    def run(self, payload: dict[str, Any]) -> SimulationReport:
        raise NotImplementedError
