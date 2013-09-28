check:
	pylint \
		--reports=no \
		--rcfile=/dev/null \
		--dummy-variables-rgx='^_+$$' \
		--disable=fixme \
		--disable=missing-docstring \
		--disable=too-many-arguments \
		--disable=invalid-name \
		--disable=too-many-locals \
		--disable=too-many-return-statements \
		--disable=too-many-instance-attributes \
		--disable=too-many-public-methods \
		--disable=too-many-branches \
		--disable=too-many-lines \
		--disable=too-many-statements \
		--disable=no-self-use \
		--disable=unused-argument \
		--disable=too-few-public-methods \
		cpp cppclean setup.py
	pep8 cpp $(wildcard *.py)
	check-manifest --ignore='.travis.yml,Makefile,test*'
	python setup.py --long-description | rst2html.py --strict > /dev/null

readme:
	@restview --long-description --strict
