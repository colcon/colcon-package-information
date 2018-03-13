# Copyright 2016-2018 Dirk Thomas
# Licensed under the Apache License, Version 2.0

from colcon_core.package_decorator import add_recursive_dependencies
from colcon_core.package_decorator import get_decorators
from colcon_core.package_selection import add_arguments \
    as add_packages_arguments
from colcon_core.package_selection import get_package_descriptors
from colcon_core.package_selection import select_package_decorators
from colcon_core.plugin_system import satisfies_version
from colcon_core.verb import VerbExtensionPoint


class InfoVerb(VerbExtensionPoint):
    """Package information."""

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(VerbExtensionPoint.EXTENSION_POINT_VERSION, '^1.0')

    def add_arguments(self, *, parser):  # noqa: D102
        parser.add_argument(
            'path', nargs='?',
            help='Specific path to check for package (ignore other discovery '
                 'arguments)')
        add_packages_arguments(parser)

    def main(self, *, context):  # noqa: D102
        # modify args to match path discovery extension
        if context.args.path is not None:
            context.args.paths = [context.args.path]

        descriptors = get_package_descriptors(
            context.args, additional_argument_names=['*'])
        decorators = get_decorators(descriptors)
        if context.args.path is None:
            add_recursive_dependencies(
                decorators, recursive_categories=('run', ))
            select_package_decorators(context.args, decorators)

        if not descriptors:
            return 'No package found'

        for decorator in decorators:
            if not decorator.selected:
                continue
            pkg = decorator.descriptor
            print('path:', pkg.path)
            print('  type:', pkg.type)
            print('  name:', pkg.name)
            if pkg.dependencies:
                print('  dependencies:')
                for category in sorted(pkg.dependencies.keys()):
                    print(
                        '    {category}:'.format_map(locals()),
                        ' '.join(sorted(pkg.dependencies[category])))
            if pkg.hooks:
                print('  hooks:', ' '.join(pkg.hooks))
            if pkg.metadata:
                print('  metadata:')
                for key in sorted(pkg.metadata.keys()):
                    value = pkg.metadata[key]
                    print(
                        '    {key}: {value}'
                        .format_map(locals()))
