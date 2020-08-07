import json

from setuptools import setup

install_requires = []
tests_require = []

with open("Pipfile.lock") as fd:
    lock_data = json.load(fd)
    install_requires = [
        package_name + package_data["version"]
        for package_name, package_data in lock_data["default"].items()
    ]
    tests_require = [
        package_name + package_data["version"]
        for package_name, package_data in lock_data["develop"].items()
    ]

setup(
    name="cfn_mod",
    version="0.1.2",
    description="CloudFormation Modules Helper",
    url="http://github.com/storborg/funniest",
    author="Jeremy Axmacher",
    author_email="jaxmacher@presidio.com",
    license="MIT",
    packages=["cfn_mod"],
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    entry_points={"console_scripts": ["cfn-mod=cfn_mod.command_line:main"]},
)
