"""Setup file for handling packaging and distribution."""
from setuptools import setup, find_packages

setup(
    name='rotest',
    version="2.2.8",
    description="Resource oriented testing framework",
    long_description=open("README.md").read(),
    license="MIT",
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
    packages=find_packages("src"),
    package_dir={"": "src"},
    package_data={'': ['*.xls', '*.xsd', '*.json', '*.css', '*.xml', '*.rst']},
    zip_safe=False
)
