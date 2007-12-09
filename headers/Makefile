
test:
	./run.sh ast foo.h | diff - foo.h.expected
	./run.sh find_warnings foo.h | diff - foo.h.expected-warnings

expected:
	./run.sh ast foo.h > foo.h.expected
	./run.sh find_warnings foo.h > foo.h.expected-warnings

clean:
	-rm -f *~ cpp/*~ cpp/*.pyc
