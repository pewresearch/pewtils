from setuptools import setup, find_packages

with open("README.md") as README:
    readme = str(README.read())

with open("requirements.txt") as reqs:
    lines = reqs.read().split("\n")
    install_requires = [line for line in lines if line]

setup(
    name="pewtils",
    version="1.1.3",
    description="General programming utilities from Pew Research Center",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/pewresearch/pewtils",
    author="Pew Research Center",
    author_email="info@pewresearch.org",
    install_requires=install_requires,
    packages=find_packages(exclude=["contrib", "docs", "tests"]),
    include_package_data=True,
    keywords="utilities, link standardization, input, output",
    license="GPLv2+",
    classifiers=[
        # https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 5 - Production/Stable",
        # "Development Status :: 6 - Mature",
        # "Development Status :: 7 - Inactive",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
)
