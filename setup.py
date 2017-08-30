"""Setup file for handling packaging and distribution."""
from setuptools import setup, find_packages

setup(
    name='rotest',
    version="2.2.8",
    install_requires=['django>=1.7,<1.8',
                      'ipdb',
                      'ipdbugger>=1.1.0',
                      'lxml',
                      'xlwt',
                      'twisted',
                      'psutil',
                      'colorama',
                      'termcolor',
                      'xmltodict',
                      'jsonschema',
                      'basicstruct'],
    packages=find_packages(exclude=['doc']),
    package_data={'': ['*.xls', '*.xsd', '*.json', '*.css', '*.xml', '*.rst']},
    zip_safe=False
)
