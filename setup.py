import os
import re

from setuptools import find_packages
from setuptools import setup


ROOT = os.path.dirname(__file__)
VERSION_RE = re.compile(r'''__version__ = ['"]([a-zA-Z0-9.]+)['"]''')


def get_version():
    init = open(os.path.join(ROOT, 'teflo_podman_plugin', '__init__.py')).read()
    return VERSION_RE.search(init).group(1)


setup(
    name='teflo_podman_plugin',
    version=get_version(),
    description="teflo provisioner using podman",
    author="Red Hat Inc",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "podman>=3.1",
    ],
    entry_points={
        'provisioner_plugins': 'podman_plugin = teflo_podman_plugin:PodmanProvisionerPlugin',
    },
)
