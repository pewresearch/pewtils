# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS	=
SPHINXBUILD = sphinx-build
SOURCEDIR   = docs_source
BUILDDIR	= _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

github_docs:
	@make html
	@cp -a _build/html/. ./docs

python_lint:
	# stop the build if there are Python syntax errors or undefined names
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	# exit-zero treats all errors as warnings. The GitHub editor is 127 chars wide
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

python_test: python_lint
	python3 -m unittest tests

python_build: python_test
	python3 setup.py sdist bdist_wheel

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
