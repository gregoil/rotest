"""Setup file for handling packaging and distribution."""
import sys

from setuptools import setup, find_packages

result_handlers = [
    "db = rotest.core.result.handlers.db_handler:DBHandler",
    "xml = rotest.core.result.handlers.xml_handler:XMLHandler",
    "tags = rotest.core.result.handlers.tags_handler:TagsHandler",
    "excel = rotest.core.result.handlers.excel_handler:ExcelHandler",
    "dots = rotest.core.result.handlers.stream.dots_handler:DotsHandler",
    "tree = rotest.core.result.handlers.stream.tree_handler:TreeHandler",
    "remote = rotest.core.result.handlers.remote_db_handler:RemoteDBHandler",
    "loginfo = rotest.core.result.handlers.stream.log_handler:LogInfoHandler",
    "artifact = rotest.core.result.handlers.artifact_handler:ArtifactHandler",
    "logdebug = "
    "rotest.core.result.handlers.stream.log_handler:LogDebugHandler",
    "signature = "
    "rotest.core.result.handlers.signature_handler:SignatureHandler",
    "full = "
    "rotest.core.result.handlers.stream.stream_handler:EventStreamHandler",
]

requirements = [
    'django>=1.7,<1.8',
    'ipdb',
    'ipdbugger>=1.1.2',
    'docopt',
    'lxml<4.0.0',
    'xlwt',
    'attrdict',
    'pyyaml',
    'twisted',
    'psutil',
    'colorama',
    'termcolor',
    'jsonschema',
    'basicstruct'
]

if not sys.platform.startswith("win32"):
    requirements.append('python-daemon')

setup(
    name='rotest',
    version="2.8.0",
    description="Resource oriented testing framework",
    long_description=open("README.rst").read(),
    license="MIT",
    author="gregoil",
    author_email="gregoil@walla.co.il",
    url="https://github.com/gregoil/rotest",
    keywords="testing system django unittest",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "rotest-server = rotest.management.server.main:main"
        ],
        "rotest.result_handlers": result_handlers},
    packages=find_packages("src"),
    package_dir={"": "src"},
    package_data={'': ['*.xls', '*.xsd', '*.json', '*.css', '*.xml', '*.rst']},
    zip_safe=False
)
