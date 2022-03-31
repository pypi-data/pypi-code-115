""" Creature class definition """

import random
from typing import Any, Callable, Dict, Tuple, List, Type

from BaseParameter import BaseParameter


class Creature:
    __fitness_cache: Dict[Tuple[float], float] = {}

    def __init__(
        self,
        dna_config: List[Type[BaseParameter]],
        hard_cache=False,
        dna: Tuple[float] = None,
    ):
        """Creature class which holds a specific DNA sequence.

        Args:
            dna_config (List[Type[BaseParameter]]): Set of DNA to use for mutations
            hard_cache (bool, optional): Sets the Creature's caching value, this can save on calculations as it will not have to measure the fitness of a creature which has already been measured. Defaults to False.
            dna (Tuple[float], optional): Initial DNA to set. Defaults to None.
        """
        self.dna_config = dna_config
        self.hard_cache = hard_cache

        self.fitness = None
        if dna is not None:
            self.dna = dna
        else:
            self.dna = tuple(map(lambda parameter: parameter.new(), self.dna_config))
        for i, parameter in enumerate(dna_config):
            setattr(self, parameter.alias, self.dna[i])

    def set_dna(self, dna: List[Any]) -> None:
        self.dna = dna

    def get_similarity(self, other: "Creature") -> float:
        """Measures how similar another creature is to this one"""
        return sum(abs(self.dna[i] - other.dna[i]) for i in range(len(self.dna)))

    def mate(self, other, self_bias: float = 0.5) -> "Creature":
        """Combines this creature's dna with another's"""
        return Creature(
            self.dna_config,
            self.hard_cache,
            dna=tuple(
                self.dna[i] if random.random() < self_bias else other.dna[i]
                for i in range(len(self.dna))
            ),
        )

    def mutate(self, mutation_rate: float) -> "Creature":
        """Has a chance (mutation rate) to randomly change each dna unit and returns it"""
        return Creature(
            self.dna_config,
            self.hard_cache,
            dna=tuple(
                random.choice(self.dna_config[i]["values"])
                if random.random() < mutation_rate
                else item
                for i, item in enumerate(self.dna)
            ),
        )

    def __str__(self):
        return (
            "[Creature "
            + " ".join(
                f"{parameter.label}:{self.dna[i]}"
                for i, parameter in enumerate(self.dna_config)
            )
            + "]"
        )

    @classmethod
    def cache_fitness(cls, measure_fitness: Callable[["Creature"], float]):
        def wrapper(creature: Creature, *args, **kwargs):
            if creature.hard_cache:
                if creature.dna not in cls.__fitness_cache:
                    cls.__fitness_cache[creature.dna] = measure_fitness(
                        creature, *args, **kwargs
                    )
            elif creature.fitness is None:
                creature.fitness = measure_fitness(creature, *args, **kwargs)
            return (
                creature.fitness
                if not creature.hard_cache
                else cls.__fitness_cache[creature.dna]
            )

        return wrapper
