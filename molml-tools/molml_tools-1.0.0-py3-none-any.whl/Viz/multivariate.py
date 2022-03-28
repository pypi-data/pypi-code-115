from typing import List, Callable, Any
from molml.Data.datastructures import Molecule
from sklearn.manifold import TSNE as sklearn_tsne
from sklearn.decomposition import PCA as sklearn_PCA
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


class TSNE:
    def __init__(self, n_components: int = 2, perplexity: Any = 30.0, early_exaggeration: Any = 12.0,
                 learning_rate: Any = "warn", n_iter: Any = 1000, n_iter_without_progress: Any = 300,
                 min_grad_norm: Any = 1e-7, metric: Any = "euclidean", init: Any = "warn", verbose: Any = 0,
                 random_state: Any = None, method: Any = "barnes_hut", angle: Any = 0.5, n_jobs: Any = None):

        self.tsne = sklearn_tsne(n_components=n_components, perplexity=perplexity,
                                 early_exaggeration=early_exaggeration, learning_rate=learning_rate, n_iter=n_iter,
                                 n_iter_without_progress=n_iter_without_progress, min_grad_norm=min_grad_norm,
                                 metric=metric, init=init, verbose=verbose, random_state=random_state, method=method,
                                 angle=angle, n_jobs=n_jobs)

        self.molecules = None
        self.results = None
        self.coords = None

    def fit(self, molecules: List[Molecule], transform: Callable = None, use_n_principal_components: int = None):

        self.molecules = molecules

        if use_n_principal_components is not None:
            pca = PCA(n_components=use_n_principal_components)
            pca.fit(molecules, transform=transform)
            x = pca.results

        else:
            if transform is None:
                x = np.array([m.ecfp() for m in molecules])
            else:
                x = np.array([transform(m.smiles) for m in molecules])

        self.results = self.tsne.fit_transform(x)
        self.coords = pd.DataFrame({"x": self.results[:, 0], "y": self.results[:, 1]})

    def show(self, color_by: List[any] = None, palette: Any = None):
        """ Make a quick scatter plot of the T-SNE"""

        if color_by is None:
            color_by = [None for _ in range(len(self.coords))]
        self.coords['label'] = color_by

        plt.figure(figsize=(10, 10))
        sns.scatterplot(
            x="x", y="y",
            hue="label",
            palette=palette,
            data=self.coords,
            alpha=0.5
        )
        plt.show()


class PCA:
    def __init__(self, n_components: int = 2):
        self.pca = sklearn_PCA(n_components=n_components)
        self.molecules = None
        self.results = None
        self.coords = None

    def fit(self, molecules: List[Molecule], transform: Callable = None):

        self.molecules = molecules

        if transform is None:
            x = np.array([m.ecfp() for m in molecules])
        else:
            x = np.array([transform(m.smiles) for m in molecules])

        self.results = self.pca.fit_transform(x)

        self.coords = pd.DataFrame({"x": self.results[:, 0], "y": self.results[:, 1]})

    def show(self, color_by: List[any] = None, palette: Any = None):
        """ Make a quick scatter plot of the PCA"""

        if color_by is None:
            color_by = [None for _ in range(len(self.coords))]
        self.coords['label'] = color_by

        plt.figure(figsize=(10, 10))
        sns.scatterplot(
            x="x", y="y",
            hue="label",
            palette=palette,
            data=self.coords,
            alpha=0.5
        )
        plt.show()
