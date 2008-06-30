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

__author__ = 'nnorwitz@google.com (Neal Norwitz)'


from test import test_support
import unittest

from cpp import ast
from cpp import tokenize


def _InstallGenericEqual(cls, attrs):
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


def _InstallEqualMethods():
    """Install __eq__ methods on the appropriate objects used for testing."""
    _InstallGenericEqual(tokenize.Token, 'name')
    _InstallGenericEqual(ast.Class, 'name bases templated_types namespace')
    _InstallGenericEqual(ast.Type, ('name templated_types modifiers '
                                    'reference pointer array'))
    _InstallGenericEqual(ast.Method, ('name in_class return_type parameters '
                                      'modifiers templated_types '
                                      'body namespace'))
_InstallEqualMethods()


def GetTokens(code_string):
    return tokenize.GetTokens(code_string + '\n')


def MakeBuilder(code_string):
    """Convenience function to make an AstBuilder from a code snippet.."""
    return ast.AstBuilder(GetTokens(code_string), '<test>')


def Token(name, start=0, end=0, token_type=tokenize.NAME):
    return tokenize.Token(token_type, name, start, end)


def Class(name, start=0, end=0, bases=None, body=None, templated_types=None,
          namespace=None):
    if namespace is None:
        namespace = []
    return ast.Class(start, end, name, bases, templated_types, body, namespace)


def Type(name, start=0, end=0, templated_types=None, modifiers=None,
          reference=False, pointer=False, array=False):
    if templated_types is None:
        templated_types = []
    if modifiers is None:
        modifiers = []
    return ast.Type(start, end, name, templated_types, modifiers,
                     reference, pointer, array)


def Method(name, in_class, return_type, parameters, start=0, end=0,
           modifiers=0, templated_types=None, body=None, namespace=None):
    if templated_types is None:
        templated_types = []
    if body is None:
        body = []
    if namespace is None:
        namespace = []
    return ast.Method(start, end, name, in_class, return_type, parameters,
                      modifiers, templated_types, body, namespace)


class TypeConverter_DeclarationToPartsTest(unittest.TestCase):

    def setUp(self):
        self.converter = ast.TypeConverter([])

    def testSimple(self):
        tokens = GetTokens('Fool data')
        name, type_name, templated_types, modifiers, default, other_tokens = \
              self.converter.DeclarationToParts(list(tokens), True)
        self.assertEqual('data', name)
        self.assertEqual('Fool', type_name)
        self.assertEqual([], templated_types)
        self.assertEqual([], modifiers)

    def testSimpleModifiers(self):
        tokens = GetTokens('const volatile Fool data')
        name, type_name, templated_types, modifiers, default, other_tokens = \
              self.converter.DeclarationToParts(list(tokens), True)
        self.assertEqual('data', name)
        self.assertEqual('Fool', type_name)
        self.assertEqual([], templated_types)
        self.assertEqual(['const', 'volatile'], modifiers)

    def testSimpleArray(self):
        tokens = GetTokens('Fool[] data')
        name, type_name, templated_types, modifiers, default, other_tokens = \
              self.converter.DeclarationToParts(list(tokens), True)
        self.assertEqual('data', name)
        self.assertEqual('Fool', type_name)
        self.assertEqual([], templated_types)
        self.assertEqual([], modifiers)

    def testSimpleTemplate(self):
        tokens = GetTokens('Fool<tt> data')
        name, type_name, templated_types, modifiers, default, other_tokens = \
              self.converter.DeclarationToParts(list(tokens), True)
        self.assertEqual('data', name)
        self.assertEqual('Fool', type_name)
        self.assertEqual([Type('tt')], templated_types)
        self.assertEqual([], modifiers)


class TypeConverter_ToParametersTest(unittest.TestCase):

    def setUp(self):
        self.converter = ast.TypeConverter([])

    def testReallySimple(self):
        tokens = GetTokens('int bar')
        results = self.converter.ToParameters(list(tokens))
        self.assertEqual(1, len(results))

        self.assertEqual([], results[0].type.modifiers)
        self.assertEqual('int', results[0].type.name)
        self.assertEqual([], results[0].type.templated_types)
        self.assertEqual(False, results[0].type.pointer)
        self.assertEqual(False, results[0].type.reference)
        self.assertEqual(False, results[0].type.array)
        self.assertEqual('bar', results[0].name)

    def testArray(self):
        tokens = GetTokens('int[] bar')
        results = self.converter.ToParameters(list(tokens))
        self.assertEqual(1, len(results))

        self.assertEqual([], results[0].type.modifiers)
        self.assertEqual('int', results[0].type.name)
        self.assertEqual([], results[0].type.templated_types)
        self.assertEqual(False, results[0].type.pointer)
        self.assertEqual(False, results[0].type.reference)
        self.assertEqual(True, results[0].type.array)
        self.assertEqual('bar', results[0].name)

    def testArrayPointerReference(self):
        params = 'const int[] bar, mutable char* foo, volatile Bar& babar'
        tokens = GetTokens(params)
        results = self.converter.ToParameters(list(tokens))
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

    def testArrayWithClass(self):
        tokens = GetTokens('Bar[] bar')
        results = self.converter.ToParameters(list(tokens))
        self.assertEqual(1, len(results))

        self.assertEqual([], results[0].type.modifiers)
        self.assertEqual('Bar', results[0].type.name)
        self.assertEqual([], results[0].type.templated_types)
        self.assertEqual(False, results[0].type.pointer)
        self.assertEqual(False, results[0].type.reference)
        self.assertEqual(True, results[0].type.array)
        self.assertEqual('bar', results[0].name)

    def testMultipleArgs(self):
        tokens = GetTokens('const volatile Fool* data, int bar, enum X foo')
        results = self.converter.ToParameters(list(tokens))
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

    def testSimpleTemplateBegin(self):
        tokens = GetTokens('pair<int, int> data, int bar')
        results = self.converter.ToParameters(list(tokens))
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

    def testSimpleWithInitializers(self):
        tokens = GetTokens('Fool* data = NULL')
        results = self.converter.ToParameters(list(tokens))
        self.assertEqual(1, len(results))

        self.assertEqual([], results[0].type.modifiers)
        self.assertEqual('Fool', results[0].type.name)
        self.assertEqual([], results[0].type.templated_types)
        self.assertEqual(True, results[0].type.pointer)
        self.assertEqual(False, results[0].type.reference)
        self.assertEqual(False, results[0].type.array)
        self.assertEqual('data', results[0].name)
        self.assertEqual([Token('NULL')], results[0].default)


class TypeConverter_ToTypeTest(unittest.TestCase):

    def setUp(self):
        self.converter = ast.TypeConverter([])

    def testSimple(self):
        tokens = GetTokens('Bar')
        result = self.converter.ToType(list(tokens))
        self.assertEqual(1, len(result))
        self.assertEqual(Type('Bar'), result[0])

    def testTemplate(self):
        tokens = GetTokens('Bar<Foo>')
        result = self.converter.ToType(list(tokens))
        self.assertEqual(1, len(result))
        self.assertEqual(Type('Bar', templated_types=[Type('Foo')]),
                         result[0])

    def testTemplateWithMultipleArgs(self):
        tokens = GetTokens('Bar<Foo, Blah, Bling>')
        result = self.converter.ToType(list(tokens))
        self.assertEqual(1, len(result))
        types = [Type('Foo'), Type('Blah'), Type('Bling')]
        self.assertEqual(Type('Bar', templated_types=types), result[0])

    def testTemplateWithMultipleTemplateArgsStart(self):
        tokens = GetTokens('Bar<Foo<x>, Blah, Bling>')
        result = self.converter.ToType(list(tokens))
        self.assertEqual(1, len(result))
        types = [Type('Foo', templated_types=[Type('x')]),
                 Type('Blah'),
                 Type('Bling')]
        self.assertEqual(types[0], result[0].templated_types[0])
        self.assertEqual(types[1], result[0].templated_types[1])
        self.assertEqual(types[2], result[0].templated_types[2])
        self.assertEqual(Type('Bar', templated_types=types), result[0])

    def testTemplateWithMultipleTemplateArgsMid(self):
        tokens = GetTokens('Bar<Foo, Blah<x>, Bling>')
        result = self.converter.ToType(list(tokens))
        self.assertEqual(1, len(result))
        types = [Type('Foo'),
                 Type('Blah', templated_types=[Type('x')]),
                 Type('Bling')]
        self.assertEqual(Type('Bar', templated_types=types), result[0])

    def testTemplateWithMultipleTemplateArgsEnd(self):
        tokens = GetTokens('Bar<Foo, Blah, Bling<x> >')
        result = self.converter.ToType(list(tokens))
        self.assertEqual(1, len(result))
        types = [Type('Foo'),
                 Type('Blah'),
                 Type('Bling', templated_types=[Type('x')])]
        self.assertEqual(Type('Bar', templated_types=types), result[0])


class TypeConverter_CreateReturnTypeTest(unittest.TestCase):

    def setUp(self):
        self.converter = ast.TypeConverter([])

    def testEmpty(self):
        self.assertEqual(None, self.converter.CreateReturnType(None))
        self.assertEqual(None, self.converter.CreateReturnType([]))

    def testSimple(self):
        tokens = GetTokens('Bar')
        result = self.converter.CreateReturnType(list(tokens))
        self.assertEqual(Type('Bar'), result)

    def testArray(self):
        tokens = GetTokens('Bar[]')
        result = self.converter.CreateReturnType(list(tokens))
        self.assertEqual(Type('Bar', array=True), result)

    def testConstPointer(self):
        tokens = GetTokens('const Bar*')
        result = self.converter.CreateReturnType(list(tokens))
        self.assertEqual(Type('Bar', modifiers=['const'], pointer=True),
                         result)

    def testConstClassPointer(self):
        tokens = GetTokens('const class Bar*')
        result = self.converter.CreateReturnType(list(tokens))
        modifiers = ['const', 'class']
        self.assertEqual(Type('Bar', modifiers=modifiers, pointer=True),
                         result)

    def testTemplate(self):
        tokens = GetTokens('const pair<int, NS::Foo>*')
        result = self.converter.CreateReturnType(list(tokens))
        templated_types = [Type('int'), Type('NS::Foo')]
        self.assertEqual(Type('pair', modifiers=['const'],
                              templated_types=templated_types, pointer=True),
                         result)


class AstBuilder_GetVarTokensUpToTest(unittest.TestCase):
    pass  # TODO(nnorwitz): implement.


class AstBuilder_SkipIf0BlocksTest(unittest.TestCase):
    pass  # TODO(nnorwitz): implement.


class AstBuilder_GetMatchingCharTest(unittest.TestCase):
    pass  # TODO(nnorwitz): implement.


class AstBuilderGetNameTest(unittest.TestCase):
    pass  # TODO(nnorwitz): implement.


class AstBuilder_GetNestedTypesTest(unittest.TestCase):
    pass  # TODO(nnorwitz): implement.


class AstBuilder_GetTemplatedTypesTest(unittest.TestCase):

    def testSimple(self):
        builder = MakeBuilder('T> class')
        result = builder._GetTemplatedTypes()
        self.assertEqual(1, len(result))
        self.assertEqual(None, result['T'])

    def testMultiple(self):
        builder = MakeBuilder('T, U> class')
        result = builder._GetTemplatedTypes()
        self.assertEqual(2, len(result))
        self.assertEqual(None, result['T'])
        self.assertEqual(None, result['U'])

    def testMultipleWithTypename(self):
        builder = MakeBuilder('typename T, typename U> class')
        result = builder._GetTemplatedTypes()
        self.assertEqual(2, len(result))
        self.assertEqual(None, result['T'])
        self.assertEqual(None, result['U'])

    def testMultipleWithTypenameAndDefaults(self):
        builder = MakeBuilder('typename T=XX, typename U=YY> class')
        result = builder._GetTemplatedTypes()
        self.assertEqual(2, len(result))
        self.assertEqual(1, len(result['T']))
        self.assertEqual('XX', result['T'][0].name)
        self.assertEqual(1, len(result['U']))
        self.assertEqual('YY', result['U'][0].name)


class AstBuilder_GetBasesTest(unittest.TestCase):
    pass  # TODO(nnorwitz): implement.


class AstBuilder_GetClassTest(unittest.TestCase):
    pass  # TODO(nnorwitz): implement.


class AstBuilderIntegrationTest(unittest.TestCase):
    """Unlike the other test cases in this file, this test case is
    meant to be an integration test.  It doesn't test any individual
    method.  It tests whole code blocks.
    """

    # TODO(nnorwitz): add lots more tests.

    def testClass_ForwardDeclaration(self):
        nodes = list(MakeBuilder('class Foo;').Generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', body=None), nodes[0])

    def testClass_EmptyBody(self):
        nodes = list(MakeBuilder('class Foo {};').Generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', body=[]), nodes[0])

    def testClass_InNamespaceSingle(self):
        nodes = list(MakeBuilder('namespace N { class Foo; }').Generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', namespace=['N']), nodes[0])

    def testClass_InNamespaceMultiple(self):
        code = 'namespace A { namespace B { namespace C { class Foo; }}}'
        nodes = list(MakeBuilder(code).Generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', namespace=['A', 'B', 'C']), nodes[0])

    def testClass_InAnonymousNamespaceSingle(self):
        nodes = list(MakeBuilder('namespace { class Foo; }').Generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', namespace=[None]), nodes[0])

    def testClass_InAnonymousNamespaceMultiple(self):
        code = 'namespace A { namespace { namespace B { class Foo; }}}'
        nodes = list(MakeBuilder(code).Generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', namespace=['A', None, 'B']), nodes[0])

    def testClass_NoAnonymousNamespace(self):
        nodes = list(MakeBuilder('class Foo;').Generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', namespace=[]), nodes[0])

    def testClass_VirtualInheritance(self):
        cpp_code = 'class Foo : public virtual Bar {};'
        nodes = list(MakeBuilder(cpp_code).Generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', bases=[Type('Bar')]), nodes[0])

    def testClass_ColonSeparatedClassNameAndInlineDtor(self):
        cpp_code = 'class Foo::Bar { ~Bar() { XXX(1) << "should work"; } };'
        nodes = list(MakeBuilder(cpp_code).Generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo::Bar', body=[]), nodes[0])
        # TODO(nnorwitz): assert more about the body of the class.

    def testClass_HandlesStructRebind(self):
        cpp_code = """
        template <typename T, typename Alloc = std::allocator<T> >
        class AnotherAllocator : public Alloc {
            template <class U> struct rebind {
            };
        };
        """
        nodes = list(MakeBuilder(cpp_code).Generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('AnotherAllocator', bases=[Type('Alloc')]),
                         nodes[0])
        # TODO(nnorwitz): assert more about the body of the class.

    def testMethod_WithTemplateClassWorks(self):
        cpp_code = """
        template <class T>
        inline void EVM::VH<T>::Write() { 
        } 
        """
        nodes = list(MakeBuilder(cpp_code).Generate())
        self.assertEqual(1, len(nodes))
        expected = Method('Write', list(GetTokens('EVM::VH<T>')),
                          list(GetTokens('inline void')), [],
                          templated_types={'T': None})
        self.assertEqual(expected.return_type, nodes[0].return_type)
        self.assertEqual(expected.in_class, nodes[0].in_class)
        self.assertEqual(expected.templated_types, nodes[0].templated_types)
        self.assertEqual(expected, nodes[0])

    def testMethod_WithTemplateClassWith2ArgsWorks(self):
        cpp_code = """
        template <class T, typename U>
        inline void EVM::VH<T, U>::Write() { 
        } 
        """
        nodes = list(MakeBuilder(cpp_code).Generate())
        self.assertEqual(1, len(nodes))
        expected = Method('Write', list(GetTokens('EVM::VH<T, U>')),
                          list(GetTokens('inline void')), [],
                          templated_types={'T': None, 'U': None})
        self.assertEqual(expected.return_type, nodes[0].return_type)
        self.assertEqual(expected.in_class, nodes[0].in_class)
        self.assertEqual(expected.templated_types, nodes[0].templated_types)
        self.assertEqual(expected, nodes[0])

    def testMethod_WithTemplateClassWith2ArgsWorks(self):
        cpp_code = """
        template <class CT, class IT, class DT>
        DT* Worker<CT, IT, DT>::Create() { 
        } 
        """
        nodes = list(MakeBuilder(cpp_code).Generate())
        self.assertEqual(1, len(nodes))
        expected = Method('Create', list(GetTokens('Worker<CT, IT, DT>')),
                          list(GetTokens('DT*')), [],
                          templated_types={'CT': None, 'IT': None, 'DT': None})
        self.assertEqual(expected.return_type, nodes[0].return_type)
        self.assertEqual(expected.in_class, nodes[0].in_class)
        self.assertEqual(expected.templated_types, nodes[0].templated_types)
        self.assertEqual(expected, nodes[0])


def test_main():
    tests = [t for t in globals().values()
             if isinstance(t, type) and issubclass(t, unittest.TestCase)]
    test_support.run_unittest(*tests)


if __name__ == '__main__':
    test_main()
