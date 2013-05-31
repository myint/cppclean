#!/usr/bin/env python
#
# Copyright 2007 Neal Norwitz
# Portions Copyright 2007 Google Inc.
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

"""Symbol Table test."""

__author__ = 'nnorwitz@google.com (Neal Norwitz)'


try:
    # Python 2.x
    from test import test_support
except ImportError:
    # Python 3.x
    from test import support as test_support
import unittest

from cpp import symbols


class SymbolTableTest(unittest.TestCase):

    def _AddSymbol(self, st, name, ns_stack):
        """Helper for the LookupSymbol test methods."""
        node = object()
        module = object()
        st.AddSymbol(name, ns_stack, node, module)
        return node, module

    def testLookupSymbolWithGlobalThatDoesNotExist(self):
        st = symbols.SymbolTable()
        self.assertRaises(symbols.Error, st.LookupSymbol, 'foo', None)

    def testLookupSymbolWithNamespaceThatDoesNotExist(self):
        st = symbols.SymbolTable()
        self.assertRaises(symbols.Error, st.LookupSymbol, 'foo', ['n'])

    def testLookupSymbolWithGlobalThatExists(self):
        st = symbols.SymbolTable()
        node, module = self._AddSymbol(st, 'foo', None)
        self.assertEqual((node, module), st.LookupSymbol('foo', None))

    def testLookupSymbolWithComplexGlobalThatExists(self):
        st = symbols.SymbolTable()
        node, module = self._AddSymbol(st, 'foo', ['ns1', 'ns2'])
        self.assertEqual((node, module),
                         st.LookupSymbol('::ns1::ns2::foo', None))
        self.assertEqual((node, module),
                         st.LookupSymbol('ns1::ns2::foo', None))

    def testLookupSymbolInNamespaces(self):
        st = symbols.SymbolTable()

        # 3 nested namespaces, all contain the same symbol (foo).
        ns = ['ns1', 'ns2', 'ns3']
        AddSymbol = self._AddSymbol
        # Also add foo to the global namespace.
        ns_symbols = [AddSymbol(st, 'foo', None)] + \
                     [AddSymbol(st, 'foo', ns[:i+1]) for i in range(len(ns))]

        # Verify global lookup works.
        self.assertEqual(ns_symbols[0], st.LookupSymbol('::foo', ns))

        # Verify looking up relative symbols work.
        self.assertEqual(ns_symbols[1], st.LookupSymbol('foo', ns[:1]))
        self.assertEqual(ns_symbols[2], st.LookupSymbol('foo', ns[:2]))
        self.assertEqual(ns_symbols[3], st.LookupSymbol('foo', ns[:3]))
        bigger = ns + ['ns4', 'ns5']
        self.assertEqual(ns_symbols[3], st.LookupSymbol('foo', bigger))

        # Remove ns2 and verify that when looking for foo in ns2 it finds ns1.
        ns1 = st.namespaces['ns1']
        del ns1['ns2']
        self.assertEqual(ns_symbols[1], st.LookupSymbol('foo', ns[:2]))

    def test_Add(self):
        st = symbols.SymbolTable()
        node = object()
        module = object()
        namespace = {}
        symbol_name = 'foo'

        self.assertEqual(True, st._Add(symbol_name, namespace, node, module))
        self.assertEqual(1, len(namespace))
        self.assertEqual(['foo'], list(namespace.keys()))

        # Adding again should return False.
        self.assertEqual(False, st._Add(symbol_name, namespace, node, module))

    def testAddSymbolInGlobalNamespace(self):
        st = symbols.SymbolTable()
        node = object()
        module = object()
        ns_stack = None
        name = 'foo'

        self.assertEqual(True, st.AddSymbol(name, ns_stack, node, module))
        # Verify the symbol was added properly to the symbol table namespaces.
        self.assert_('foo' in st.namespaces[None])
        self.assertEqual((node, module), st.namespaces[None]['foo'])

        # Already added, verify we get false.
        self.assertEqual(False, st.AddSymbol(name, ns_stack, node, module))

    def testAddSymbolInNamespaceWithOneLevel(self):
        st = symbols.SymbolTable()
        node = object()
        module = object()
        ns_stack = ['ns-foo']
        name = 'foo'
        self.assertEqual(True, st.AddSymbol(name, ns_stack, node, module))
        # Verify the symbol was added properly to the symbol table namespaces.
        self.assert_('ns-foo' in st.namespaces)
        self.assert_('foo' in st.namespaces['ns-foo'])
        self.assertEqual((node, module), st.namespaces['ns-foo']['foo'])

        # Already added, verify we get false.
        self.assertEqual(False, st.AddSymbol(name, ns_stack, node, module))

    def testAddSymbolInNamespaceWithThreeLevels(self):
        st = symbols.SymbolTable()
        node = object()
        module = object()
        ns_stack = ['ns1', 'ns2', 'ns3']
        name = 'foo'

        self.assertEqual(True, st.AddSymbol(name, ns_stack, node, module))
        # Verify the symbol was added properly to the symbol table namespaces.
        self.assert_('ns1' in st.namespaces)
        self.assert_('ns2' in st.namespaces['ns1'])
        self.assert_('ns3' in st.namespaces['ns1']['ns2'])
        self.assert_('foo' in st.namespaces['ns1']['ns2']['ns3'])
        self.assertEqual((node, module),
                         st.namespaces['ns1']['ns2']['ns3']['foo'])

        # Now add something to ns1 and verify.
        ns_stack = ['ns1']
        name = 'something'
        self.assertEqual(True, st.AddSymbol(name, ns_stack, node, module))
        self.assert_('something' in st.namespaces['ns1'])
        self.assertEqual((node, module), st.namespaces['ns1']['something'])

        # Now add something to ns1::ns2 and verify.
        ns_stack = ['ns1', 'ns2']
        name = 'else'
        self.assertEqual(True, st.AddSymbol(name, ns_stack, node, module))
        self.assert_('else' in st.namespaces['ns1']['ns2'])
        self.assertEqual((node, module), st.namespaces['ns1']['ns2']['else'])

        # Now add something to the global namespace and verify.
        ns_stack = None
        name = 'global'
        self.assertEqual(True, st.AddSymbol(name, ns_stack, node, module))
        self.assert_('global' in st.namespaces[None])
        self.assertEqual((node, module), st.namespaces[None]['global'])

        # Verify table still has 2 elements (global namespace and ::ns1).
        self.assertEqual(2, len(st.namespaces))
        # Verify ns1 still has 2 elements (ns2 and 'something').
        self.assertEqual(2, len(st.namespaces['ns1']))
        # Verify ns2 still has 2 elements (ns3 and 'else').
        self.assertEqual(2, len(st.namespaces['ns1']['ns2']))
        # Verify ns3 still has 1 element ('foo').
        self.assertEqual(1, len(st.namespaces['ns1']['ns2']['ns3']))

    def testGetNamespace(self):
        # Setup.
        st = symbols.SymbolTable()
        node = object()
        module = object()
        ns_stack = ['ns1', 'ns2', 'ns3']
        name = 'foo'
        self.assertEqual(True, st.AddSymbol(name, ns_stack, node, module))

        # Verify.
        self.assertEqual([], st.GetNamespace([]))
        self.assertEqual(['ns1'], st.GetNamespace(['ns1']))
        self.assertEqual(['ns1'], st.GetNamespace(['ns1', 'foo']))
        self.assertEqual(['ns1'], st.GetNamespace(['ns1', 'foo']))
        self.assertEqual(['ns1'], st.GetNamespace(['ns1', 'foo', 'ns2']))
        self.assertEqual(['ns1', 'ns2'], st.GetNamespace(['ns1', 'ns2']))
        self.assertEqual(['ns1', 'ns2'], st.GetNamespace(['ns1', 'ns2', 'f']))
        self.assertEqual(['ns1', 'ns2'], st.GetNamespace(['ns1', 'ns2', 'f']))
        self.assertEqual(['ns1', 'ns2', 'ns3'],
                         st.GetNamespace(['ns1', 'ns2', 'ns3', 'f']))


def test_main():
    test_support.run_unittest(SymbolTableTest)


if __name__ == '__main__':
    test_main()
