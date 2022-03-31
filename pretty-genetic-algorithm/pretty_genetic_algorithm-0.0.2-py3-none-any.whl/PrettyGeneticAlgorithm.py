from collections import OrderedDict
from typing import Any, Callable, List, Optional, Self, Tuple, Type

from functools import reduce
from tqdm import notebook
import random
import json

from BaseParameter import BaseParameter
from Creature import Creature


class PrettyGeneticAlgorithm:
    def __init__(
        self,
        num_species: int,
        num_creatures_per_species: int,
        dna_config: List[Type[BaseParameter]],
        fitness_cache_size: int = 500,
        mutation_rate: float = 0.1,
    ):
        """A pretty printing genetic algorithm implementation

        Args:
            num_species (int): Number of species to create, all species will evolve separately.
            num_creatures_per_species (int): Number of creatures to have per species. All creatures within a species can mutate/evolve with eachother.
            dna_config (List[Type[BaseParameter]]): The set of parameters to search over.
            fitness_cache_size (int, optional): If the genetic has already calculated a creature's fitness, it will use the old value and not calculate again. Defaults to 500.
            mutation_rate (float, optional): How likely a single DNA piece will mutate. Defaults to 0.1.
        """
        self.__num_species = num_species
        self.__num_creatures_per_species = num_creatures_per_species
        self.__species = [
            [Creature(dna_config) for _ in range(self.__num_creatures_per_species)]
            for _ in range(self.__num_species)
        ]
        self.__mutation_rate = mutation_rate
        self.__fitness_cache_size = fitness_cache_size

        self.__fitness_cache = OrderedDict()
        self.__best_fitness = None
        self.__best_creature = None
        total_permutations = reduce(
            lambda acc, item: acc * len(item["values"]), dna_config, 1
        )
        print(
            f"Total DNA permutations: {' * '.join(str(len(item['values'])) for item in dna_config)} = {total_permutations}"
        )

    __progress = None

    def __show_progress(
        self, progress: float, total: float, description: str = None
    ) -> None:
        if self.__progress is None:
            self.__progress = notebook.tqdm(total=total)
        if description is not None:
            self.__progress.set_description(description)
        self.__progress.n = progress
        self.__progress.refresh()

    def __measure_fitnesses(
        self,
        measure_fitness: Callable[[Creature], float],
        generation: int,
        generations: int,
    ) -> List[List[float]]:
        fitnesses = []
        for i, species in enumerate(self.__species):
            fitnesses.append([])
            for j, creature in enumerate(species):
                if creature.dna not in self.__fitness_cache:
                    self.__fitness_cache[creature.dna] = measure_fitness(creature)
                    while len(self.__fitness_cache) > self.__fitness_cache_size:
                        self.__fitness_cache.popitem()
                fitness = self.__fitness_cache[creature.dna]

                if self.__best_fitness is None or self.__best_fitness < fitness:
                    self.__best_fitness = round(fitness, 4)
                    self.__best_creature = creature
                fitnesses[-1].append(fitness)
                self.__show_progress(
                    (generation * self.__num_species * self.__num_creatures_per_species)
                    + (i * self.__num_creatures_per_species)
                    + j
                    + 1,
                    self.__num_species * self.__num_creatures_per_species * generations,
                    description=f"GA Progress | Best So Far: {round(self.__best_fitness, 4)}",
                )
        return fitnesses

    def evolve(
        self,
        generations: int,
        measure_fitness: Callable[[Creature], float],
        choose_mate: Callable[[Self, List[Creature]], int] = None,
        choose_mate_args: Tuple[Any, ...] = (),
        mutate: Callable[
            [Self, Creature, Creature, Callable[[Creature], float]], None
        ] = None,
        mutate_args: Tuple[Any, ...] = (),
        creatures_to_keep: int = 1,
    ) -> List[List[List[float]]]:
        """Evolves the GA based on parameters.

        Args:
            generations (int): Number of generations to run the genetic algorithm for.
            measure_fitness (Callable[[Creature], float]): The method used to determine how good a specific creature is. Must return a float corresponding to this value.
            choose_mate (Callable[[Self, List[Creature]], int, ...], optional): Chooses the next creature based on the index of the first. Only provide a custom function if you know what you're doing. Defaults to None.
            choose_mate_args (Tuple[Any, ...], optional): Any extra arguments you would like to supply for the choose_mate method. Defaults to ().
            mutate (Callable[ [Self, Creature, Creature, Callable[[Creature], float], ...], None ], optional): Mutates one of the two passed creature's DNA, to progress the genetic algorithm. Only provide a custom function if you know what you're doing. Defaults to None.
            mutate_args (Tuple[Any, ...], optional): Any extra arguments you would like to supply for the mutate method. Defaults to ().
            creatures_to_keep (int, optional): Number of creatures to keep per species for the next generation. Only keeps the best creatures. Defaults to 1.

        Returns:
            List[List[List[float]]]: History of the fitnesses which is a 3 dimensional list, where the outer list is the generations, followed by the number of species, and then the creatures.
        """
        if choose_mate is None:
            choose_mate = self.spatial_area
        if mutate is None:
            mutate = self.tournament_mutation
            mutate_args = (measure_fitness,)

        fitness_history = [self.__measure_fitnesses(measure_fitness, 0, generations)]
        for i in range(1, generations):
            for j, species in enumerate(self.__species):
                sorted_creatures = sorted(
                    enumerate(species),
                    key=lambda item: fitness_history[-1][j][item[0]],
                    reverse=True,
                )
                creatures_saved = sorted(
                    [item[0] for item in sorted_creatures[:creatures_to_keep]]
                )
                for _ in range(self.__num_creatures_per_species):
                    a = random.randint(
                        0, self.__num_creatures_per_species - 1 - creatures_to_keep
                    )
                    for index in creatures_saved:
                        if a >= index:
                            a += 1
                        else:
                            break
                    b = choose_mate(self, species, a, *choose_mate_args)
                    mutate(
                        self, self.__species[j][a], self.__species[j][b], *mutate_args
                    )
            fitness_history.append(
                self.__measure_fitnesses(measure_fitness, i, generations)
            )
        return fitness_history

    def best(self) -> Tuple[Optional[float], Optional[Creature]]:
        """Returns the best fitness and creature so far.

        Returns:
            Tuple[Optional[float], Optional[Creature]]: The fitness and the creature which are the best it's found.
        """
        return (self.__best_fitness, self.__best_creature)

    def serialise_dna_data(self) -> str:
        """Serialises all the dna from this genetic algorithm instance.

        Returns:
            str: Json string containing all of this instance's creature dna.
        """
        return json.dumps(
            [[creature.dna for creature in creatures] for creatures in self.__species]
        )

    @staticmethod
    def deserialise_dna_data(dna_str: str, **kwargs) -> "PrettyGeneticAlgorithm":
        """Creates a new PrettyGeneticAlgorithm instance from some passed in dna data.
            Accepts kwargs which are passed to the constructor of the created instance.

        Args:
            dna_str (str): Input dna data string

        Returns:
            PrettyGeneticAlgorithm: Instance created from the dna data string
        """
        dna_data = json.loads(dna_str)
        assert len(dna_data) > 0 and all(
            len(species) == len(dna_data[0]) for species in dna_data
        ), "Malformed DNA data when deserialising!"
        ga_kwargs = {
            "num_species": len(dna_data),
            "num_creatures_per_species": len(dna_data[0]),
        }
        ga_kwargs.update(kwargs)
        ga = PrettyGeneticAlgorithm(**ga_kwargs)
        for species_dna, species in zip(dna_data, ga.__species):
            for creature_dna, creature in zip(species_dna, species):
                creature.set_dna(creature_dna)
        return ga

    # Mutation functions defined below

    @staticmethod
    def tournament_mutation(instance, a, b, measure_fitness):
        if measure_fitness(a) > measure_fitness(b):
            b.set_dna(a.mutate(instance.__mutation_rate))
        else:
            a.set_dna(b.mutate(instance.__mutation_rate))

    @staticmethod
    def mating_mutation(instance, a, b, measure_fitness):
        a_fitness = measure_fitness(a)
        b_fitness = measure_fitness(b)
        offset = min(a_fitness, b_fitness) - 1
        a_fitness, b_fitness = (a_fitness - offset) ** 2, (b_fitness - offset) ** 2
        child = a.mate(b, self_bias=a_fitness / (a_fitness + b_fitness))
        a.set_dna(child.mutate(instance.__mutation_rate))

    # Choosing mate functions below

    @staticmethod
    def simple_random(instance, species_idx, creature_idx):
        return random.randint(0, len(instance.__species[species_idx]) - 1)

    @staticmethod
    def spatial_area(instance, species_idx, creature_idx, num_creatures_per_species=3):
        return random.randint(
            creature_idx, creature_idx + num_creatures_per_species - 1
        ) % len(instance.__species[species_idx])

    @staticmethod
    def spatial_similarity(
        instance, species_idx, creature_idx, num_creatures_per_species=3, invert=False
    ):
        similarities = zip(
            range(len(instance.__species[species_idx])),
            [
                instance.__species[species_idx][creature_idx].get_similarity(other)
                for other in instance.__species[species_idx]
            ],
        )
        sorted_creatures = sorted(
            similarities, key=lambda item: item[1], reverse=invert
        )
        return random.choice(sorted_creatures[:num_creatures_per_species])[0]

    @staticmethod
    def weighted_random(instance, species_idx, creature_idx, measure_fitness):
        raw_weights = list(
            map(
                lambda creature: measure_fitness(creature),
                instance.__species[species_idx],
            )
        )
        min_weight = min(raw_weights)
        weights = list(map(lambda weight: weight - min_weight, raw_weights))
        chosen_creature = round(random.random() * sum(weights))
        curr_weight = 0
        for i, weight in enumerate(weights):
            curr_weight += weight
            if curr_weight >= chosen_creature:
                return i

    @staticmethod
    def choose_next(instance, species_idx, creature_idx):
        return (creature_idx + 1) % len(instance.__species[species_idx])
