from setuptools import setup, find_packages

with open("README.md") as README:
    readme = str(README.read())

with open("requirements.txt") as reqs:
    lines = reqs.read().split("\n")
    install_requires = [line for line in lines if line]

setup(
    name="pewtils",
    version="1.0.8",
    description="General programming utilities from Pew Research Center",
    long_description=readme,
    url="https://github.com/pewresearch/pewtils",
    author="Pew Research Center",
    author_email="info@pewresearch.org",
    install_requires=install_requires,
    packages=[p for p in find_packages() if p != "tests"],
    include_package_data=True,
    keywords="utilities, link standardization, input, output, pew pew pew",
    license="GPLv2+",
    classifiers=[
        # https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
)
