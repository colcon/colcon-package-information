# Copyright 2016-2018 Dirk Thomas
# Licensed under the Apache License, Version 2.0

from collections import defaultdict
from collections import OrderedDict

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
            help='Output topological graph in ASCII '
                 '(implies --topological-order)')
        group.add_argument(
            '--topological-graph-dot',
            action='store_true',
            default=False,
            help='Output topological graph in DOT '
                 '(e.g. pass the output to dot: ` | dot -Tpng -o graph.png`), '
                 'legend: blue=build, red=run, tan=test, dashed=indirect')

        parser.add_argument(
            '--topological-graph-density',
            action='store_true',
            default=False,
            help='Output density for topological graph (only affects '
                 '--topological-graph)')

        parser.add_argument(
            '--topological-graph-legend',
            action='store_true',
            default=False,
            help='Output legend for topological graph (only affects '
                 '--topological-graph)')

    def main(self, *, context):  # noqa: D102
        args = context.args
        if args.topological_graph or args.topological_graph_dot:
            args.topological_order = True

        descriptors = get_package_descriptors(args)

        # always perform topological order for the select package extensions
        decorators = topological_order_packages(
            descriptors, recursive_categories=('run', ))

        select_package_decorators(args, decorators)

        if args.topological_graph:
            if args.topological_graph_legend:
                print('+ marks when the package in this row can be processed')
                print('* marks a direct dependency '
                      'from the package indicated by the + in the same column '
                      'to the package in this row')
                print('. marks a transitive dependency')
                print()

            # draw dependency graph in ASCII
            shown_decorators = list(filter(lambda d: d.selected, decorators))
            max_length = max([
                len(m.descriptor.name) for m in shown_decorators] + [0])
            lines = [
                m.descriptor.name.ljust(max_length + 2)
                for m in shown_decorators]
            depends = [
                m.descriptor.get_dependencies() for m in shown_decorators]
            rec_depends = [
                m.descriptor.get_recursive_dependencies(
                    [d.descriptor for d in decorators],
                    recursive_categories=('run', ))
                for m in shown_decorators]

            empty_cells = 0
            for i, decorator in enumerate(shown_decorators):
                for j in range(len(lines)):
                    if j == i:
                        # package i is being processed
                        lines[j] += '+'
                    elif shown_decorators[j].descriptor.name in depends[i]:
                        # package i directly depends on package j
                        lines[j] += '*'
                    elif shown_decorators[j].descriptor.name in rec_depends[i]:
                        # package i recursively depends on package j
                        lines[j] += '.'
                    else:
                        # package i doesn't depend on package j
                        lines[j] += ' '
                        empty_cells += 1
            if args.topological_graph_density:
                empty_fraction = \
                    empty_cells / (len(lines) * (len(lines) - 1)) \
                    if len(lines) > 1 else 1.0
                # normalize to 200% since half of the matrix should be empty
                density_percentage = 200.0 * (1.0 - empty_fraction)
                print('dependency density %.2f %%' % density_percentage)
                print()

        elif args.topological_graph_dot:
            lines = ['digraph graphname {']
            decorators_by_name = {m.descriptor.name: m for m in decorators}
            selected_pkg_names = [
                m.descriptor.name for m in decorators if m.selected]

            direct_edges = defaultdict(set)
            for deco in reversed(decorators):
                if not deco.selected:
                    continue
                # output selected packages as nodes
                lines.append(
                    '  "{deco.descriptor.name}";'.format_map(locals()))
                # collect direct dependencies
                for category, deps in deco.descriptor.dependencies.items():
                    for dep in deps:
                        if dep not in selected_pkg_names:
                            continue
                        direct_edges[(deco.descriptor.name, dep)].add(category)

            indirect_edges = defaultdict(set)
            for deco in reversed(decorators):
                if not deco.selected:
                    continue
                # collect indirect dependencies
                for category, deps in deco.descriptor.dependencies.items():
                    for dep in deps:
                        if dep in selected_pkg_names:
                            continue
                        if dep not in decorators_by_name:
                            continue
                        d = decorators_by_name[dep]
                        for rdep in d.recursive_dependencies:
                            if rdep not in selected_pkg_names:
                                continue
                            # skip redundant edges
                            if (deco.descriptor.name, rdep) in direct_edges:
                                continue
                            indirect_edges[(deco.descriptor.name, rdep)].add(
                                category)

            # output edges
            color_mapping = OrderedDict((
                ('build', 'blue'),
                ('run', 'red'),
                ('test', 'tan'),
            ))
            for style, edges in zip(
                ('', ', style="dashed"'),
                (direct_edges, indirect_edges),
            ):
                for (node_start, node_end), categories in edges.items():
                    colors = ':'.join([
                        color for category, color in color_mapping.items()
                        if category in categories])
                    lines.append(
                        '  "{node_start}" -> "{node_end}" '
                        '[color="{colors}"{style}];'
                        .format_map(locals()))

            lines.append('}')

        else:
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
