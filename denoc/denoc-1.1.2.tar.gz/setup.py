# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['denoc']

package_data = \
{'': ['*']}

install_requires = \
['colores>=0.1.2,<0.2.0']

entry_points = \
{'console_scripts': ['denoc = denoc:main']}

setup_kwargs = {
    'name': 'denoc',
    'version': '1.1.2',
    'description': 'Utilities for compile JavaScript with Deno',
    'long_description': '# Deprecated\n\nThis would make more sense if it was written using Deno, or a compiled language\nlike Go or Rust.\n\nEmail me to `eliaz.bobadilladev@gmail.com` if you create a similar tool, so I\nwill link it here.\n\n> If no one does, I will try to do it in my free time later,\n> [sponsor me](https://patreon.com/ultirequiem) 😩\n\n# Denoc\n\nCompile Deno executables and compress them for all platforms easily 🚀\n\n## Install\n\nYou can install [denoc](https://pypi.org/project/denoc) from PyPI like any other\npackage:\n\n```bash\npip install denoc\n```\n\nFrom Github 👇\n\n```bash\npip install git+https:/github.com/UltiRequiem/denoc\n```\n\n## Usage\n\n### Basic usage\n\n```bash\ndenoc compileMe.ts\n```\n\nThis will make a directory (`deno_builds`) with executables for all the\nsupported platforms.\n\nOptional flags:\n\n```bash\ndenoc --outputDir deno_dir_output --compress True file.ts\n```\n\n- `outputDir`: The directory where the binaries will be, by default the\n  directory is _deno_build_\n\n- `compress`: Compress the binaries directory\n\n### Build and Publish on GitHub Actions\n\n```yaml\nname: Compile\n\non:\n  push:\n    tags:\n      - "*"\n\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - name: Checkout\n        uses: actions/checkout@v2\n\n      - uses: denoland/setup-deno@v1\n        with:\n          deno-version: v1.x\n\n      - name: Install denoc\n        run: pip install denoc\n\n      - name: Build for all platforms\n        run: denoc cli.ts\n\n      - name: Release\n        uses: softprops/action-gh-release@v1\n        with:\n          files: |\n            deno_builds/x86_64-unknown-linux-gnu\n            deno_builds/aarch64-apple-darwin \n            deno_builds/x86_64-apple-darwin\n            deno_builds/x86_64-pc-windows-msvc.exe\n          token: ${{ secrets.GITHUB_TOKEN }}\n```\n\n> Example Repository 👉\n> [ultirequiem/deno-clear](https://github.com/UltiRequiem/deno-clear/releases/tag/v1.3.0)\n\n## Authors\n\n[Eliaz Bobadilla (a.k.a UltiRequiem)](https://ultirequiem.com) - Creator and\nMaintainer 💪\n\nSee also the full list of\n[contributors](https://github.com/UltiRequiem/denoc/contributors) who\nparticipated in this project.\n\n## Versioning\n\nWe use [SemVer](http://semver.org) for versioning. For the versions available,\nsee the [tags](https://github.com/UltiRequiem/denoc/tags).\n\n## Licence\n\nLicensed under the MIT License.\n',
    'author': 'Eliaz Bobadilla',
    'author_email': 'eliaz.bobadilladev@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/UltiRequiem/denoc',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
