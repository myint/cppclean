default: check test

check:
	pylint \
		--reports=no \
		--rcfile=/dev/null \
		--dummy-variables-rgx='^_+$$' \
		--disable=bad-continuation \
		--disable=duplicate-code \
		--disable=fixme \
		--disable=invalid-name \
		--disable=missing-docstring \
		--disable=no-else-return \
		--disable=no-self-use \
		--disable=too-many-arguments \
		--disable=raising-bad-type \
		--disable=redefined-variable-type \
		--disable=simplifiable-if-statement \
		--disable=too-few-public-methods \
		--disable=too-many-locals \
		--disable=too-many-return-statements \
		--disable=too-many-instance-attributes \
		--disable=too-many-public-methods \
		--disable=too-many-branches \
		--disable=too-many-lines \
		--disable=too-many-statements \
		--disable=undefined-loop-variable \
		--disable=unused-argument \
		cpp cppclean setup.py
	pycodestyle cpp $(wildcard *.py)
	check-manifest
	python setup.py --long-description | rstcheck -

coverage:
	@coverage erase
	@PYTHON='coverage run --branch --parallel-mode' ./test.bash
	@coverage combine
	@coverage report

open_coverage: coverage
	@coverage html
	@python -m webbrowser -n "file://${PWD}/htmlcov/index.html"

readme:
	@restview --long-description --strict

test:
	./test.bash

.PHONY: check coverage open_coverage readme test
