import os
from setuptools import setup, find_packages

with open("requirements.txt") as reqs:
    install_requires = [
        line
        for line in reqs.read().split("\n")
        if line and not line.startswith(("--", "git+ssh"))
    ]
    dependency_links = [
        line
        for line in reqs.read().split("\n")
        if line and line.startswith(("--", "git+ssh"))
    ]

setup(
    name="pewtils",
    version="0.0.1",
    description="miscellaneous utilities",
    url="https://github.com/pewresearch/pewtils",
    author="Pew Research Center",
    author_email="admin@pewresearch.tech",
    install_requires=install_requires,
    dependency_links=dependency_links,
    packages=["pewtils"],
    # find_packages(exclude =
    #    ['contrib', 'docs', 'tests']),
    include_package_data=True,
    classifiers=[
        # https://pypi.python.org/pypi?%3Aaction=list_classifiers
        #        'Development Status :: 1 - Planning',
        #        'Development Status :: 2 - Pre-Alpha',
        "Development Status :: 3 - Alpha",
        #        'Development Status :: 4 - Beta',
        #        'Development Status :: 5 - Production/Stable',
        #        'Development Status :: 6 - Mature',
        #        'Development Status :: 7 - Inactive'
        "Intended Audience :: Science/Research",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
    ],
    keywords="pew pew pew",
    license="MIT",
)
