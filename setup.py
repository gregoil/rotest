"""Setup file for handling packaging and distribution."""
from __future__ import absolute_import
from setuptools import setup, find_packages


__version__ = "7.13.1"

result_handlers = [
    "db = rotest.core.result.handlers.db_handler:DBHandler",
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
    install_requires=[
        'django>=1.8,<2.1',
        'py',
        'ipdbugger>=2.5',
        'xlwt',
        'attrdict',
        'pyyaml',
        'psutil',
        'colorama',
        'termcolor',
        'jsonschema',
        'basicstruct',
        'future',
        'swaggapi>=0.6.7',
        'cached_property',
        'channels>=1,<2',
        'websocket-client>=0.56',
        'pywin32<224; sys.platform == "win32"',
    ],
    extras_require={
        ':python_version=="2.7"': ['statistics'],
        "dev": [
            "pytest",
            "pytest-django",
            "pytest-cov",
            "mock",
            "pyfakefs",
            "xlrd",
            "pathlib2",
            "flake8",
            "pylint<2.4",
            "waiting",
        ]
    },
    python_requires=">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*,!=3.5.*",
    entry_points={
        "console_scripts": [
            "rotest = rotest.cli.main:main"
        ],
        "rotest.result_handlers": result_handlers,
        "rotest.cli_server_actions": [],
        "rotest.cli_client_parsers": [],
    },
    packages=find_packages("src"),
    package_dir={"": "src"},
    package_data={'': ['*.xls', '*.xsd', '*.json', '*.css', '*.xml', '*.rst']},
    zip_safe=False,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Testing',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Operating System :: MacOS',
    ],
)
