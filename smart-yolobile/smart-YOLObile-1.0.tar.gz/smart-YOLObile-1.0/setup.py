
import setuptools

setuptools.setup(
    name="smart-YOLObile",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['numpy == 1.17.5', 'opencv-python >= 4.1', 'torch == 1.4.0', 'torchvision==0.5.0', 'matplotlib', 'pycocotools', 'tqdm', 'pillow', 'tensorboard >= 1.14', 'PyYAML', 'thop'],
)
