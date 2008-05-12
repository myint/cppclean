
.PHONY: test

HEADER_TESTS=4 5 6 7 8
CC_TESTS=1 2 3

test:
	./runtests.py > /dev/null
	cd test ; ../run.sh ast.py foo.h | diff - foo.h.expected
	cd test ; ../run.sh find_warnings.py foo.h | diff - foo.h.expected-warnings
	cd test ; ../run.sh find_warnings.py need-class.h | diff - need-class.h.expected-warnings
	for i in ${HEADER_TESTS} ; do \
	    (cd test/define ; \
	     ../../run.sh find_warnings.py d$$i.h | diff - d$$i.expected ) \
	done
	for i in ${CC_TESTS} ; do \
	    (cd test/define ; \
	     ../../run.sh find_warnings.py d$$i.cc | diff - d$$i.expected ) \
	done

expected:
	cd test ; ../run.sh ast.py foo.h > foo.h.expected
	cd test ; ../run.sh find_warnings.py foo.h > foo.h.expected-warnings
	cd test ; ../run.sh find_warnings.py need-class.h > need-class.h.expected-warnings
	for i in ${HEADER_TESTS} ; do \
	    (cd test/define ; \
	     ../../run.sh find_warnings.py d$$i.h > d$$i.expected ) \
	done
	for i in ${CC_TESTS} ; do \
	    (cd test/define ; \
	     ../../run.sh find_warnings.py d$$i.cc > d$$i.expected ) \
	done

clean:
	-rm -f *~ cpp/*~ cpp/*.pyc
