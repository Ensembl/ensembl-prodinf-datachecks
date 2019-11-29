from setuptools import setup

with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='ensembl_srv',
    version='0.1.0',
    description='Server libraries for Ensembl Production infrastructure services',
    long_description=readme,
    author='Dan Staines',
    author_email='dstaines@ebi.ac.uk',
    url='https://github.com/radome/ensembl-prodinf-srv',
    license=license,
    install_requires=[
        'ensembl_prodinf @ git+https://github.com/radome/ensembl-prodinf-core@EP-4321_py2_to_py3',
    ]
)
