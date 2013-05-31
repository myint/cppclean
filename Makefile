
.PHONY: test

test:
	./runtests.py > /dev/null

expected:
	./runtests.py --expected > /dev/null

clean:
	-rm -f *~ cpp/*~ cpp/*.pyc
