# Copyright 2024 Open Source Robotics Foundation, Inc.
# Licensed under the Apache License, Version 2.0

from unittest.mock import patch

from colcon_core.dependency_descriptor import DependencyDescriptor
from colcon_core.package_descriptor import PackageDescriptor
from colcon_package_information.package_augmentation.\
    check_dependency_constraint \
    import CheckDependencyConstraintPackageAugmentation
import pytest


@pytest.mark.parametrize(
    'operator,expect_lt,expect_eq,expect_gt', [
        (None,          0, 0, 0),
        ('version_eq',  1, 0, 1),
        ('version_gt',  1, 1, 0),
        ('version_gte', 1, 0, 0),
        ('version_lt',  0, 1, 1),
        ('version_lte', 0, 0, 1),
        ('version_neq', 0, 1, 0),
    ])
def test_operators(operator, expect_lt, expect_eq, expect_gt):
    pkg_a_v1 = PackageDescriptor('/tmp/pkg_a')
    pkg_a_v1.name = 'pkg_a'
    pkg_a_v1.metadata['version'] = '1.0'

    pkg_a_v2 = PackageDescriptor('/tmp/pkg_a')
    pkg_a_v2.name = 'pkg_a'
    pkg_a_v2.metadata['version'] = '2.0'

    pkg_a_v3 = PackageDescriptor('/tmp/pkg_a')
    pkg_a_v3.name = 'pkg_a'
    pkg_a_v3.metadata['version'] = '3.0'

    pkg_a_dep = DependencyDescriptor('pkg_a')
    if operator is not None:
        pkg_a_dep.metadata[operator] = '2.0'

    pkg_b = PackageDescriptor('/tmp/pkg_b')
    pkg_b.name = 'pkg_b'
    pkg_b.dependencies['build'] = {pkg_a_dep}

    extension = CheckDependencyConstraintPackageAugmentation()

    with patch(
        'colcon_package_information.package_augmentation.'
        'check_dependency_constraint.logger.warning'
    ) as warning:
        extension.augment_packages({pkg_a_v1, pkg_b})
        assert expect_lt == warning.call_count
        warning.reset_mock()

        extension.augment_packages({pkg_a_v2, pkg_b})
        assert expect_eq == warning.call_count
        warning.reset_mock()

        extension.augment_packages({pkg_a_v3, pkg_b})
        assert expect_gt == warning.call_count
        warning.reset_mock()


def test_dependency_missing():
    pkg_b = PackageDescriptor('/tmp/pkg_b')
    pkg_b.name = 'pkg_b'
    pkg_b.dependencies['build'] = {
        DependencyDescriptor('pkg_a'),
    }

    extension = CheckDependencyConstraintPackageAugmentation()
    extension.augment_packages({pkg_b})


def test_dependency_missing_version():
    pkg_a = PackageDescriptor('/tmp/pkg_a')
    pkg_a.name = 'pkg_a'

    pkg_b = PackageDescriptor('/tmp/pkg_b')
    pkg_b.name = 'pkg_b'
    pkg_b.dependencies['build'] = {
        DependencyDescriptor('pkg_a'),
    }

    extension = CheckDependencyConstraintPackageAugmentation()
    extension.augment_packages({pkg_a, pkg_b})


def test_dependency_invalid_version():
    pkg_a = PackageDescriptor('/tmp/pkg_a')
    pkg_a.name = 'pkg_a'
    pkg_a.metadata['version'] = 'totally!invalid&version'

    pkg_b = PackageDescriptor('/tmp/pkg_b')
    pkg_b.name = 'pkg_b'
    pkg_b.dependencies['build'] = {
        DependencyDescriptor('pkg_a'),
    }

    extension = CheckDependencyConstraintPackageAugmentation()
    extension.augment_packages({pkg_a, pkg_b})


def test_dependency_invalid_version_operator():
    pkg_a = PackageDescriptor('/tmp/pkg_a')
    pkg_a.name = 'pkg_a'
    pkg_a.metadata['version'] = '2.0'

    pkg_b = PackageDescriptor('/tmp/pkg_b')
    pkg_b.name = 'pkg_b'
    pkg_b.dependencies['build'] = {
        DependencyDescriptor('pkg_a', metadata={
            'version_eq': 'totally!invalid&version'
        }),
    }

    extension = CheckDependencyConstraintPackageAugmentation()
    extension.augment_packages({pkg_a, pkg_b})
