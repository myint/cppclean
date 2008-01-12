
.PHONY: test

test:
	./run.sh ast test/foo.h | diff - test/foo.h.expected
	./run.sh find_warnings test/foo.h | diff - test/foo.h.expected-warnings

expected:
	./run.sh ast test/foo.h > test/foo.h.expected
	./run.sh find_warnings test/foo.h > test/foo.h.expected-warnings

clean:
	-rm -f *~ cpp/*~ cpp/*.pyc
