# -*- coding: utf-8 -*-

from setuptools import setup, find_namespace_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='ensembl_prodinf',
    version='0.1.0',
    description='Base libraries for Ensembl Production infrastructure services',
    long_description=readme,
    author='Dan Staines',
    author_email='dstaines@ebi.ac.uk',
    url='https://github.com/radome/ensembl-prodinf-core',
    license=license,
    packages=find_namespace_packages(exclude=('tests', 'docs'))
)
