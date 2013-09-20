========
cppclean
========
.. image:: https://travis-ci.org/myint/cppclean.png?branch=master
   :target: https://travis-ci.org/myint/cppclean
   :alt: Build status


Goal
====
cppclean attempts to find problems in C++ source that slow development
in large code bases, for example various forms of unused code.
Unused code can be unused functions, methods, data members, types, etc
to unnecessary #include directives. Unnecessary #includes can cause
considerable extra compiles increasing the edit-compile-run cycle.

The project home page is: http://code.google.com/p/cppclean/


Features
========
- Find and print C++ language constructs: classes, methods, functions, etc.
- Find classes with virtual methods, no virtual destructor, and no bases
- Find global/static data that are potential problems when using threads
- Unnecessary forward class declarations
- Unnecessary function declarations
- Undeclared function definitions
- Find unnecessary header files #included
    - No direct reference to anything in the header
    - Header is unnecessary if classes were forward declared instead
- (planned) Source files that reference headers not directly #included,
  ie, files that rely on a transitive #include from another header
- (planned) Unused members (private, protected, & public) methods and data

AST is Abstract Syntax Tree, a representation of parsed source code.
http://en.wikipedia.org/wiki/Abstract_syntax_tree


Installation
============
::

    $ pip install --upgrade cppclean


Run
===
::

    $ cppclean <path>


Multiple include paths can be specified::

    $ cppclean --include-path=directory1 --include-path=directory2 <path>


Current status
==============
The parser works pretty well for header files, parsing about 99% of Google's
header files. Anything which inspects structure of C++ source files should
work reasonably well. Function bodies are not transformed to an AST,
but left as tokens. Such work is still needed on finding unused header files
and storing an AST in a database.


Non-goals
=========
- Parsing all valid C++ source
- Handling invalid C++ source gracefully
- Compiling to machine code (or anything beyond an AST)


Contact
=======
If you used cppclean, I would love to hear about your experiences
cppclean@googlegroups.com. Even if you don't use cppclean, I'd like to
hear from you. :-) (You can contact me directly at: nnorwitz@gmail.com)
