# Copyright 2019 Dirk Thomas
# Licensed under the Apache License, Version 2.0

import operator

from colcon_core.package_augmentation import logger as \
    package_augmentation_logger
from colcon_core.package_augmentation import PackageAugmentationExtensionPoint
from colcon_core.plugin_system import satisfies_version
from packaging.version import Version

logger = package_augmentation_logger.getChild('check_dependency_constraint')


class CheckDependencyConstraintPackageAugmentation(
    PackageAugmentationExtensionPoint
):
    """Check package dependency constraints."""

    # the priority needs to be lower than other extensions to allow them to
    # augment dependency information before
    PRIORITY = 1

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(
            PackageAugmentationExtensionPoint.EXTENSION_POINT_VERSION, '^1.0')

    def augment_packages(  # noqa: D102
        self, descs, *, additional_argument_names=None
    ):
        descs_dict = {}
        for desc in descs:
            descs_dict.setdefault(desc.name, []).append(desc)
        for desc in descs:
            deps = desc.get_dependencies()
            for dep in deps:
                # skip dependencies which don't have a descriptor
                if dep.name not in descs_dict:
                    continue

                miss = all(
                    self._check_version_constraints(desc, dep, dep_desc)
                    for dep_desc in descs_dict.get(dep.name, ()))
                if miss and dep.metadata.get('skip_incompatible'):
                    logger.warning(
                        'Dropping version-incompatible dependency on ' +
                        dep.name + ' from ' + desc.name)
                    for category in dep.metadata.get('categories') or ():
                        desc.dependencies[category].discard(dep)

    def _check_version_constraints(self, desc, dep, dep_desc):
        """
        Check dependency version constraints against another package.

        :param desc: The package declaring the dependency being checked
        :param dep: The dependency being checked
        :param dep_desc: The package to which the dependency refers

        :returns: True if one or more constraints fail, False if all
          constraints pass, and None if no constraints were checked.
        """
        # if the dependency descriptor doesn't have a version there is nothing
        # to compare to
        if 'version' not in dep_desc.metadata:
            return
        try:
            dep_version = Version(dep_desc.metadata['version'])
        except Exception:  # noqa: B902
            # skip check if the version fails to parse
            return

        def lte(a, b):
            return operator.lt(a, b) or operator.eq(a, b)

        def gte(a, b):
            return operator.gt(a, b) or operator.eq(a, b)

        operators = {
            'version_lt': (operator.lt, 'less than'),
            'version_lte': (lte, 'less than or equal to'),
            'version_eq': (operator.eq, 'equal to'),
            'version_neq': (operator.ne, 'not equal to'),
            'version_gte': (gte, 'greater than or equal to'),
            'version_gt': (operator.gt, 'greater than'),
        }
        miss = None
        for key, value in dep.metadata.items():
            # only consider version operator metadata
            if key not in operators:
                continue
            op, msg = operators[key]
            try:
                version_constraint = Version(value)
            except Exception:  # noqa: B902
                logger.error(
                    "Failed to parse version '" + value + "' with " +
                    "constraint '" + msg + "' for dependency " + dep.name +
                    ' in package ' + desc.name)
                # skip check if the version fails to parse
                continue

            if not op(dep_version, version_constraint):
                miss = True
                logger.warning(
                    desc.name + ' depends on ' + dep.name +
                    ' which has version ' + dep_desc.metadata['version'] +
                    ' but expects it to be ' + msg + ' ' + value)
            else:
                miss = miss or False
                logger.debug(
                    desc.name + ' depends on ' + dep.name +
                    ' which has version ' + dep_desc.metadata['version'] +
                    ' which satisfies to be ' + msg + ' ' + value)
        return miss
