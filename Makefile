.ONESHELL:
SHELL := /bin/bash
SRC = $(wildcard nbs/*.ipynb)

all: nbdev2 docexp

nbdev2: $(SRC)
	nbprocess_export
	touch nbdev2

sync:
	nbdev_update_lib

.PHONY: docexp
docexp:
	nbdev2_docs --path nbs --dest mddocs

test:
	nbdev_test_nbs

release: pypi conda_release
	nbdev_bump_version

conda_release:
	fastrelease_conda_package

pypi: dist
	twine upload --repository pypi dist/*

dist: clean
	python setup.py sdist bdist_wheel

clean:
	rm -rf dist

