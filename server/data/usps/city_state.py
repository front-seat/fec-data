from dataclasses import dataclass


@dataclass(frozen=True)
class CityState:
    city: str
    state: str
