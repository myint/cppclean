
.PHONY: test

test:
	./runtests.py > /dev/null
	cd test ; ../run.sh ast foo.h | diff - foo.h.expected
	cd test ; ../run.sh find_warnings foo.h | diff - foo.h.expected-warnings
	for i in 1 2 3 ; do \
	    (cd test/define ; \
	     ../../run.sh find_warnings d$$i.cc | diff - d$$i.expected ) \
	done

expected:
	cd test ; ../run.sh ast foo.h > foo.h.expected
	cd test ; ../run.sh find_warnings foo.h > foo.h.expected-warnings
	for i in 1 2 3 ; do \
	    (cd test/define ; \
	     ../../run.sh find_warnings d$$i.cc > d$$i.expected ) \
	done

clean:
	-rm -f *~ cpp/*~ cpp/*.pyc
