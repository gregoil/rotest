"""Setup file for handling packaging and distribution."""
from setuptools import setup, find_packages

setup(
    name='rotest',
    version="2.3.2",
    description="Resource oriented testing framework",
    long_description=open("README.rst").read(),
    license="MIT",
    author="gregoil",
    author_email="gregoil@walla.co.il",
    url="https://github.com/gregoil/rotest",
    keywords=["testing", "system", "django", "unittest"],
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
