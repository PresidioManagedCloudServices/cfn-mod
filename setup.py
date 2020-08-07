from setuptools import setup

setup(entry_points={"console_scripts": ["cfn-mod=cfn_mod.command_line:main"]})
