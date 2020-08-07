from setuptools import setup

setup(
    name="cfn_mod",
    version="0.1",
    description="CloudFormation Modules Helper",
    url="http://github.com/storborg/funniest",
    author="Jeremy Axmacher",
    author_email="jaxmacher@presidio.com",
    license="MIT",
    packages=["cfn_mod"],
    zip_safe=False,
    entry_points={"console_scripts": ["cfn-mod=cfn_mod.command_line:main"]},
)
