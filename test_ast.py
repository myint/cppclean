#!/usr/bin/env python
#
# Copyright 2008 Neal Norwitz
# Portions Copyright 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AST test."""

from __future__ import absolute_import

import unittest

from cpp import ast
from cpp import tokenize


__author__ = 'nnorwitz@google.com (Neal Norwitz)'


def _install_generic_equal(cls, attrs):
    """Add an __eq__ method to |cls| so objects can be compared for tests.

    Args:
      cls: Python class to add __eq__ method to
      attrs: string - space separated of attribute names to compare

    """
    attrs = attrs.split()

    def __eq__(self, other):
        if not isinstance(other, cls):
            return False
        for a in attrs:
            # Use not (a == other) since this could be recursive and
            # we don't define a not equals method.
            if not (getattr(self, a) == getattr(other, a)):
                return False
        return True
    cls.__eq__ = __eq__


def _install_equal_methods():
    """Install __eq__ methods on the appropriate objects used for testing."""
    _install_generic_equal(tokenize.Token, 'name')
    _install_generic_equal(ast.Class,
                           'name bases templated_types namespace body')
    _install_generic_equal(ast.Struct,
                           'name bases templated_types namespace body')
    _install_generic_equal(ast.Type, ('name templated_types modifiers '
                                      'reference pointer array'))
    _install_generic_equal(ast.Parameter, 'name type default')
    _install_generic_equal(ast.Function, ('name return_type parameters '
                                          'modifiers templated_types '
                                          'body namespace'))
    _install_generic_equal(ast.Method, ('name in_class return_type parameters '
                                        'modifiers templated_types '
                                        'body namespace'))
    _install_generic_equal(ast.Include, 'filename system')
    _install_generic_equal(ast.Typedef, 'name alias namespace')
    _install_generic_equal(ast.VariableDeclaration,
                           'name type initial_value namespace')
_install_equal_methods()


def get_tokens(code_string):
    return tokenize.get_tokens(code_string + '\n')


def MakeBuilder(code_string):
    """Convenience function to make an AstBuilder from a code snippet.."""
    return ast.AstBuilder(get_tokens(code_string), '<test>')


def Token(name, start=0, end=0, token_type=tokenize.NAME):
    return tokenize.Token(token_type, name, start, end)


def Include(filename, system=False, start=0, end=0):
    return ast.Include(start, end, filename, system)


def Class(name, start=0, end=0, bases=None, body=None, templated_types=None,
          namespace=None):
    if namespace is None:
        namespace = []

    return ast.Class(start, end, name, bases, templated_types, body, namespace)


def Struct(name, start=0, end=0, bases=None, body=None, templated_types=None,
           namespace=None):
    if namespace is None:
        namespace = []

    return ast.Struct(start, end, name, bases, templated_types, body,
                      namespace)


def Type(name, start=0, end=0, templated_types=None, modifiers=None,
         reference=False, pointer=False, array=False):
    if templated_types is None:
        templated_types = []

    if modifiers is None:
        modifiers = []

    return ast.Type(start, end, name, templated_types, modifiers,
                    reference, pointer, array)


def Function(name, return_type, parameters, start=0, end=0,
             modifiers=0, templated_types=None, body=None, namespace=None):
    if namespace is None:
        namespace = []

    return ast.Function(start, end, name, return_type, parameters,
                        modifiers, templated_types, body, namespace)


def Method(name, in_class, return_type, parameters, start=0, end=0,
           modifiers=0, templated_types=None, body=None, namespace=None):
    if namespace is None:
        namespace = []

    return ast.Method(start, end, name, in_class, return_type, parameters,
                      modifiers, templated_types, body, namespace)


def Typedef(name, start=0, end=0, alias=None, namespace=None):
    if alias is None:
        alias = []

    if namespace is None:
        namespace = []

    return ast.Typedef(start, end, name, alias, namespace)


def VariableDeclaration(name, var_type, start=0, end=0, initial_value='',
                        namespace=None):
    if namespace is None:
        namespace = []

    return ast.VariableDeclaration(start, end, name, var_type, initial_value,
                                   namespace)


class TypeConverterDeclarationToPartsTest(unittest.TestCase):

    def setUp(self):
        self.converter = ast.TypeConverter([])

    def test_simple(self):
        tokens = get_tokens('Fool data')
        name, type_name, templated_types, modifiers, _, __ = \
            self.converter.declaration_to_parts(list(tokens), True)
        self.assertEqual('data', name)
        self.assertEqual('Fool', type_name)
        self.assertEqual([], templated_types)
        self.assertEqual([], modifiers)

    def test_simpleModifiers(self):
        tokens = get_tokens('const volatile Fool data')
        name, type_name, templated_types, modifiers, _, __ = \
            self.converter.declaration_to_parts(list(tokens), True)
        self.assertEqual('data', name)
        self.assertEqual('Fool', type_name)
        self.assertEqual([], templated_types)
        self.assertEqual(['const', 'volatile'], modifiers)

    def test_simpleArray(self):
        tokens = get_tokens('Fool[] data')
        name, type_name, templated_types, modifiers, _, __ = \
            self.converter.declaration_to_parts(list(tokens), True)
        self.assertEqual('data', name)
        self.assertEqual('Fool', type_name)
        self.assertEqual([], templated_types)
        self.assertEqual([], modifiers)

    def test_simpleTemplate(self):
        tokens = get_tokens('Fool<tt> data')
        name, type_name, templated_types, modifiers, _, __ = \
            self.converter.declaration_to_parts(list(tokens), True)
        self.assertEqual('data', name)
        self.assertEqual('Fool', type_name)
        self.assertEqual([Type('tt')], templated_types)
        self.assertEqual([], modifiers)


class TypeConverterToParametersTest(unittest.TestCase):

    def setUp(self):
        self.converter = ast.TypeConverter([])

    def test_really_simple(self):
        tokens = get_tokens('int bar')
        results = self.converter.to_parameters(list(tokens))
        self.assertEqual(1, len(results))

        self.assertEqual([], results[0].type.modifiers)
        self.assertEqual('int', results[0].type.name)
        self.assertEqual([], results[0].type.templated_types)
        self.assertEqual(False, results[0].type.pointer)
        self.assertEqual(False, results[0].type.reference)
        self.assertEqual(False, results[0].type.array)
        self.assertEqual('bar', results[0].name)

    def test_array(self):
        tokens = get_tokens('int[] bar')
        results = self.converter.to_parameters(list(tokens))
        self.assertEqual(1, len(results))

        self.assertEqual([], results[0].type.modifiers)
        self.assertEqual('int', results[0].type.name)
        self.assertEqual([], results[0].type.templated_types)
        self.assertEqual(False, results[0].type.pointer)
        self.assertEqual(False, results[0].type.reference)
        self.assertEqual(True, results[0].type.array)
        self.assertEqual('bar', results[0].name)

    def test_arrayPointerReference(self):
        params = 'const int[] bar, mutable char* foo, volatile Bar& babar'
        tokens = get_tokens(params)
        results = self.converter.to_parameters(list(tokens))
        self.assertEqual(3, len(results))

        self.assertEqual(['const'], results[0].type.modifiers)
        self.assertEqual('int', results[0].type.name)
        self.assertEqual([], results[0].type.templated_types)
        self.assertEqual(False, results[0].type.pointer)
        self.assertEqual(False, results[0].type.reference)
        self.assertEqual(True, results[0].type.array)
        self.assertEqual('bar', results[0].name)

        self.assertEqual(['mutable'], results[1].type.modifiers)
        self.assertEqual('char', results[1].type.name)
        self.assertEqual([], results[1].type.templated_types)
        self.assertEqual(True, results[1].type.pointer)
        self.assertEqual(False, results[1].type.reference)
        self.assertEqual(False, results[1].type.array)
        self.assertEqual('foo', results[1].name)

        self.assertEqual(['volatile'], results[2].type.modifiers)
        self.assertEqual('Bar', results[2].type.name)
        self.assertEqual([], results[2].type.templated_types)
        self.assertEqual(False, results[2].type.pointer)
        self.assertEqual(True, results[2].type.reference)
        self.assertEqual(False, results[2].type.array)
        self.assertEqual('babar', results[2].name)

    def test_arrayWithClass(self):
        tokens = get_tokens('Bar[] bar')
        results = self.converter.to_parameters(list(tokens))
        self.assertEqual(1, len(results))

        self.assertEqual([], results[0].type.modifiers)
        self.assertEqual('Bar', results[0].type.name)
        self.assertEqual([], results[0].type.templated_types)
        self.assertEqual(False, results[0].type.pointer)
        self.assertEqual(False, results[0].type.reference)
        self.assertEqual(True, results[0].type.array)
        self.assertEqual('bar', results[0].name)

    def test_multipleArgs(self):
        tokens = get_tokens('const volatile Fool* data, int bar, enum X foo')
        results = self.converter.to_parameters(list(tokens))
        self.assertEqual(3, len(results))

        self.assertEqual(['const', 'volatile'], results[0].type.modifiers)
        self.assertEqual('Fool', results[0].type.name)
        self.assertEqual([], results[0].type.templated_types)
        self.assertEqual(True, results[0].type.pointer)
        self.assertEqual(False, results[0].type.reference)
        self.assertEqual('data', results[0].name)

        self.assertEqual([], results[1].type.modifiers)
        self.assertEqual('int', results[1].type.name)
        self.assertEqual([], results[1].type.templated_types)
        self.assertEqual(False, results[1].type.pointer)
        self.assertEqual(False, results[1].type.reference)
        self.assertEqual('bar', results[1].name)

        self.assertEqual(['enum'], results[2].type.modifiers)
        self.assertEqual('X', results[2].type.name)
        self.assertEqual([], results[2].type.templated_types)
        self.assertEqual(False, results[2].type.pointer)
        self.assertEqual(False, results[2].type.reference)
        self.assertEqual('foo', results[2].name)

    def test_simpleTemplateBegin(self):
        tokens = get_tokens('pair<int, int> data, int bar')
        results = self.converter.to_parameters(list(tokens))
        self.assertEqual(2, len(results), repr(results))

        self.assertEqual([], results[0].type.modifiers)
        self.assertEqual('pair', results[0].type.name)
        self.assertEqual([Type('int'), Type('int')],
                         results[0].type.templated_types)
        self.assertEqual(False, results[0].type.pointer)
        self.assertEqual(False, results[0].type.reference)
        self.assertEqual('data', results[0].name)

        self.assertEqual([], results[1].type.modifiers)
        self.assertEqual('int', results[1].type.name)
        self.assertEqual([], results[1].type.templated_types)
        self.assertEqual(False, results[1].type.pointer)
        self.assertEqual(False, results[1].type.reference)
        self.assertEqual('bar', results[1].name)

    def test_simpleWithInitializers(self):
        tokens = get_tokens('Fool* data = NULL')
        results = self.converter.to_parameters(list(tokens))
        self.assertEqual(1, len(results))

        self.assertEqual([], results[0].type.modifiers)
        self.assertEqual('Fool', results[0].type.name)
        self.assertEqual([], results[0].type.templated_types)
        self.assertEqual(True, results[0].type.pointer)
        self.assertEqual(False, results[0].type.reference)
        self.assertEqual(False, results[0].type.array)
        self.assertEqual('data', results[0].name)
        self.assertEqual([Token('NULL')], results[0].default)


class TypeConverterToTypeTest(unittest.TestCase):

    def setUp(self):
        self.converter = ast.TypeConverter([])

    def test_simple(self):
        tokens = get_tokens('Bar')
        result = self.converter.to_type(list(tokens))
        self.assertEqual(1, len(result))
        self.assertEqual(Type('Bar'), result[0])

    def test_template(self):
        tokens = get_tokens('Bar<Foo>')
        result = self.converter.to_type(list(tokens))
        self.assertEqual(1, len(result))
        self.assertEqual(Type('Bar', templated_types=[Type('Foo')]),
                         result[0])

    def test_templateWithMultipleArgs(self):
        tokens = get_tokens('Bar<Foo, Blah, Bling>')
        result = self.converter.to_type(list(tokens))
        self.assertEqual(1, len(result))
        types = [Type('Foo'), Type('Blah'), Type('Bling')]
        self.assertEqual(Type('Bar', templated_types=types), result[0])

    def test_templateWithMultipleTemplateArgsStart(self):
        tokens = get_tokens('Bar<Foo<x>, Blah, Bling>')
        result = self.converter.to_type(list(tokens))
        self.assertEqual(1, len(result))
        types = [Type('Foo', templated_types=[Type('x')]),
                 Type('Blah'),
                 Type('Bling')]
        self.assertEqual(types[0], result[0].templated_types[0])
        self.assertEqual(types[1], result[0].templated_types[1])
        self.assertEqual(types[2], result[0].templated_types[2])
        self.assertEqual(Type('Bar', templated_types=types), result[0])

    def test_templateWithMultipleTemplateArgsMid(self):
        tokens = get_tokens('Bar<Foo, Blah<x>, Bling>')
        result = self.converter.to_type(list(tokens))
        self.assertEqual(1, len(result))
        types = [Type('Foo'),
                 Type('Blah', templated_types=[Type('x')]),
                 Type('Bling')]
        self.assertEqual(Type('Bar', templated_types=types), result[0])

    def test_templateWithMultipleTemplateArgsEnd(self):
        tokens = get_tokens('Bar<Foo, Blah, Bling<x> >')
        result = self.converter.to_type(list(tokens))
        self.assertEqual(1, len(result))
        types = [Type('Foo'),
                 Type('Blah'),
                 Type('Bling', templated_types=[Type('x')])]
        self.assertEqual(Type('Bar', templated_types=types), result[0])


class TypeConverterCreateReturnTypeTest(unittest.TestCase):

    def setUp(self):
        self.converter = ast.TypeConverter([])

    def test_empty(self):
        self.assertEqual(None, self.converter.create_return_type(None))
        self.assertEqual(None, self.converter.create_return_type([]))

    def test_simple(self):
        tokens = get_tokens('Bar')
        result = self.converter.create_return_type(list(tokens))
        self.assertEqual(Type('Bar'), result)

    def test_array(self):
        tokens = get_tokens('Bar[]')
        result = self.converter.create_return_type(list(tokens))
        self.assertEqual(Type('Bar', array=True), result)

    def test_const_pointer(self):
        tokens = get_tokens('const Bar*')
        result = self.converter.create_return_type(list(tokens))
        self.assertEqual(Type('Bar', modifiers=['const'], pointer=True),
                         result)

    def test_const_class_pointer(self):
        tokens = get_tokens('const class Bar*')
        result = self.converter.create_return_type(list(tokens))
        modifiers = ['const', 'class']
        self.assertEqual(Type('Bar', modifiers=modifiers, pointer=True),
                         result)

    def test_template(self):
        tokens = get_tokens('const pair<int, NS::Foo>*')
        result = self.converter.create_return_type(list(tokens))
        templated_types = [Type('int'), Type('NS::Foo')]
        self.assertEqual(Type('pair', modifiers=['const'],
                              templated_types=templated_types, pointer=True),
                         result)


class AstBuilderGetTemplatedTypesTest(unittest.TestCase):

    def test_simple(self):
        builder = MakeBuilder('T> class')
        result = builder._get_templated_types()
        self.assertEqual(1, len(result))
        self.assertEqual((None, None), result['T'])

    def test_multiple(self):
        builder = MakeBuilder('T, U> class')
        result = builder._get_templated_types()
        self.assertEqual(2, len(result))
        self.assertEqual((None, None), result['T'])
        self.assertEqual((None, None), result['U'])

    def test_multipleWithTypename(self):
        builder = MakeBuilder('typename T, typename U> class')
        result = builder._get_templated_types()
        self.assertEqual(2, len(result))
        self.assertEqual((None, None), result['T'])
        self.assertEqual((None, None), result['U'])

    def test_multipleWithTypenameAndDefaults(self):
        builder = MakeBuilder('typename T=XX, typename U=YY> class')
        result = builder._get_templated_types()
        self.assertEqual(2, len(result))
        self.assertEqual(None, result['T'][0])
        self.assertEqual(1, len(result['T'][1]))
        self.assertEqual('XX', result['T'][1][0].name)
        self.assertEqual(None, result['U'][0])
        self.assertEqual(1, len(result['U'][1]))
        self.assertEqual('YY', result['U'][1][0].name)

    def test_multipleWithUserDefinedTypeName(self):
        builder = MakeBuilder('class C, Type t> class')
        result = builder._get_templated_types()
        self.assertEqual(2, len(result))
        self.assertEqual((None, None), result['C'])
        self.assertEqual('Type', result['t'][0].name)


class AstBuilderIntegrationTest(unittest.TestCase):

    """Unlike the other test cases in this file, this test case is meant to be
    an integration test.

    It doesn't test any individual method. It tests whole code blocks.

    """

    # TODO(nnorwitz): add lots more tests.

    def test_struct_variable_declaration(self):
        nodes = list(MakeBuilder('struct Foo foo;').generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(
            VariableDeclaration('foo', Type('Foo', modifiers=['struct'])),
            nodes[0])

    def test_anon_typedef(self):
        nodes = list(
            MakeBuilder('typedef struct { int zz; } AnonStruct;').generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(
            Typedef('AnonStruct',
                    alias=[Struct(None,
                                  body=[VariableDeclaration('zz',
                                                            Type('int'))])]),
            nodes[0])

    def test_typedef(self):
        nodes = list(
            MakeBuilder('typedef struct _IplImage IplImage;').generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Typedef('IplImage', alias=[Struct('_IplImage')]),
                         nodes[0])

    def test_class_forward_declaration(self):
        nodes = list(MakeBuilder('class Foo;').generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', body=None), nodes[0])

    def test_struct_forward_declaration(self):
        nodes = list(MakeBuilder('struct Foo;').generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Struct('Foo', body=None), nodes[0])

    def test_class_empty_body(self):
        nodes = list(MakeBuilder('class Foo {};').generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', body=[]), nodes[0])

    def test_struct_empty_body(self):
        nodes = list(MakeBuilder('struct Foo {};').generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Struct('Foo', body=[]), nodes[0])

    def test_class_exported(self):
        nodes = list(MakeBuilder('class DLLEXPORT Foo {};').generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', body=[]), nodes[0])

    def test_struct_exported(self):
        nodes = list(MakeBuilder('struct DLLEXPORT Foo {};').generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Struct('Foo', body=[]), nodes[0])

    def test_class_in_namespace_single(self):
        nodes = list(MakeBuilder('namespace N { class Foo; }').generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', namespace=['N']), nodes[0])

    def test_class_in_namespace_multiple(self):
        code = 'namespace A { namespace B { namespace C { class Foo; }}}'
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', namespace=['A', 'B', 'C']), nodes[0])

    def test_class_in_namespace_multipleWithOneClosed(self):
        code = 'namespace A { namespace B {} namespace C { class Foo; }}'
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', namespace=['A', 'C']), nodes[0])

    def test_class_in_anonymous_namespace_single(self):
        nodes = list(MakeBuilder('namespace { class Foo; }').generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', namespace=[None]), nodes[0])

    def test_class_in_anonymous_namespace_multiple(self):
        code = 'namespace A { namespace { namespace B { class Foo; }}}'
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', namespace=['A', None, 'B']), nodes[0])

    def test_template_typedef(self):
        code = 'class Foo; typedef Bar<Foo*> v;'
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(2, len(nodes))
        self.assertEqual(Class('Foo'), nodes[0])
        self.assertEqual(
            Typedef('v',
                    alias=Type('Bar',
                               templated_types=[Type('Foo', pointer=True)])),
            nodes[1])

    def test_operators(self):
        for operator in ('=', '+=', '-=', '*=', '==', '!=', '()', '[]'):
            code = 'void Foo::operator%s();' % operator
            nodes = list(MakeBuilder(code).generate())
            self.assertEqual(1, len(nodes))
            self.assertEqual(Method(('operator%s' % operator), list(get_tokens('Foo')),
                                    list(get_tokens('void')), []), nodes[0])

    def test_class_no_anonymous_namespace(self):
        nodes = list(MakeBuilder('class Foo;').generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', namespace=[]), nodes[0])

    def test_class_virtual_inheritance(self):
        code = 'class Foo : public virtual Bar {};'
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', bases=[Type('Bar')], body=[]), nodes[0])

    def test_class_virtual_inheritance_reverse(self):
        code = 'class Foo : virtual public Bar {};'
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', bases=[Type('Bar')], body=[]), nodes[0])

    def test_class_virtual_inline_destructor(self):
        code = 'class Foo { virtual inline ~Foo(); };'
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(1, len(nodes))
        function = nodes[0].body[0]
        expected = Function('Foo', [], [],
                            modifiers=ast.FUNCTION_DTOR | ast.FUNCTION_VIRTUAL)
        self.assertEqual(expected.return_type, function.return_type)
        self.assertEqual(expected, function)
        self.assertEqual(Class('Foo', body=[expected]), nodes[0])

    def test_class_colon_separated_class_name_and_inline_dtor(self):
        method_body = 'XXX(1) << "should work";'
        code = 'class Foo::Bar { ~Bar() { %s } };' % method_body
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(1, len(nodes))
        function = nodes[0].body[0]
        expected = Function('Bar', [], [], body=list(get_tokens(method_body)),
                            modifiers=ast.FUNCTION_DTOR)
        self.assertEqual(expected.return_type, function.return_type)
        self.assertEqual(expected, function)
        self.assertEqual(Class('Foo::Bar', body=[expected]), nodes[0])

    def test_class_handles_struct_rebind(self):
        code = """
        template <typename T, typename Alloc = std::allocator<T> >
        class AnotherAllocator : public Alloc {
            template <class U> struct rebind {
            };
        };
        """
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('AnotherAllocator', bases=[Type('Alloc')],
                               body=[Struct('rebind', body=[])]),
                         nodes[0])
        # TODO(nnorwitz): assert more about the body of the class.

    def test_function_parses_operator_bracket(self):
        code = """
        class A {
            const B& operator[](const int i) const {}
        };
        """
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(1, len(nodes))
        function = nodes[0].body[0]
        expected = Function('operator[]', list(get_tokens('const B&')),
                            list(get_tokens('const int i')), body=[],
                            modifiers=ast.FUNCTION_CONST)
        self.assertEqual(expected.return_type, function.return_type)
        self.assertEqual(expected, function)
        self.assertEqual(Class('A', body=[expected]), nodes[0])

    def test_function_parses_template_with_array_access(self):
        code = """
        template <typename T, size_t N>
        char (&ASH(T (&seq)[N]))[N];
        """
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(1, len(nodes))
        # TODO(nnorwitz): this doesn't parse correctly, but at least
        # it doesn't raise an exception anymore. Improve the parsing.

    def test_method_with_template_class_works(self):
        code = """
        template <class T>
        inline void EVM::VH<T>::Write() {
        }
        """
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(1, len(nodes))
        expected = Method('Write', list(get_tokens('EVM::VH<T>')),
                          list(get_tokens('inline void')), [],
                          templated_types={'T': (None, None)},
                          body=[])
        self.assertEqual(expected.return_type, nodes[0].return_type)
        self.assertEqual(expected.in_class, nodes[0].in_class)
        self.assertEqual(expected.templated_types, nodes[0].templated_types)
        self.assertEqual(expected, nodes[0])

    def test_method_with_template_class_with2args_works(self):
        code = """
        template <class T, typename U>
        inline void EVM::VH<T, U>::Write() {
        }
        """
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(1, len(nodes))
        expected = Method('Write', list(get_tokens('EVM::VH<T, U>')),
                          list(get_tokens('inline void')), [],
                          templated_types={'T': (None, None),
                                           'U': (None, None)},
                          body=[])
        self.assertEqual(expected.return_type, nodes[0].return_type)
        self.assertEqual(expected.in_class, nodes[0].in_class)
        self.assertEqual(expected.templated_types, nodes[0].templated_types)
        self.assertEqual(expected, nodes[0])

    def test_method_with_template_class_with3args_works(self):
        code = """
        template <class CT, class IT, class DT>
        DT* Worker<CT, IT, DT>::Create() {
        }
        """
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(1, len(nodes))
        tt = (None, None)
        expected = Method('Create', list(get_tokens('Worker<CT, IT, DT>')),
                          list(get_tokens('DT*')), [],
                          templated_types={'CT': tt, 'IT': tt, 'DT': tt},
                          body=[])
        self.assertEqual(expected.return_type, nodes[0].return_type)
        self.assertEqual(expected.in_class, nodes[0].in_class)
        self.assertEqual(expected.templated_types, nodes[0].templated_types)
        self.assertEqual(expected, nodes[0])

    def test_include_with_backslash_continuation_works(self):
        nodes = list(MakeBuilder('#include \\\n  "test.h"').generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Include('test.h'), nodes[0])


if __name__ == '__main__':
    unittest.main()
