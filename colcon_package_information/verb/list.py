# Copyright 2016-2018 Dirk Thomas
# Licensed under the Apache License, Version 2.0

from colcon_core.package_selection import add_arguments \
    as add_packages_arguments
from colcon_core.package_selection import get_package_descriptors
from colcon_core.package_selection import select_package_decorators
from colcon_core.plugin_system import satisfies_version
from colcon_core.topological_order import topological_order_packages
from colcon_core.verb import VerbExtensionPoint


class ListVerb(VerbExtensionPoint):
    """List packages, optionally in topological ordering."""

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(VerbExtensionPoint.EXTENSION_POINT_VERSION, '^1.0')

    def add_arguments(self, *, parser):  # noqa: D102
        # only added so that package selection arguments can be used
        # which use the build directory to store state information
        parser.add_argument(
            '--build-base',
            default='build',
            help='The base path for all build directories (default: build)')

        add_packages_arguments(parser)

        parser.add_argument(
            '--topological-order', '-t',
            action='store_true',
            default=False,
            help='Order output based on topological ordering (breadth-first)')

        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            '--names-only', '-n',
            action='store_true',
            default=False,
            help='Output only the name of each package but not the path')
        group.add_argument(
            '--paths-only', '-p',
            action='store_true',
            default=False,
            help='Output only the path of each package but not the name')
        group.add_argument(
            '--topological-graph', '-g',
            action='store_true',
            default=False,
            help='Deprecated, use `colcon graph`')
        group.add_argument(
            '--topological-graph-dot',
            action='store_true',
            default=False,
            help='Deprecated, use `colcon graph --dot`')
        parser.add_argument(
            '--topological-graph-density',
            action='store_true',
            default=False,
            help='Deprecated, use `colcon graph --density`')
        parser.add_argument(
            '--topological-graph-legend',
            action='store_true',
            default=False,
            help='Deprecated, use `colcon graph --legend`')
        parser.add_argument(
            '--topological-graph-dot-cluster',
            action='store_true',
            default=False,
            help='Deprecated, use `colcon graph --dot-cluster`')
        parser.add_argument(
            '--topological-graph-dot-include-skipped',
            action='store_true',
            default=False,
            help='Deprecated, use `colcon graph --dot-include-skipped`')

    def main(self, *, context):  # noqa: D102
        args = context.args

        descriptors = get_package_descriptors(args)

        # always perform topological order for the select package extensions
        decorators = topological_order_packages(
            descriptors, recursive_categories=('run', ))

        select_package_decorators(args, decorators)

        if args.topological_graph:
            print('[colcon list -g] has been deprecated, '
                  'please use [colcon graph]')
            return
        elif args.topological_graph_dot:
            print('[colcon list --topological-graph-dot] has been deprecated, '
                  'please use [colcon graph --dot]')
            return
        elif args.topological_graph_density:
            print('[colcon list --topological-graph-density] has been '
                  'deprecated, please use [colcon graph --density]')
            return
        elif args.topological_graph_legend:
            print('[colcon list --topological-graph-legend] has been '
                  'deprecated, please use [colcon graph --legend]')
            return
        elif args.topological_graph_dot_cluster:
            print('[colcon list --topological-graph-dot-cluster] has been '
                  'deprecated, please use [colcon graph --dot-cluster]')
            return
        elif args.topological_graph_dot_include_skipped:
            print('[colcon list --topological-graph-dot-include-skipped] has '
                  'been deprecated, please use [colcon graph '
                  '--dot-include-skipped]')
            return

        if not args.topological_order:
            decorators = sorted(
                decorators, key=lambda d: d.descriptor.name)
        lines = []
        for decorator in decorators:
            if not decorator.selected:
                continue
            pkg = decorator.descriptor
            if args.names_only:
                lines.append(pkg.name)
            elif args.paths_only:
                lines.append(str(pkg.path))
            else:
                lines.append(
                    pkg.name + '\t' + str(pkg.path) + '\t(%s)' % pkg.type)
        if not args.topological_order:
            # output names and / or paths in alphabetical order
            lines.sort()

        for line in lines:
            print(line)
