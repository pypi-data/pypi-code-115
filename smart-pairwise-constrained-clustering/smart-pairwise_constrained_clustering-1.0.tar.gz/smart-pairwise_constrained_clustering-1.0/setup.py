
import setuptools

setuptools.setup(
    name="smart-pairwise_constrained_clustering",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['numpy==1.18.4', 'scipy==1.4.1', 'scikit-learn==0.22.1', 'gurobipy==9.0.2'],
)
