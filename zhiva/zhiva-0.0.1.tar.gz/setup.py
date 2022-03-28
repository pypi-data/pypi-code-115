# Copyright zhiva.ai team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from distutils.core import setup
setup(
  name = 'zhiva',
  packages = ['zhiva'],
  version = '0.0.1',
  license=' Apache-2.0 License',
  description = 'Deploy AI models with a few lines of code',
  author = 'Piotr Mazurek & Kemal Erdem',
  author_email = 'ceo@zhiva.ai',
  url = 'https://github.com/zhiva-ai/zhiva',
  download_url = 'https://github.com/zhiva-ai/zhiva',
  install_requires=[
          'numpy',
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: Apache Software License',
    'Programming Language :: Python :: 3',
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
  ],
)
