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

""" CLI dispatcher for renderers. """

from .base import PlizCommand
from ..core.plugins import load_plugin, PluginContext, write_to_disk
from termcolor import colored
import os


def _get_package_warnings(package):  # type: (Package) -> Iterable[str]
  if not package.package.author:
    yield 'missing ' + colored('$.package.author', attrs=['bold'])
  if not package.package.license:
    yield 'missing ' + colored('$.package.license', attrs=['bold'])
  if not package.package.url:
    yield 'missing ' +  colored('$.package.url', attrs=['bold'])
  for check in _get_package_consistency_checks(package):
    yield check


def _get_package_consistency_checks(package):
  data = package.load_entry_file_data()
  if data.author != str(package.package.author):
    yield 'Inconsistent package author ({!r} != {!r})'.format(
      data.author, str(package.package.author))
  if data.version != package.package.version:
    yield 'Inconsistent package version ({!r} != {!r})'.format(
      data.version, package.package.version)


class RenderCommand(PlizCommand):

  name = 'render'
  description = __doc__

  def update_parser(self, parser):
    super(RenderCommand, self).update_parser(parser)
    parser.add_argument('renderer', help='The name of a renderer to use.')
    parser.add_argument('--recursive', action='store_true')
    parser.add_argument('--dry', action='store_true')

  def handle_unknown_args(self, parser, args, argv):
    """ Parses additional `--` flags for the renderer options. """

    plugin_cls = load_plugin(args.renderer)
    options = plugin_cls.get_options()
    config = {o.name: o.get_default() for o in options if not o.required}
    pos_args = []

    it = iter(argv)
    queue = []
    while True:
      item = queue.pop(0) if queue else next(it, None)
      if item is None:
        break
      if not item.startswith('--'):
        if not config:  # No options have been parsed yet.
          pos_args.append(item)
          continue
        parser.error('unexpected argument {!r}'.format(item))
      if '=' in item:
        k, v = item[2:].partition('=')[::2]
      else:
        k = item[2:]
        v = next(it, 'true')
        if v.startswith('--'):
          queue.append(v)
          v = 'true'
      if v.lower().strip() in ('true', 'yes', '1', 'y', 'on', 'enabled'):
        v = True
      elif v.lower().strip() in ('false', 'no', '0', 'n', 'off', 'disabled'):
        v = False
      else:
        for f in (float, int):
          try:
            v = f(v)
          except ValueError:
            pass
      config[k] = v

    if len(pos_args) > len(options):
      parser.error('expected at max {} positional arguments, got {}'.format(
        len(plugin_cls.options), len(pos_args)))
    for option, value in zip(options, pos_args):
      if option.name in config:
        parser.error('duplicate argument value for option "{}"'.format(option.name))
      config[option.name] = value

    args._plugin = plugin_cls(config)

  def execute(self, parser, args):
    super(RenderCommand, self).execute(parser, args)

    monorepo, package = self.get_configuration()
    if package:
      context = PluginContext(None, [package])
    else:
      packages = monorepo.list_packages() if args.recursive else []
      context = PluginContext(monorepo, packages)

    files = list(args._plugin.get_files_to_render(context))
    print('Rendering {} file(s)'.format(len(files)))
    for file in files:
      print(' ', file.name)
      if not args.dry:
        write_to_disk(file)
