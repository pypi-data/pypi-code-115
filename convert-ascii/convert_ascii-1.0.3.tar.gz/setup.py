from setuptools import setup

setup(
    name = 'convert_ascii',
    version = '1.0.3',
    author = 'Leidiane Beatriz Passos Rodrigues',
    author_email = 'leidianebeatrizpassosrodrigues@gmail.com',
    packages = ['convert_ascii'],
    description = 'Um simples conversor de letra para decimal e vice e versa baseado na tabela ASCII',
    long_description = 'Um simples conversor de letra para decimal '
                        + 'e vice e versa baseado na tabela ASCII'
                        + 'para linguagem Python',
    url = 'https://github.com/leidibeatriz/convert_ascii',
    project_urls = {
        'Código fonte': 'https://github.com/leidibeatriz/convert_ascii',
        'Download': 'https://github.com/leidibeatriz/convert_ascii/archive/1.0.3.zip'
    },
    license = 'MIT',
    keywords = 'conversor de letra para decimal e vice e versa baseado na tabela ASCII',
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: Portuguese (Brazilian)',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Internationalization',
        'Topic :: Scientific/Engineering :: Physics'
    ]
)