from setuptools import setup, find_packages
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    my_long_description = f.read()

setup(
    # https://pypi.org/search/?q=&o=&c=Topic+%3A%3A+Software+Development+%3A%3A+Build+Tools
    classifiers=[
        "Topic :: Software Development :: Libraries :: Python Modules",

        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",

        "Natural Language :: English",
        "Natural Language :: Chinese (Simplified)",
    ],

    name="mlvp",
    version="0.0.1",
    author="MLVP Team",
    author_email="879754743@qq.com",
    description="Multi-Language Verification Platform",
    long_description=my_long_description,

    url="https://github.com/XS-MLVP/mlvp",

    packages=find_packages(),

      package_data={
        'mlvp': ['templates/html/*',
                 'templates/html/icons/*'],
    },

    install_requires=[
        'pytest==7.4.3',
        'pytest-reporter-html1>=0.8.4',
        'pytest-xdist>=3.5.0',
    ],

    long_description_content_type="text/markdown",
)
