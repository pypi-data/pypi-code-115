
import setuptools

setuptools.setup(
    name="smart-jawfish",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['click==6.6', 'flask>=0.12.3', 'Flask-SSLify==0.1.5', 'itsdangerous==0.24', 'Jinja2>=2.10.1', 'MarkupSafe==0.23', 'Werkzeug==0.11.11', 'WTForms==2.1'],
)
