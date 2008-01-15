
.PHONY: test

test:
	./test.sh > /dev/null 2>&1
	cd test ; ../run.sh ast foo.h | diff - foo.h.expected
	cd test ; ../run.sh find_warnings foo.h | diff - foo.h.expected-warnings

expected:
	cd test ; ../run.sh ast foo.h > foo.h.expected
	cd test ; ../run.sh find_warnings foo.h > foo.h.expected-warnings

clean:
	-rm -f *~ cpp/*~ cpp/*.pyc
