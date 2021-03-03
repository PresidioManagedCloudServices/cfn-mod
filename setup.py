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
    name="cfn-mod",
    version="0.15.13",
    description="CloudFormation Modules Helper",
    url="https://github.com/PresidioManagedCloudServices/cfn-mod",
    author="Jeremy Axmacher",
    author_email="jaxmacher@presidio.com",
    license="MIT",
    packages=["cfnmod"],
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    entry_points={"console_scripts": ["cfn-mod=cfnmod.__main__:main"]},
)
