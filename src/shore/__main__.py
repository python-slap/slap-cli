# -*- coding: utf8 -*-
# Copyright (c) 2019 Niklas Rosenstein
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

from shore.core.plugins import FileToRender, write_to_disk
from shore.util.resources import walk_package_resources
from typing import Iterable
import argparse
import jinja2
import os
import pkg_resources
import sys


def get_argument_parser(prog=None):
  parser = argparse.ArgumentParser(prog=prog)
  parser.add_argument('-C', '--change-directory', metavar='DIR')
  subparser = parser.add_subparsers(dest='command')

  new = subparser.add_parser('new')
  new.add_argument('name')
  new.add_argument('directory', nargs='?')
  new.add_argument('--monorepo', action='store_true')
  new.add_argument('--version')
  new.add_argument('--license')
  new.add_argument('--modulename')

  check = subparser.add_parser('check')
  check.add_argument('--treat-warnings-as-errors', action='store_true')

  update = subparser.add_parser('update')
  update.add_argument('--hotfix', action='store_true')
  update.add_argument('--patch', action='store_true')
  update.add_argument('--minor', action='store_true')
  update.add_argument('--major', action='store_true')
  update.add_argument('--version')

  build = subparser.add_parser('build')
  build.add_argument('target', nargs='?')
  build.add_argument('--all', action='store_true')
  build.add_argument('--directory')

  publish = subparser.add_parser('publish')
  publish.add_argument('target', nargs='?')
  publish.add_argument('--all', action='store_true')
  publish.add_argument('--test', action='store_true')
  publish.add_argument('--build-directory')

  return parser


def main(argv=None, prog=None):
  parser = get_argument_parser(prog)
  args = parser.parse_args(argv)
  if not args.command:
    parser.print_usage()
    return 0

  if args.command in ('build', 'publish'):
    # Convert relative to absolute paths before changing directory.
    for attr in ('directory', 'build_directory'):
      if getattr(args, attr, None):
        setattr(args, attr, os.path.abspath(getattr(args, attr)))
  if args.change_directory:
    os.chdir(args.change_directory)

  return globals()['_' + args.command](parser, args)


def _new(parser, args):

  if not args.directory:
    args.directory = args.name

  env_vars = {
    'name': args.name,
    'version': args.version,
    'license': args.license,
    'modulename': args.modulename
  }

  def _render_template(template_string, **kwargs):
    assert isinstance(template_string, str), type(template_string)
    return jinja2.Template(template_string).render(**(kwargs or env_vars))

  def _render_file(fp, filename):
    content = pkg_resources.resource_string('shore', filename).decode()
    fp.write(_render_template(content))

  def _render_namespace_file(fp):
    fp.write("__path__ = __import__('pkgutil').extend_path(__path__, __name__)\n")

  def _get_files() -> Iterable[FileToRender]:
    # Render the template files to the target directory.
    for source_filename in walk_package_resources('shore', 'templates/new'):
      # Expand variables in the filename.
      filename = _render_template(source_filename, name=args.name.replace('.', '/'))
      dest = os.path.join(args.directory, filename)
      yield FileToRender(
        None,
        os.path.normpath(dest),
        lambda _, fp: _render_file(fp, 'templates/new/' + source_filename))

    # Render namespace supporting files.
    parts = []
    for item in args.name.split('.')[:-1]:
      parts.append(item)
      dest = os.path.join(args.directory, 'src', *parts, '__init__.py')
      yield FileToRender(
        None,
        os.path.normpath(dest),
        lambda _, fp: _render_namespace_file(fp))

    # TODO (@NiklasRosenstein): Render the license file if it does not exist.

  for file in _get_files():
    print(file.name)
    write_to_disk(file)


_entry_main = lambda: sys.exit(main())

if __name__ == '__main__':
  _entry_main()
