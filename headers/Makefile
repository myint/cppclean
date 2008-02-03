
.PHONY: test

test:
	./test.sh > /dev/null 2>&1
	cd test ; ../run.sh ast foo.h | diff - foo.h.expected
	cd test ; ../run.sh find_warnings foo.h | diff - foo.h.expected-warnings
	cd test/define ; ../../run.sh find_warnings d1.cc | diff - d1.expected
	cd test/define ; ../../run.sh find_warnings d2.cc | diff - d2.expected

expected:
	cd test ; ../run.sh ast foo.h > foo.h.expected
	cd test ; ../run.sh find_warnings foo.h > foo.h.expected-warnings
	cd test/define ; ../../run.sh find_warnings d1.cc > d1.expected
	cd test/define ; ../../run.sh find_warnings d2.cc > d2.expected

clean:
	-rm -f *~ cpp/*~ cpp/*.pyc
