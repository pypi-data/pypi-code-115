from typing import Any, Callable, List, Self, Tuple, Type

from functools import reduce
from tqdm import notebook
import random

from BaseParameter import BaseParameter
from Creature import Creature


class PrettyGeneticAlgorithm:
    def __init__(
        self,
        num_species: int,
        num_creatures_per_species: int,
        dna_config: List[Type[BaseParameter]],
        hard_cache: bool = False,
        mutation_rate: float = 0.1,
    ):
        """A pretty printing genetic algorithm implementation

        Args:
            num_species (int): Number of species to create, all species will evolve separately.
            num_creatures_per_species (int): Number of creatures to have per species. All creatures within a species can mutate/evolve with eachother.
            dna_config (List[Type[BaseParameter]]): The set of parameters to search over.
            hard_cache (bool, optional): Sets the Creature's caching value, this can save on calculations as it will not have to measure the fitness of a creature which has already been measured. Defaults to False.
            mutation_rate (float, optional): How likely a single DNA piece will mutate. Defaults to 0.1.
        """
        self.num_species = num_species
        self.num_creatures_per_species = num_creatures_per_species
        self.__species = [
            [
                Creature(dna_config, hard_cache)
                for _ in range(self.num_creatures_per_species)
            ]
            for _ in range(self.num_species)
        ]
        self.mutation_rate = mutation_rate

        self.best_fitness = None
        self.best_creature = None
        self.total_permutations = reduce(
            lambda acc, item: acc * len(item["values"]), dna_config, 1
        )
        print(
            f"Total DNA permutations: {' * '.join(str(len(item['values'])) for item in dna_config)} = {self.total_permutations}"
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
                fitness = measure_fitness(creature)
                if self.best_fitness is None or self.best_fitness < fitness:
                    self.best_fitness = round(fitness, 4)
                    self.best_creature = creature
                fitnesses[-1].append(fitness)
                self.__show_progress(
                    (generation * self.num_species * self.num_creatures_per_species)
                    + (i * self.num_creatures_per_species)
                    + j
                    + 1,
                    self.num_species * self.num_creatures_per_species * generations,
                    description=f"GA Progress | Best So Far: {round(self.best_fitness, 4)} | {round(len(Creature.fitness_cache.keys()) / self.total_permutations * 100, 2)}% input space explored",
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
        """Evolves the GA based on parameters

        Args:
            generations (int): Number of generations to run the genetic algorithm for.
            measure_fitness (Callable[[Creature], float]): The method used to determine how good a specific creature is. Must return a float corresponding to this value.
            choose_mate (Callable[[Self, List[Creature]], int, ...], optional): Chooses the next creature based on the index of the first. Only provide a custom function if you know what you're doing. Defaults to None.
            choose_mate_args (Tuple[Any, ...], optional): Any extra arguments you would like to supply for the choose_mate method. Defaults to ().
            mutate (Callable[ [Self, Creature, Creature, Callable[[Creature], float], ...], None ], optional): Mutates one of the two passed creature's DNA, to progress the genetic algorithm. Only provide a custom function if you know what you're doing. Defaults to None.
            mutate_args (Tuple[Any, ...], optional): Any extra arguments you would like to supply for the mutate method. Defaults to ().
            creatures_to_keep (int, optional): Number of creatures to keep for the next generation. Only keeps the best creatures. Defaults to 1.

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
                for _ in range(self.num_creatures_per_species):
                    a = random.randint(
                        0, self.num_creatures_per_species - 1 - creatures_to_keep
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

    # Mutation functions defined below

    @staticmethod
    def tournament_mutation(instance, a, b, measure_fitness):
        if measure_fitness(a) > measure_fitness(b):
            b.set_dna(a.mutate(instance.mutation_rate))
        else:
            a.set_dna(b.mutate(instance.mutation_rate))

    @staticmethod
    def mating_mutation(instance, a, b, measure_fitness):
        a_fitness = measure_fitness(a)
        b_fitness = measure_fitness(b)
        offset = min(a_fitness, b_fitness) - 1
        a_fitness, b_fitness = (a_fitness - offset) ** 2, (b_fitness - offset) ** 2
        child = a.mate(b, self_bias=a_fitness / (a_fitness + b_fitness))
        a.set_dna(child.mutate(instance.mutation_rate))

    # Choosing mate functions below

    @staticmethod
    def simple_random(instance, species_idx, creature_idx):
        return random.randint(0, len(instance.species[species_idx]) - 1)

    @staticmethod
    def spatial_area(instance, species_idx, creature_idx, num_creatures_per_species=3):
        return random.randint(
            creature_idx, creature_idx + num_creatures_per_species - 1
        ) % len(instance.species[species_idx])

    @staticmethod
    def spatial_similarity(
        instance, species_idx, creature_idx, num_creatures_per_species=3, invert=False
    ):
        similarities = zip(
            range(len(instance.species[species_idx])),
            [
                instance.species[species_idx][creature_idx].get_similarity(other)
                for other in instance.species[species_idx]
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
                instance.species[species_idx],
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
        return (creature_idx + 1) % len(instance.species[species_idx])
