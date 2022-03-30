
import setuptools

setuptools.setup(
    name="smart-crema",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['six', 'librosa>=0.6', 'jams>=0.3', 'scikit-learn>=0.18', 'keras>=2.0', 'tensorflow>=1.0', 'mir_eval>=0.5', 'pumpp>=0.4', 'h5py>=2.7'],
)
