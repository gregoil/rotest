"""Setup file for handling packaging and distribution."""
import sys

from setuptools import setup, find_packages

__version__ = "3.1.0"

result_handlers = [
    "db = rotest.core.result.handlers.db_handler:DBHandler",
    "xml = rotest.core.result.handlers.xml_handler:XMLHandler",
    "excel = rotest.core.result.handlers.excel_handler:ExcelHandler",
    "dots = rotest.core.result.handlers.stream.dots_handler:DotsHandler",
    "tree = rotest.core.result.handlers.stream.tree_handler:TreeHandler",
    "remote = rotest.core.result.handlers.remote_db_handler:RemoteDBHandler",
    "loginfo = rotest.core.result.handlers.stream.log_handler:LogInfoHandler",
    "artifact = rotest.core.result.handlers.artifact_handler:ArtifactHandler",
    "logdebug = "
    "rotest.core.result.handlers.stream.log_handler:LogDebugHandler",
    "pretty = "
    "rotest.core.result.handlers.stream.log_handler:PrettyHandler",
    "signature = "
    "rotest.core.result.handlers.signature_handler:SignatureHandler",
    "full = "
    "rotest.core.result.handlers.stream.stream_handler:EventStreamHandler",
]

requirements = [
    'django>=1.7,<1.8',
    'ipdb',
    'py',
    'isort',
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
    version=__version__,
    description="Resource oriented testing framework",
    long_description=open("README.rst").read(),
    license="MIT",
    author="gregoil",
    author_email="gregoil@walla.co.il",
    url="https://github.com/gregoil/rotest",
    keywords="testing system django unittest",
    install_requires=requirements,
    python_requires="~=2.7.0",
    entry_points={
        "console_scripts": [
            "rotest = rotest.cli.main:main"
        ],
        "rotest.result_handlers": result_handlers,
        "rotest.cli_client_parsers": [],
        "rotest.cli_client_actions": [],
    },
    packages=find_packages("src"),
    package_dir={"": "src"},
    package_data={'': ['*.xls', '*.xsd', '*.json', '*.css', '*.xml', '*.rst']},
    zip_safe=False,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Testing',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.7',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Operating System :: MacOS',
    ],
)
