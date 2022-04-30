import re
from . import utils


def line_comment_regex(comment):
    return re.compile(rf"^\s*//\s*{comment}\s*$")


def file_disabled(filename):
    lines = utils.read_file(filename).split("\n")
    return len(lines) >= 1 and line_comment_regex("cppclean-disable").match(lines[0])


def line_disabled(filename, line_number):
    lines = utils.read_file(filename).split("\n")
    return (
        line_number >= 2
        and line_number <= len(lines) + 2
        and line_comment_regex("cppclean-disable-next-line").match(lines[line_number - 2])
    )
