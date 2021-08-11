# This file was auto-generated by Shut. DO NOT EDIT
# For more information about Shut, check out https://pypi.org/project/shut/

from __future__ import print_function
import io
import os
import setuptools
import sys

command = sys.argv[1] if len(sys.argv) >= 2 else None

readme_file = 'README.md'
if os.path.isfile(readme_file):
  with io.open(readme_file, encoding='utf8') as fp:
    long_description = fp.read()
else:
  print("warning: file \"{}\" does not exist.".format(readme_file), file=sys.stderr)
  long_description = None

requirements = [
  'beautifulsoup4 >=4.8.1,<5.0.0',
  'databind.core >=1.1.2,<2.0.0',
  'databind.json >=1.1.2,<2.0.0',
  'click >=7.0.0,<8.0.0',
  'jinja2 >=2.11.1,<3.0.0',
  'networkx >=2.4.0,<3.0.0',
  'nr.fs >=1.5.0,<2.0.0',
  'nr.parsing.date >=1.0.3,<2.0.0',
  'nr.proxy >=1.0.0,<2.0.0',
  'nr.pylang.utils >=0.0.1,<1.0.0',
  'nr.utils.git >=0.1.3,<0.2.0',
  'nr.stream >=0.2.2,<1.0.0',
  'requests >=2.22.0,<3.0.0',
  'packaging >=20.1.0,<21.0.0',
  'PyYAML >=5.1.0,<6.0.0',
  'termcolor >=1.1.0,<2.0.0',
  'typing-extensions >=3.10.0.0,<4.0.0',
  'twine',
  'wheel',
]
test_requirements = [
  'pytest',
  'mypy',
  'types-beautifulsoup4',
  'types-click',
  'types-requests',
  'types-jinja2',
  'types-PyYAML',
  'types-setuptools',
  'types-termcolor',
]
extras_require = {}
extras_require['test'] = test_requirements

setuptools.setup(
  name = 'shut',
  version = '0.16.1',
  author = 'Niklas Rosenstein',
  author_email = 'rosensteinniklas@gmail.com',
  description = 'Automates the heavy lifting of release and distribution management for pure Python packages.',
  long_description = long_description,
  long_description_content_type = 'text/markdown',
  url = 'https://github.com/NiklasRosenstein/shut',
  license = 'MIT',
  packages = setuptools.find_packages('src', ['test', 'test.*', 'tests', 'tests.*', 'docs', 'docs.*']),
  package_dir = {'': 'src'},
  include_package_data = True,
  install_requires = requirements,
  extras_require = extras_require,
  tests_require = test_requirements,
  python_requires = '>=3.7.0,<4.0.0',
  data_files = [],
  entry_points = {
    'console_scripts': [
      'shut = shut.commands:shut',
    ]
  },
  cmdclass = {},
  keywords = [],
  classifiers = [],
  zip_safe = False,
)
