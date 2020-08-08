# -*- coding: utf8 -*-
# Copyright (c) 2020 Niklas Rosenstein
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import ast
import os
from typing import Dict, Iterable, List, Optional
from databind.core import datamodel, field
from shore.util.ast import load_module_members

from .abstract import AbstractProjectModel
from .author import Author
from .changelog import ChangelogConfiguration
from .linter import LinterConfiguration
from .release import ReleaseConfiguration
from .requirements import Requirement
from .version import Version


def _get_file_in_directory(directory: str, prefix: str, preferred: List[str]) -> Optional[str]:
  """
  Returns a file in *directory* that is either in the *preferred* list or starts with
  specified *prefix*.
  """

  choices = []
  for name in sorted(os.listdir(directory)):
    if name in preferred:
      break
    if name.startswith(prefix):
      choices.append(name)
  else:
    if choices:
      return choices[0]
    return None

  return os.path.join(directory, name)


@datamodel
class PackageData:
  name: str
  modulename: Optional[str] = None
  version: Optional[Version] = None
  author: Author
  description: Optional[str] = None
  license: Optional[str] = None
  url: Optional[str] = None
  readme: Optional[str] = None
  wheel: Optional[bool] = True
  universal: Optional[bool] = None
  typed: Optional[bool] = False
  requirements: List[Requirement] = field(default_factory=list)
  test_requirements: List[Requirement] = field(altname='test-requirements', default_factory=list)
  extra_requirements: Dict[str, List[Requirement]] = field(altname='extra-requirements', default_factory=dict)
  source_directory: str = field(altname='source-directory', default='src')
  exclude: List[str] = field(default_factory=lambda: ['test', 'tests', 'docs'])
  entrypoints: Dict[str, List[str]] = field(default_factory=dict)
  classifiers: List[str] = field(default_factory=list)
  keywords: List[str] = field(default_factory=list)
  # TODO: Data files

  def get_modulename(self) -> str:
    return self.modulename or self.name.replace('-', '_')


@datamodel
class InstallConfiguration:
  @datamodel
  class InstallHooks:
    before_install: List[str] = field(altname='before-install', default_factory=list)
    after_install: List[str] = field(altname='after-install', default_factory=list)
    before_develop: List[str] = field(altname='before-develop', default_factory=list)
    after_develop: List[str] = field(altname='after-develop', default_factory=list)

  hooks: InstallHooks = field(default_factory=InstallHooks)


@datamodel
class PackageModel(AbstractProjectModel):
  data: PackageData = field(altname='package')
  install: InstallConfiguration = field(default_factory=InstallConfiguration)
  linter: LinterConfiguration = field(default_factory=LinterConfiguration)
  release: ReleaseConfiguration = field(default_factory=ReleaseConfiguration)

  def get_python_package_metadata(self) -> 'PythonPackageMetadata':
    """
    Returns a #PythonPackageMetadata object for this #PackageModel. This object can be
    used to inspect the author and version information that is defined in the package
    source code.
    """

    return PythonPackageMetadata(
      os.path.join(os.path.dirname(self.filename), self.data.source_directory),
      self.data.get_modulename())

  def get_readme(self) -> Optional[str]:
    """
    Returns the absolute path to the README for this package.
    """

    directory = os.path.dirname(self.filename)

    if self.data.readme:
      return os.path.abspath(os.path.join(directory, self.readme))

    return _get_file_in_directory(
      directory=directory,
      prefix='README.',
      preferred=['README.md', 'README.rst', 'README.txt', 'README'])

  def get_license(self) -> Optional[str]:
    """
    Returns the absolute path to the LICENSE file for this package.
    """

    return _get_file_in_directory(
      directory=os.path.dirname(self.filename),
      prefix='LICENSE.',
      preferred=['LICENSE', 'LICENSE.txt', 'LICENSE.rst', 'LICENSE.md'])


class PythonPackageMetadata:
  """
  Represents the metadata of a Python package on disk.
  """

  def __init__(self, source_directory: str, modulename: str) -> None:
    self.source_directory = source_directory
    self.modulename = modulename
    self._filename = None
    self._author = None
    self._version = None

  @property
  def filename(self) -> str:
    """
    Returns the file that contains the package metadata in the Python source code. This is
    usually the module filename, the package `__init__.py` or `__version__.py`.
    """

    if self._filename:
      return self._filename

    parts = self.modulename.split('.')
    prefix = os.sep.join(parts[:-1])
    choices = [
      parts[-1] + '.py',
      os.path.join(parts[-1], '__version__.py'),
      os.path.join(parts[-1], '__init__.py'),
    ]
    for filename in choices:
      filename = os.path.join(self.source_directory, prefix, filename)
      if os.path.isfile(filename):
        self._filename = filename
        return filename

    raise ValueError('Entry file for package "{}" could not be determined'
                     .format(self.modulename))

  @property
  def package_directory(self) -> str:
    """
    Returns the Python package directory. Raises a #ValueError if this metadata represents
    just a single Python module.
    """

    dirname, basename = os.path.split(self.filename)
    if basename not in ('__init__.py', '__version__.py'):
      raise ValueError('this package is in module-only form')

    return dirname

  @property
  def author(self) -> str:
    if not self._author:
      self._load_metadata()
    return self._author

  @property
  def version(self) -> str:
    if not self._version:
      self._load_metadata()
    return self._version

  def _load_metadata(self) -> None:
    members = load_module_members(self.filename)

    author = None
    version = None

    if '__version__' in members:
      try:
        version = ast.literal_eval(members['__version__'])
      except ValueError as exc:
        version = '<Non-literal expression>'

    if '__author__' in members:
      try:
        author = ast.literal_eval(members['__author__'])
      except ValueError as exc:
        author = '<Non-literal expression>'

    self._author = author
    self._version = version
