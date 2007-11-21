#!/usr/bin/env python

"""Generic utilities."""

def ReadFile(filename, print_error=True):
    try:
        fp = open(filename)
        try:
            return fp.read()
        finally:
            fp.close()
    except IOError, e:
        if print_error:
            print 'Error reading %s: %s' % (filename, e)
        return None
