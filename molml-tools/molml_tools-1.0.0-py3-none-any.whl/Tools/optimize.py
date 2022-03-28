from molml.Data.datastructures import Dataset
from molml.Tools.utils import create_search_space, cross_validate
from skopt.utils import use_named_args
from skopt import gp_minimize
import pandas as pd
from typing import Dict, Callable, Union, List, Tuple


class BayesianOpt:
    def __init__(self, model: Callable, dataset: Dataset):
        """ Bayesian hyperparameter optimization

        Args:
            model: (Callable) A model that can be initizalize with a set of hyperparameters. This model MUST have
            the following methods: model.fit(x_train, y_train) and model.predict(x_test). (model input is taken
            from the Dataset)
            dataset: (Dataset) A Dataset containing molecules ready for training
        """
        self.model = model
        self.dataset = dataset
        self.hyperparameters = None
        self.best_score = None
        self.best_hyperparameters = None
        self.result = None
        self.history = pd.DataFrame(columns=['Iteration', 'Score', 'Best Score'])

    def opt(self, hyperparameters: Dict[str, list], evaluator: Callable, cv: Union[int, List[Tuple[int, int]]] = 5,
            n_calls: int = 100, minimize: bool = True):
        """

        Args:
            hyperparameters: (Dict[list]) A dict with a list of hyperparameters to optimize.
            Keys must be model params
            evaluator: (Callable) Any evaluation function that takes two arrays and returns a float
            cv: (Union[int, list]) Either an int (will perform random fold splitting) or a list of n tuples with data
            indices in the form of (train_indices, test_indices)
            n_calls: (int) number of iterations
            minimize: (bool) if False, it will try to maximise your evaluator

        Returns: (dict) best hyperparameters

        """

        self.hyperparameters = hyperparameters
        search_space = create_search_space(hyperparameters)
        self.iteration = 0

        @use_named_args(search_space)
        def evaluate_model(**params):
            self.iteration += 1

            try:
                model = self.model(**params)
                score = cross_validate(model, self.dataset, evaluator, cv=cv, verbose=False)
            except:
                import warnings
                warnings.warn(f"Optimization failed using: {params} -- A dummy score is being used, which "
                              f"might impact optimization")
                score = 0.5 if len(self.history) == 0 else self.history['Score'].tolist()[-1]

            if self.best_score is None:
                self.best_score = score
            if minimize and score < self.best_score:
                self.best_score = score
            if not minimize and score > self.best_score:
                self.best_score = score

            print(f"Iteration {self.iteration}/{n_calls} - score: {score:.4f} - best: {self.best_score:.4f}")
            self.history = pd.concat([self.history, pd.DataFrame({'Iteration': [self.iteration], 'Score': [score],
                                                                  'Best Score': [self.best_score]})], ignore_index=True)

            return -1 * score if not minimize else score

        # perform optimization
        print(f"Starting Bayesian optimization for {n_calls} iterations:")
        self.result = gp_minimize(evaluate_model, search_space, n_calls=n_calls)
        del self.iteration
        self.best_score = -1 * self.result.fun if not minimize else self.result.fun
        self.best_hyperparameters = dict(zip(self.hyperparameters.keys(), self.result.x))

        print(f'\nBest Score: {self.best_score}')
        print(self.best_hyperparameters)

    def show(self):
        """Plot optimization convergence"""
        import matplotlib.pyplot as plt

        plt.figure()
        plt.xlabel('Iteration')
        plt.ylabel('Score')
        plt.plot(self.history["Iteration"], self.history['Score'], label='Score')
        plt.plot(self.history["Iteration"], self.history['Best Score'], label='Best Score')
        plt.legend()
        plt.show()
