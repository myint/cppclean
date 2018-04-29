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

"""Generate an Abstract Syntax Tree (AST) for C++."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os
import collections

from . import keywords
from . import tokenize


try:
    unicode
except NameError:
    unicode = str


__author__ = 'nnorwitz@google.com (Neal Norwitz)'


# TODO:
#  * Tokens should never be exported, need to convert to Nodes
#    (return types, parameters, etc.)
#  * Handle static class data for templatized classes
#  * Handle casts (both C++ and C-style)
#  * Handle conditions and loops (if/else, switch, for, while/do)
#
# TODO much, much later:
# * Handle #define
# * exceptions


FUNCTION_NONE = 0x00
FUNCTION_SPECIFIER = 0x01
FUNCTION_VIRTUAL = 0x02
FUNCTION_PURE_VIRTUAL = 0x04
FUNCTION_CTOR = 0x08
FUNCTION_DTOR = 0x10
FUNCTION_ATTRIBUTE = 0x20
FUNCTION_UNKNOWN_ANNOTATION = 0x40
FUNCTION_THROW = 0x80


class ParseError(Exception):

    """Raise exception on parsing problems."""


# TODO(nnorwitz): move AST nodes into a separate module.
class Node(object):

    """Base AST node."""

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def is_declaration(self):
        """Returns bool if this node is a declaration."""
        return False

    def is_definition(self):
        """Returns bool if this node is a definition."""
        return False

    def is_exportable(self):
        """Returns bool if this node exportable from a header file."""
        return False

    def _string_helper(self, name, suffix):
        return '%s(%d, %d, %s)' % (name, self.start, self.end, suffix)

    def __repr__(self):
        return unicode(self)


class Define(Node):

    def __init__(self, start, end, name, definition):
        Node.__init__(self, start, end)
        self.name = name
        self.definition = definition
        # TODO(christarazi):
        # Defines aren't bound to namespaces, so this is just a stopgap
        # solution.
        self.namespace = []

    def __str__(self):
        value = '%s %s' % (self.name, self.definition)
        return self._string_helper(self.__class__.__name__, value)

    def is_exportable(self):
        return True


class Include(Node):

    def __init__(self, start, end, filename, system):
        Node.__init__(self, start, end)
        self.filename = filename
        self.system = system

    def __str__(self):
        fmt = '"%s"'
        if self.system:
            fmt = '<%s>'
        return self._string_helper(self.__class__.__name__,
                                   fmt % self.filename)


class Expr(Node):

    def __init__(self, start, end, expr):
        Node.__init__(self, start, end)
        self.expr = expr

    def __str__(self):
        return self._string_helper(self.__class__.__name__, unicode(self.expr))


class Friend(Expr):

    def __init__(self, start, end, expr, namespace):
        Expr.__init__(self, start, end, expr)
        self.namespace = namespace[:]


class Using(Node):

    def __init__(self, start, end, names):
        Node.__init__(self, start, end)
        self.names = names

    def __str__(self):
        return self._string_helper(self.__class__.__name__,
                                   unicode(self.names))


class Parameter(Node):

    def __init__(self, start, end, name, parameter_type, default):
        Node.__init__(self, start, end)
        self.name = name
        self.type = parameter_type
        self.default = default

    def __str__(self):
        name = unicode(self.type)
        suffix = '%s %s' % (name, self.name)
        if self.default:
            suffix += ' = ' + ''.join([d.name for d in self.default])
        return self._string_helper(self.__class__.__name__, suffix)


class _GenericDeclaration(Node):

    def __init__(self, start, end, name, namespace):
        Node.__init__(self, start, end)
        self.name = name
        self.namespace = namespace[:]

    def full_name(self):
        prefix = ''
        names = [n for n in self.namespace if n is not None]
        if names:
            prefix = '::'.join(names) + '::'
        return prefix + self.name

    def _type_string_helper(self, suffix):
        if self.namespace:
            names = [n or '<anonymous>' for n in self.namespace]
            suffix += ' in ' + '::'.join(names)
        return self._string_helper(self.__class__.__name__, suffix)


# TODO(nnorwitz): merge with Parameter in some way?
class VariableDeclaration(_GenericDeclaration):

    def __init__(self, start, end, name, var_type, initial_value, namespace):
        _GenericDeclaration.__init__(self, start, end, name, namespace)
        self.type = var_type
        self.initial_value = initial_value

    def to_string(self):
        """Return a string that tries to reconstitute the variable decl."""
        suffix = '%s %s' % (self.type, self.name)
        if self.initial_value:
            suffix += ' = ' + self.initial_value
        return suffix

    def __str__(self):
        return self._string_helper(self.__class__.__name__, self.to_string())


class Typedef(_GenericDeclaration):

    def __init__(self, start, end, name, alias, namespace):
        _GenericDeclaration.__init__(self, start, end, name, namespace)
        self.alias = alias

    def is_definition(self):
        return True

    def is_exportable(self):
        return True

    def __str__(self):
        suffix = '%s, %s' % (self.name, self.alias)
        return self._type_string_helper(suffix)


class Enum(_GenericDeclaration):

    def __init__(self, start, end, name, fields, namespace):
        _GenericDeclaration.__init__(self, start, end, name, namespace)
        self.fields = fields

    def is_definition(self):
        return True

    def is_exportable(self):
        return True

    def __str__(self):
        suffix = '%s, {%s}' % (self.name, self.fields)
        return self._type_string_helper(suffix)


class Class(_GenericDeclaration):

    def __init__(self, start, end, name,
                 bases, templated_types, body, namespace):
        _GenericDeclaration.__init__(self, start, end, name, namespace)
        self.bases = bases
        self.body = body
        self.templated_types = templated_types

    def is_declaration(self):
        return self.bases is None and self.body is None

    def is_definition(self):
        return not self.is_declaration()

    def is_exportable(self):
        return not self.is_declaration()

    def __str__(self):
        name = self.name
        if self.templated_types:
            types = ','.join([t for t in self.templated_types])
            name += '<%s>' % types
        suffix = '%s, %s, %s' % (name, self.bases, self.body)
        return self._type_string_helper(suffix)


class Struct(Class):
    pass


class Union(Class):
    pass


class Function(_GenericDeclaration):

    def __init__(self, start, end, name, return_type, parameters,
                 specializations, modifiers, templated_types, body, namespace,
                 initializers=None):
        if initializers is None:
            initializers = {}
        _GenericDeclaration.__init__(self, start, end, name, namespace)
        converter = TypeConverter(namespace)
        self.return_type = converter.create_return_type(return_type)
        self.parameters = converter.to_parameters(parameters)
        self.specializations = converter.to_type(specializations)
        self.modifiers = modifiers
        self.body = body
        self.templated_types = templated_types
        self.initializers = initializers

    def is_declaration(self):
        return self.body is None

    def is_definition(self):
        return self.body is not None

    def is_exportable(self):
        if self.return_type:
            if (
                'static' in self.return_type.modifiers or
                'constexpr' in self.return_type.modifiers
            ):
                return False
        return None not in self.namespace

    def __str__(self):
        # TODO(nnorwitz): add templated_types.
        suffix = ('%s %s(%s), 0x%02x, %s' %
                  (self.return_type, self.name, self.parameters,
                   self.modifiers, self.body))
        return self._type_string_helper(suffix)


class Method(Function):

    def __init__(self, start, end, name, in_class, return_type, parameters,
                 specializations, modifiers, templated_types, body, namespace):
        # TODO(christarazi):
        # Add support for ctor initializers.
        # For now, only inline defined ctors are supported because we would
        # need to figure out how to keep state of which class is currently
        # being processed in order to modify its body (var decls).
        #
        # Note: ctor initializers are inside Function because a inline defined
        # class members are parsed as functions rather than methods.
        Function.__init__(self, start, end, name, return_type, parameters,
                          specializations, modifiers, templated_types,
                          body, namespace)
        # TODO(nnorwitz): in_class could also be a namespace which can
        # mess up finding functions properly.
        self.in_class = in_class


class Type(_GenericDeclaration):

    """Type used for any variable (eg class, primitive, struct, etc)."""

    def __init__(self, start, end, name, templated_types, modifiers,
                 reference, pointer, array):
        """Args:

        name: str name of main type
        templated_types: [Class (Type?)] template type info between <>
        modifiers: [str] type modifiers (keywords) eg, const, mutable, etc.
        reference, pointer, array: bools
        """
        _GenericDeclaration.__init__(self, start, end, name, [])
        self.templated_types = templated_types
        if not name and modifiers:
            self.name = modifiers.pop()
        self.modifiers = modifiers
        self.reference = reference
        self.pointer = pointer
        self.array = array

    def __str__(self):
        prefix = ''
        if self.modifiers:
            prefix = ' '.join(self.modifiers) + ' '
        name = unicode(self.name)
        if self.templated_types:
            name += '<%s>' % self.templated_types
        suffix = prefix + name
        if self.reference:
            suffix += '&'
        if self.pointer:
            suffix += '*'
        if self.array:
            suffix += '[]'
        return self._type_string_helper(suffix)

    # By definition, Is* are always False. A Type can only exist in
    # some sort of variable declaration, parameter, or return value.
    def is_declaration(self):
        return False

    def is_definition(self):
        return False

    def is_exportable(self):
        return False


class TypeConverter(object):

    def __init__(self, namespace_stack):
        self.namespace_stack = namespace_stack

    def _get_template_end(self, tokens, start):
        count = 1
        end = start
        while count and end < len(tokens):
            token = tokens[end]
            end += 1
            if token.name == '<':
                count += 1
            elif token.name == '>':
                count -= 1
        return tokens[start:end - 1], end

    def to_type(self, tokens):
        """Convert [Token,...] to [Class(...), ] useful for base classes.

        For example, code like class Foo : public Bar<x, y> { ... };
        the "Bar<x, y>" portion gets converted to an AST.

        Returns:
          [Class(...), ...]
        """
        result = []
        name_tokens = []
        reference = pointer = array = False
        inside_array = False
        empty_array = True
        templated_tokens = []

        def add_type():
            if not name_tokens:
                return

            # Partition tokens into name and modifier tokens.
            names = []
            modifiers = []
            for t in name_tokens:
                if keywords.is_keyword(t.name):
                    modifiers.append(t.name)
                else:
                    names.append(t.name)
            name = ''.join(names)

            templated_types = self.to_type(templated_tokens)
            result.append(Type(name_tokens[0].start, name_tokens[-1].end,
                               name, templated_types, modifiers,
                               reference, pointer, array))
            del name_tokens[:]
            del templated_tokens[:]

        i = 0
        end = len(tokens)
        while i < end:
            token = tokens[i]
            if token.name == ']':
                inside_array = False
                if empty_array:
                    pointer = True
                else:
                    array = True
            elif inside_array:
                empty_array = False
            elif token.name == '<':
                templated_tokens, i = self._get_template_end(tokens, i + 1)
                continue
            elif token.name == ',' or token.name == '(':
                add_type()
                reference = pointer = array = False
                empty_array = True
            elif token.name == '*':
                pointer = True
            elif token.name == '&':
                reference = True
            elif token.name == '[':
                inside_array = True
            elif token.name != ')':
                name_tokens.append(token)
            i += 1

        add_type()
        return result

    def declaration_to_parts(self, parts, needs_name_removed):
        arrayBegin = 0
        arrayEnd = 0
        default = []
        other_tokens = []

        # Handle default (initial) values properly.
        for i, t in enumerate(parts):
            if t.name == '[' and arrayBegin == 0:
                arrayBegin = i
                other_tokens.append(t)
            elif t.name == ']':
                arrayEnd = i
                other_tokens.append(t)
            elif t.name == '=':
                default = parts[i + 1:]
                parts = parts[:i]
                break

        if arrayBegin < arrayEnd:
            parts = parts[:arrayBegin] + parts[arrayEnd + 1:]

        modifiers = []
        type_name = ['']
        last_type = tokenize.SYNTAX
        templated_types = []
        i = 0
        end = len(parts)
        while i < end:
            p = parts[i]
            if keywords.is_builtin_modifiers(p.name):
                modifiers.append(p.name)
            elif p.name == '<':
                templated_tokens, new_end = self._get_template_end(
                    parts, i + 1)
                templated_types = self.to_type(templated_tokens)
                i = new_end - 1
            elif p.name not in ('*', '&'):
                if (
                    last_type == tokenize.NAME and
                    p.token_type == tokenize.NAME
                ):
                    type_name.append('')
                type_name[-1] += p.name
                last_type = p.token_type
            else:
                other_tokens.append(p)
            i += 1

        name = None
        if len(type_name) == 1 or keywords.is_builtin_type(type_name[-1]):
            needs_name_removed = False
        if needs_name_removed:
            name = type_name.pop()

        return (name,
                ' '.join([t for t in type_name]),
                templated_types,
                modifiers,
                default,
                other_tokens)

    def to_parameters(self, tokens):
        if not tokens:
            return []

        result = []
        type_modifiers = []
        pointer = reference = False
        first_token = None
        default = []

        def add_parameter():
            if not type_modifiers:
                return
            if default:
                del default[0]  # Remove flag.
            end = type_modifiers[-1].end

            (name, type_name, templated_types, modifiers,
             _, __) = self.declaration_to_parts(type_modifiers,
                                                True)

            if type_name:
                parameter_type = Type(first_token.start, first_token.end,
                                      type_name, templated_types, modifiers,
                                      reference, pointer, False)
                p = Parameter(first_token.start, end, name,
                              parameter_type, default)
                result.append(p)

        template_count = 0
        for s in tokens:
            if not first_token:
                first_token = s
            if s.name == '<':
                template_count += 1
            elif s.name == '>':
                template_count -= 1
            if template_count > 0:
                if default:
                    default.append(s)
                else:
                    type_modifiers.append(s)
                continue

            if s.name == ',':
                add_parameter()
                type_modifiers = []
                pointer = reference = False
                first_token = None
                default = []
            elif default:
                default.append(s)
            elif s.name == '*':
                pointer = True
            elif s.name == '&':
                reference = True
            elif s.name == '[':
                pointer = True
            elif s.name == ']':
                pass  # Just don't add to type_modifiers.
            elif s.name == '=':
                # Got a default value. Add any value (None) as a flag.
                default.append(None)
            else:
                type_modifiers.append(s)
        add_parameter()
        return result

    def create_return_type(self, return_type_seq):
        if not return_type_seq:
            return None
        start = return_type_seq[0].start
        end = return_type_seq[-1].end

        _, name, templated_types, modifiers, __, other_tokens = (
            self.declaration_to_parts(return_type_seq, False))

        names = [n.name for n in other_tokens]
        reference = '&' in names
        pointer = '*' in names
        array = '[' in names
        return Type(start, end, name, templated_types, modifiers,
                    reference, pointer, array)

    def get_template_indices(self, names):
        # names is a list of strings.
        start = names.index('<')
        end = len(names) - 1
        while end > 0:
            if names[end] == '>':
                break
            end -= 1
        return start, end + 1


class ASTBuilder(object):

    def __init__(self, token_stream, filename, system_includes=tuple(),
                 nonsystem_includes=tuple(), in_class=None,
                 namespace_stack=None, quiet=False):
        if namespace_stack is None:
            namespace_stack = []

        self.system_includes = system_includes
        self.nonsystem_includes = nonsystem_includes
        self.tokens = token_stream
        self.filename = filename
        self.token_queue = []
        self.namespace_stack = namespace_stack[:]
        self.namespaces = []
        self.define = set()
        self.quiet = quiet
        self.in_class = in_class
        if in_class:
            self.namespaces.append(False)
        # Keep the state whether we are currently handling a typedef or not.
        self._handling_typedef = False
        self._handling_const = False
        self.converter = TypeConverter(self.namespace_stack)

    def generate(self):
        while True:
            try:
                token = self._get_next_token()
            except StopIteration:
                break

            if token.name == '{':
                self.namespaces.append(False)
                continue
            if token.name == '}':
                if self.namespaces and self.namespaces.pop():
                    self.namespace_stack.pop()
                continue

            try:
                result = self._generate_one(token)
            except StopIteration:
                pass
            else:
                if result:
                    yield result

    def _create_variable(self, pos_token, name, type_name, type_modifiers,
                         ref_pointer_name_seq, templated_types=None, value=''):
        if templated_types is None:
            templated_types = []

        reference = '&' in ref_pointer_name_seq
        pointer = '*' in ref_pointer_name_seq
        array = '[' in ref_pointer_name_seq
        var_type = Type(pos_token.start, pos_token.end, type_name,
                        templated_types, type_modifiers,
                        reference, pointer, array)
        return VariableDeclaration(pos_token.start, pos_token.end,
                                   name, var_type, value, self.namespace_stack)

    def _generate_one(self, token):
        if token.token_type == tokenize.NAME:
            if (keywords.is_keyword(token.name) and
                    not keywords.is_builtin_type(token.name)):
                method = getattr(self, 'handle_' + token.name, None)
                assert_parse(method, 'unexpected token: {}'.format(token))
                return method()

            # Handle data or function declaration/definition.
            temp_tokens, last_token = \
                self._get_var_tokens_up_to(True, '(', ';', '{')

            temp_tokens.insert(0, token)
            if last_token.name == '(' or last_token.name == '{':
                # Ignore static_assert
                if temp_tokens[-1].name == 'static_assert':
                    self._ignore_up_to(';')
                    return None

                # Ignore __declspec
                if temp_tokens[-1].name == '__declspec':
                    list(self._get_parameters())
                    return None

                # Ignore __attribute__
                if temp_tokens[-1].name == '__attribute__':
                    list(self._get_parameters())
                    new_temp, last_token = \
                        self._get_var_tokens_up_to(True, '(', ';', '{')
                    del temp_tokens[-1]
                    temp_tokens.extend(new_temp)

                # If there is an assignment before the paren,
                # this is an expression, not a method.
                for i, elt in reversed(list(enumerate(temp_tokens))):
                    if (
                        elt.name == '=' and
                        temp_tokens[i - 1].name != 'operator'
                    ):
                        temp_tokens.append(last_token)
                        new_temp, last_token = \
                            self._get_var_tokens_up_to(False, ';')
                        temp_tokens.extend(new_temp)
                        break

            if last_token.name == ';':
                return self._get_variable(temp_tokens)
            if last_token.name == '{':
                assert_parse(temp_tokens, 'not enough tokens')

                self._add_back_token(last_token)
                self._add_back_tokens(temp_tokens[1:])
                method_name = temp_tokens[0].name
                method = getattr(self, 'handle_' + method_name, None)
                if not method:
                    return None
                return method()
            return self._get_method(temp_tokens, 0, None, False)
        elif token.token_type == tokenize.SYNTAX:
            if token.name == '~' and self.in_class:
                # Must be a dtor (probably not in method body).
                token = self._get_next_token()
                return self._get_method([token], FUNCTION_DTOR, None, True)
            # TODO(nnorwitz): handle a lot more syntax.
        elif token.token_type == tokenize.PREPROCESSOR:
            # TODO(nnorwitz): handle more preprocessor directives.
            # token starts with a #, so remove it and strip whitespace.
            name = token.name[1:].lstrip()
            if name.startswith('include'):
                # Remove "include".
                name = name[7:].strip()
                assert name
                # Handle #include \<newline> "header-on-second-line.h".
                if name.startswith('\\'):
                    name = name[1:].strip()

                filename = name.strip('<>"')

                def _is_file(prefix):
                    return os.path.isfile(os.path.join(prefix, filename))

                if any([d for d in self.system_includes if _is_file(d)]):
                    system = True
                elif any([d for d in self.nonsystem_includes if _is_file(d)]):
                    system = False
                else:
                    system = True
                    filename = name

                    if name[0] in '<"':
                        assert_parse(name[-1] in '>"', token)
                        system = name[0] == '<'
                        filename = name[1:-1]

                return Include(token.start, token.end, filename, system)
            if name.startswith('define'):
                # Remove "define".
                name = name[6:].strip()
                assert name
                # Handle #define \<newline> MACRO.
                if name.startswith('\\'):
                    name = name[1:].strip()
                value = ''
                paren = 0

                for i, c in enumerate(name):
                    if not paren and c.isspace():
                        value = name[i:].lstrip()
                        name = name[:i]
                        break
                    if c == ')':
                        value = name[i + 1:].lstrip()
                        name = name[:paren]
                        self.define.add(name)
                        break
                    if c == '(':
                        paren = i
                if value.startswith('\\'):
                    value = value[1:].strip()
                return Define(token.start, token.end, name, value)
            if name.startswith('undef'):
                # Remove "undef".
                name = name[5:].strip()
                assert name
                self.define.discard(name)
        return None

    def _get_tokens_up_to(self, expected_token):
        return self._get_var_tokens_up_to(False,
                                          expected_token)[0]

    def _get_var_tokens_up_to_w_function(self, skip_bracket_content,
                                         *expected_tokens):
        # handle the std::function and boost::function case
        tokens, last = self._get_var_tokens_up_to(False, *expected_tokens)
        names = [token.name for token in tokens]
        ctr = collections.Counter(names)
        if ('(' in expected_tokens and
            ctr['<'] != ctr['>'] and
            ctr['function'] == 1 and
                last.name == '('):

            idx = names.index('function')
            if idx + 1 < len(tokens) and tokens[idx + 1].name == '<':
                new_tokens, new_last = \
                    self._get_var_tokens_up_to(False, '(', ';')
                tokens.append(last)
                last = new_last
                tokens += new_tokens
        return tokens, last

    def _get_var_tokens_up_to(self, skip_bracket_content, *expected_tokens):
        last_token = self._get_next_token()
        tokens = []
        count1 = 0
        count2 = 0
        while (count1 != 0 or
               count2 != 0 or
               last_token.token_type != tokenize.SYNTAX or
               last_token.name not in expected_tokens):
            if last_token.name == '[':
                count1 += 1
            elif last_token.name == ']':
                count1 -= 1
            if skip_bracket_content and count1 == 0:
                if last_token.name == 'operator':
                    skip_bracket_content = False
                elif last_token.name == '<':
                    count2 += 1
                elif last_token.name == '>':
                    count2 -= 1
            if last_token.token_type != tokenize.PREPROCESSOR:
                tokens.append(last_token)
            temp_token = self._get_next_token()
            if temp_token.name == '(' and last_token.name in self.define:
                # TODO: for now just ignore the tokens inside the parenthesis
                list(self._get_parameters())
                temp_token = self._get_next_token()
            last_token = temp_token
        return tokens, last_token

    def _ignore_up_to(self, token):
        self._get_tokens_up_to(token)

    def _get_matching_char(self, open_paren, close_paren, get_next_token=None):
        if get_next_token is None:
            get_next_token = self._get_next_token
        # Assumes the current token is open_paren and we will consume
        # and return up to the close_paren.
        count = 1
        while count != 0:
            token = get_next_token()
            if token.token_type == tokenize.SYNTAX:
                if token.name == open_paren:
                    count += 1
                elif token.name == close_paren:
                    count -= 1
            yield token

    def _get_parameters(self):
        return self._get_matching_char('(', ')')

    def get_scope(self):
        return self._get_matching_char('{', '}')

    def _get_next_token(self):
        if self.token_queue:
            return self.token_queue.pop()
        return next(self.tokens)

    def _add_back_token(self, token):
        self.token_queue.append(token)

    def _add_back_tokens(self, tokens):
        if tokens:
            self.token_queue.extend(reversed(tokens))

    def get_name(self, seq=None):
        """Returns ([tokens], next_token_info)."""
        if seq is not None:
            it = iter(seq)

            def get_next_token():
                return next(it)
        else:
            get_next_token = self._get_next_token

        next_token = get_next_token()
        tokens = []
        last_token_was_name = False
        while (next_token.token_type == tokenize.NAME or
               (next_token.token_type == tokenize.SYNTAX and
                next_token.name in ('::', '<'))):
            # Two NAMEs in a row means the identifier should terminate.
            # It's probably some sort of variable declaration.
            if last_token_was_name and next_token.token_type == tokenize.NAME:
                break
            last_token_was_name = next_token.token_type == tokenize.NAME
            tokens.append(next_token)
            # Handle templated names.
            if next_token.name == '<':
                tokens.extend(self._get_matching_char('<', '>',
                                                      get_next_token))
                last_token_was_name = True
            next_token = get_next_token()
        return tokens, next_token

    def get_method(self, modifiers, templated_types):
        return_type_and_name = \
            self._get_var_tokens_up_to_w_function(False, '(')[0]
        assert len(return_type_and_name) >= 1
        return self._get_method(
            return_type_and_name, modifiers, templated_types,
            False)

    def _get_method(self, return_type_and_name, modifiers, templated_types,
                    get_paren):
        specializations = []
        if get_paren:
            token = self._get_next_token()
            assert_parse(token.token_type == tokenize.SYNTAX, token)
            if token.name == '<':
                # Handle templatized dtors.
                specializations = list(self._get_matching_char('<', '>'))
                del specializations[-1]
                token = self._get_next_token()
            assert_parse(token.token_type == tokenize.SYNTAX, token)
            assert_parse(token.name == '(', token)

        name = return_type_and_name.pop()
        if (len(return_type_and_name) > 2 and
                return_type_and_name[-1].name == '>' and
                return_type_and_name[-2].name == 'operator' and
                (name.name == '>=' or name.name == '>')):
            n = return_type_and_name.pop()
            name = tokenize.Token(tokenize.SYNTAX,
                                  n.name + name.name,
                                  n.start, name.end)

        if (len(return_type_and_name) > 1 and
            (return_type_and_name[-1].name == 'operator' or
             return_type_and_name[-1].name == '~')):
            op = return_type_and_name.pop()
            name = tokenize.Token(tokenize.NAME, op.name + name.name,
                                  op.start, name.end)
        # Handle templatized ctors.
        elif name.name == '>':
            count = 1
            index = len(return_type_and_name)
            while count and index > 0:
                index -= 1
                tok = return_type_and_name[index]
                if tok.name == '<':
                    count -= 1
                elif tok.name == '>':
                    count += 1
            specializations = return_type_and_name[index + 1:]
            del return_type_and_name[index:]
            name = return_type_and_name.pop()
        elif name.name == ']':
            name_seq = return_type_and_name[-2]
            del return_type_and_name[-2:]
            name = tokenize.Token(tokenize.NAME, name_seq.name + '[]',
                                  name_seq.start, name.end)

        return_type = return_type_and_name
        indices = name
        if return_type:
            indices = return_type[0]

        # Force ctor for templatized ctors.
        if name.name == self.in_class and not modifiers:
            modifiers |= FUNCTION_CTOR
        parameters = list(self._get_parameters())
        assert_parse(parameters, 'missing closing parenthesis')
        last_token = parameters.pop()    # Remove trailing ')'.

        # Handling operator() is especially weird.
        if name.name == 'operator' and not parameters:
            token = self._get_next_token()
            assert_parse(token.name == '(', token)
            name = tokenize.Token(tokenize.NAME, 'operator()',
                                  name.start, last_token.end)
            parameters = list(self._get_parameters())
            del parameters[-1]          # Remove trailing ')'.

        try:
            token = self._get_next_token()
        except StopIteration:
            token = tokenize.Token(tokenize.SYNTAX, ';', 0, 0)

        while (
            token.token_type == tokenize.NAME or
            token.token_type == tokenize.PREPROCESSOR
        ):
            if (
                token.name == 'const' or
                token.name == 'override' or
                token.name == 'final'
            ):
                modifiers |= FUNCTION_SPECIFIER
                token = self._get_next_token()
            elif token.name == 'noexcept':
                modifiers |= FUNCTION_SPECIFIER
                token = self._get_next_token()
                if token.name == '(':
                    # Consume everything between the parens.
                    list(self._get_matching_char('(', ')'))
                    token = self._get_next_token()
            elif token.name == '__attribute__':
                # TODO(nnorwitz): handle more __attribute__ details.
                modifiers |= FUNCTION_ATTRIBUTE
                token = self._get_next_token()
                assert_parse(token.name == '(', token)
                # Consume everything between the parens.
                list(self._get_matching_char('(', ')'))
                token = self._get_next_token()
            elif token.name == 'throw':
                modifiers |= FUNCTION_THROW
                token = self._get_next_token()
                assert_parse(token.name == '(', token)
                # Consume everything between the parens.
                list(self._get_matching_char('(', ')'))
                token = self._get_next_token()
            elif token.name == token.name.upper():
                # Assume that all upper-case names are some macro.
                modifiers |= FUNCTION_UNKNOWN_ANNOTATION
                token = self._get_next_token()
                if token.name == '(':
                    # Consume everything between the parens.
                    list(self._get_matching_char('(', ')'))
                    token = self._get_next_token()
            elif token.token_type == tokenize.PREPROCESSOR:
                token = self._get_next_token()
            else:
                self._add_back_token(token)
                token = tokenize.Token(tokenize.SYNTAX, ';', 0, 0)

        # Handle ref-qualifiers.
        if token.name == '&' or token.name == '&&':
            token = self._get_next_token()

        # Handle trailing return types.
        if token.name == '->':
            return_type, token = self._get_var_tokens_up_to(False, '{', ';')

        if token.name == '}' or token.token_type == tokenize.PREPROCESSOR:
            self._add_back_token(token)
            token = tokenize.Token(tokenize.SYNTAX, ';', 0, 0)

        assert_parse(token.token_type == tokenize.SYNTAX, token)

        # Handle ctor initializers.
        # Supports C++11 method of direct initialization with braces.
        initializers = {}
        if token.name == ':':
            while token.name != ';' and token.name != '{':
                member, token = self.get_name()
                member = member[0]
                if token.name == '(' or token.name == '{':
                    end = '}' if token.name == '{' else ')'
                    initializers[member] = [
                        x for x in list(self._get_matching_char(token.name,
                                                                end))
                        if x.name != ',' and x.name != end]
                token = self._get_next_token()

        # Handle pointer to functions.
        if token.name == '(':
            # name contains the return type.
            return_type.append(name)
            while parameters[-1].name in '()':
                parameters.pop()
            name = parameters[-1]
            # Already at the ( to open the parameter list.
            parameters = list(self._get_matching_char('(', ')'))
            del parameters[-1]  # Remove trailing ')'.
            # TODO(nnorwitz): store the function_parameters.
            token = self._get_next_token()

            if token.name != '{':
                default = []
                if token.name == '=':
                    default.extend(self._get_tokens_up_to(';'))

                return self._create_variable(
                    indices,
                    name.name,
                    indices.name,
                    [],
                    [t.name for t in return_type],
                    None,
                    ''.join([t.name for t in default]))

        if token.name == '{':
            body = list(self.get_scope())
            del body[-1]                # Remove trailing '}'.
        else:
            body = None
            if token.name == '=':
                token = self._get_next_token()
                if token.name == '0':
                    modifiers |= FUNCTION_PURE_VIRTUAL
                token = self._get_next_token()

            if token.name == '[':
                # TODO(nnorwitz): store tokens and improve parsing.
                # template <typename T, size_t N> char (&ASH(T (&seq)[N]))[N];
                list(self._get_matching_char('[', ']'))
                token = self._get_next_token()

            if token.name in '*&':
                tokens, last = self._get_var_tokens_up_to(False, '(', ';')
                tokens.insert(0, token)
                tokens = parameters + tokens
                if last.name == '(':
                    return self._get_method(tokens, 0, None, False)
                return self._get_variable(tokens)

            assert_parse(token.name == ';',
                         (token, return_type_and_name, parameters))

        # Looks like we got a method, not a function.
        if len(return_type) > 1 and return_type[-1].name == '::':
            return_type, in_class = \
                self._get_return_type_and_class_name(return_type)
            return Method(indices.start, indices.end, name.name, in_class,
                          return_type, parameters, specializations, modifiers,
                          templated_types, body, self.namespace_stack)
        return Function(indices.start, indices.end, name.name, return_type,
                        parameters, specializations, modifiers,
                        templated_types, body, self.namespace_stack,
                        initializers)

    def _get_variable(self, tokens):
        name, type_name, templated_types, modifiers, default, _ = \
            self.converter.declaration_to_parts(tokens, True)

        assert_parse(tokens, 'not enough tokens')

        t0 = tokens[0]
        names = [t.name for t in tokens]
        if templated_types:
            start, end = self.converter.get_template_indices(names)
            names = names[:start] + names[end:]
        default = ''.join([t.name for t in default])
        return self._create_variable(t0, name, type_name, modifiers,
                                     names, templated_types, default)

    def _get_return_type_and_class_name(self, token_seq):
        # Splitting the return type from the class name in a method
        # can be tricky. For example, Return::Type::Is::Hard::To::Find().
        # Where is the return type and where is the class name?
        # The heuristic used is to pull the last name as the class name.
        # This includes all the templated type info.
        # TODO(nnorwitz): if there is only One name like in the
        # example above, punt and assume the last bit is the class name.

        i = 0
        end = len(token_seq) - 1

        # Make a copy of the sequence so we can append a sentinel
        # value. This is required for get_name will has to have some
        # terminating condition beyond the last name.
        seq_copy = token_seq[i:end]
        seq_copy.append(tokenize.Token(tokenize.SYNTAX, '', 0, 0))
        names = []
        while i < end:
            # Iterate through the sequence parsing out each name.
            new_name, next_item = self.get_name(seq_copy[i:])
            # We got a pointer or ref. Add it to the name.
            if next_item and next_item.token_type == tokenize.SYNTAX:
                new_name.append(next_item)
            names.append(new_name)
            i += len(new_name)

        # Remove the sentinel value.
        names[-1].pop()
        # Flatten the token sequence for the return type.
        return_type = [e for seq in names[:-1] for e in seq]
        # The class name is the last name.
        class_name = names[-1]
        return return_type, class_name

    def _handle_class_and_struct(self, class_type):
        if self._handling_typedef:
            return self._get_class(class_type, None)

        name_tokens, var_token = self.get_name()
        if var_token.token_type == tokenize.NAME or var_token.name in '*&':
            tokens, last = self._get_var_tokens_up_to(False, '(', ';', '{')
            tokens.insert(0, var_token)
            tokens = name_tokens + tokens
            if last.name == '{':
                self._add_back_token(last)
                self._add_back_tokens(tokens)
                return self._get_class(class_type, None)
            if last.name == '(':
                return self._get_method(tokens, 0, None, False)
            return self._get_variable(tokens)

        self._add_back_token(var_token)
        self._add_back_tokens(name_tokens)
        return self._get_class(class_type, None)

    def handle_class(self):
        return self._handle_class_and_struct(Class)

    def handle_struct(self):
        return self._handle_class_and_struct(Struct)

    def handle_union(self):
        return self._handle_class_and_struct(Union)

    def handle_enum(self):
        # Handle strongly typed enumerations.
        token = self._get_next_token()
        if token.name != 'class':
            self._add_back_token(token)

        name = None
        name_tokens, token = self.get_name()
        if name_tokens:
            name = ''.join([t.name for t in name_tokens])

        if token.token_type == tokenize.NAME:
            if self._handling_typedef:
                self._add_back_token(token)
                return Enum(token.start, token.end, name, None,
                            self.namespace_stack)

            next_token = self._get_next_token()
            if next_token.name != '(':
                self._add_back_token(next_token)
            else:
                name_tokens.append(token)
                return self._get_method(name_tokens, 0, None, False)

        # Handle underlying type.
        if token.token_type == tokenize.SYNTAX and token.name == ':':
            _, token = self._get_var_tokens_up_to(False, '{', ';')

        # Handle forward declarations.
        if token.token_type == tokenize.SYNTAX and token.name == ';':
            return Enum(token.start, token.end, name, None,
                        self.namespace_stack)

        # Must be the type declaration.
        if token.token_type == tokenize.SYNTAX and token.name == '{':
            fields = list(self._get_matching_char('{', '}'))
            del fields[-1]                  # Remove trailing '}'.
            next_item = self._get_next_token()
            new_type = Enum(token.start, token.end, name, fields,
                            self.namespace_stack)
            # A name means this is an anonymous type and the name
            # is the variable declaration.
            if next_item.token_type != tokenize.NAME:
                return new_type
            name = new_type
            token = next_item

        # Must be variable declaration using the type prefixed with keyword.
        assert_parse(token.token_type == tokenize.NAME, token)
        return self._create_variable(token, token.name, name, [], '')

    def handle_const(self):
        self._handling_const = True
        token = self._get_next_token()
        result = self._generate_one(token)
        self._handling_const = False
        return result

    def handle_inline(self):
        pass

    def handle_extern(self):
        pass

    def handle_virtual(self):
        # What follows must be a method.
        token = self._get_next_token()
        if token.name == 'inline':
            token = self._get_next_token()
        if token.token_type == tokenize.SYNTAX and token.name == '~':
            return self.get_method(FUNCTION_VIRTUAL + FUNCTION_DTOR, None)
        return_type_and_name = self._get_tokens_up_to('(')
        return_type_and_name.insert(0, token)
        return self._get_method(return_type_and_name, FUNCTION_VIRTUAL,
                                None, False)

    def handle_public(self):
        assert_parse(self.in_class, 'expected to be in a class')

    def handle_protected(self):
        assert_parse(self.in_class, 'expected to be in a class')

    def handle_private(self):
        assert_parse(self.in_class, 'expected to be in a class')

    def handle_friend(self):
        tokens, last = self._get_var_tokens_up_to(False, '(', ';')
        if last.name == '(':
            tokens.append(last)
            self._add_back_tokens(tokens)
            token = self._get_next_token()
            while token.name in ('inline', 'typename', '::'):
                token = self._get_next_token()
            result = self._generate_one(token)
        else:
            if tokens[0].name == 'class':
                tokens = tokens[1:]
            result = self.converter.to_type(tokens)[0]

        assert result
        return Friend(result.start, result.end, result, self.namespace_stack)

    def handle_typedef(self):
        token = self._get_next_token()
        if (token.token_type == tokenize.NAME and
                keywords.is_builtin_other_modifiers(token.name)):
            method = getattr(self, 'handle_' + token.name)
            self._handling_typedef = True
            tokens = [method()]
            self._handling_typedef = False
        else:
            tokens = [token]

        # Get the remainder of the typedef up to the semi-colon.
        tokens.extend(self._get_tokens_up_to(';'))

        name = tokens.pop()
        if name.name == ')':
            tokens.append(name)
            end = len(tokens) - 2
            count = 1
            while count:
                if tokens[end].name == '(':
                    count -= 1
                elif tokens[end].name == ')':
                    count += 1
                end -= 1
            start = end
            if tokens[start].name == ')':
                name = tokens[start - 1]
                while tokens[start].name != '(':
                    start -= 1
            else:
                name = tokens[start]
            del tokens[start:end + 1]
        elif name.name == ']' and len(tokens) >= 2:
            tokens.append(name)
            name = tokens[1]
            del tokens[1]
        new_type = tokens
        if tokens and isinstance(tokens[0], tokenize.Token):
            new_type = self.converter.to_type(tokens)
        return Typedef(name.start, name.end, name.name,
                       new_type, self.namespace_stack)

    def handle_typename(self):
        pass  # Not needed yet.

    def _get_templated_types(self):
        result = {}
        tokens = list(self._get_matching_char('<', '>'))
        len_tokens = len(tokens) - 1    # Ignore trailing '>'.
        i = 0
        while i < len_tokens:
            key = tokens[i].name
            i += 1
            if keywords.is_keyword(key) or key == ',' or key == '.':
                continue
            type_name = default = None
            if i < len_tokens:
                i += 1
                if tokens[i - 1].name == '=':
                    assert_parse(i < len_tokens, '%s %s' % (i, tokens))
                    default, _ = self.get_name(tokens[i:])
                    i += len(default)
                elif tokens[i - 1].name != ',':
                    # We got something like: Type variable.
                    # Re-adjust the key (variable) and type_name (Type).
                    key = tokens[i - 1].name
                    type_name = tokens[i - 2]

            result[key] = (type_name, default)
        return result

    def handle_template(self):
        token = self._get_next_token()

        templated_types = None
        if token.token_type == tokenize.SYNTAX and token.name == '<':
            templated_types = self._get_templated_types()
            token = self._get_next_token()
        while token.token_type == tokenize.PREPROCESSOR:
            token = self._get_next_token()

        if token.token_type == tokenize.NAME:
            if token.name == 'class':
                return self._get_class(Class,
                                       templated_types)
            elif token.name == 'struct':
                return self._get_class(Struct,
                                       templated_types)
            elif token.name == 'union':
                return self._get_class(Union,
                                       templated_types)
            elif token.name == 'friend':
                return self.handle_friend()
            elif token.name == 'template':
                return self.handle_template()
        self._add_back_token(token)
        tokens, last = self._get_var_tokens_up_to_w_function(False, '(', ';')
        tokens.append(last)
        self._add_back_tokens(tokens)
        if last.name == '(':
            return self.get_method(FUNCTION_NONE, templated_types)
        # Must be a variable definition.
        return None

    def _get_bases(self):
        # Get base classes.
        bases = []
        specifier = ('public', 'protected', 'private', 'virtual')
        while True:
            token = self._get_next_token()
            if (
                token.name in specifier or
                token.token_type == tokenize.PREPROCESSOR
            ):
                continue
            self._add_back_token(token)

            base, next_token = self.get_name()
            if (
                len(base) > 2 and
                base[-2].name == '::' and
                next_token.token_type == tokenize.NAME and
                next_token.name not in specifier
            ):
                self._add_back_token(next_token)
                base2, next_token = self.get_name()
                base.pop()
                base.extend(base2)
            bases_ast = self.converter.to_type(base)
            if len(bases_ast) == 1:
                bases.append(bases_ast[0])
            if next_token.name == ')':
                next_token = self._get_next_token()
            while next_token.token_type == tokenize.PREPROCESSOR:
                next_token = self._get_next_token()
            if next_token.name == '{':
                token = next_token
                break
        return bases, token

    def _get_class(self, class_type, templated_types):
        class_name = None
        class_token = self._get_next_token()
        name_tokens = []
        if class_token.token_type != tokenize.NAME:
            assert_parse(class_token.token_type == tokenize.SYNTAX,
                         class_token)
            token = class_token
        else:
            self._add_back_token(class_token)
            name_tokens, token = self.get_name()

            if self._handling_typedef:
                # Handle typedef to pointer.
                if token.name in '*&':
                    name_tokens.append(token)
                    token = self._get_next_token()
            # Handle attribute.
            elif token.token_type == tokenize.NAME:
                self._add_back_token(token)
                attribute, token = self.get_name()
                if len(attribute) > 1 or attribute[0].name != 'final':
                    name_tokens = attribute
            class_name = self.converter.to_type(name_tokens)[0].name
            assert_parse(class_name, class_token)

        bases = None
        if token.token_type == tokenize.PREPROCESSOR:
            token = self._get_next_token()
        if token.token_type == tokenize.SYNTAX:
            if token.name == ';':
                # Forward declaration.
                return class_type(class_token.start, class_token.end,
                                  class_name, None, templated_types, None,
                                  self.namespace_stack)
            if token.name in '*&':
                # Inline forward declaration. Could be method or data.
                name_token = self._get_next_token()
                next_token = self._get_next_token()
                if next_token.name == ';':
                    # Handle data
                    modifiers = ['class']
                    return self._create_variable(class_token, name_token.name,
                                                 class_name,
                                                 modifiers, token.name)
                else:
                    # Assume this is a method.
                    tokens = (class_token, token, name_token, next_token)
                    self._add_back_tokens(tokens)
                    return self.get_method(FUNCTION_NONE, None)
            if token.name == ':':
                bases, token = self._get_bases()

        body = None
        if token.token_type == tokenize.SYNTAX and token.name == '{':
            name = class_name or '__unamed__'
            ast = ASTBuilder(self.get_scope(), self.filename,
                             self.system_includes, self.nonsystem_includes,
                             name,
                             self.namespace_stack,
                             quiet=self.quiet)
            body = list(ast.generate())

            ctor = None
            for member in body:
                if isinstance(member, Function) and member.name == class_name:
                    ctor = member
                    break

            # Merge ctor initializers with class members.
            if ctor:
                initializers = body[body.index(ctor)].initializers
                var_decls = [x for x in body
                             if isinstance(x, VariableDeclaration)]
                for var in var_decls:
                    for key, val in initializers.items():
                        # TODO: CT
                        # In the future, support members that have ctors with
                        # more than one parameter.
                        if len(val) > 1:
                            continue
                        if len(val) == 1 and var.name == key.name:
                            body[body.index(var)].initial_value = val[0].name

            if not self._handling_typedef:
                token = self._get_next_token()
                if token.token_type != tokenize.NAME:
                    assert_parse(token.token_type == tokenize.SYNTAX, token)
                    assert_parse(token.name == ';', token)
                else:
                    if keywords.is_builtin_type(token.name):
                        token = self._get_next_token()
                    self._ignore_up_to(';')
                    new_class = class_type(class_token.start, class_token.end,
                                           class_name, bases, None,
                                           body, self.namespace_stack)

                    modifiers = ['const'] if self._handling_const else []
                    return self._create_variable(class_token,
                                                 token.name, new_class,
                                                 modifiers, token.name)
        else:
            if not self._handling_typedef:
                name_tokens = [class_token] + name_tokens
                return self._get_method(name_tokens, 0, None, False)
            self._add_back_token(token)

        return class_type(class_token.start, class_token.end, class_name,
                          bases, templated_types, body, self.namespace_stack)

    def handle_namespace(self):
        token = self._get_next_token()
        # Support anonymous namespaces.
        name = None
        if token.token_type == tokenize.NAME:
            name = token.name
            token = self._get_next_token()
        assert_parse(token.token_type == tokenize.SYNTAX, token)

        if token.name == '=':
            # TODO(nnorwitz): handle aliasing namespaces.
            name, next_token = self.get_name()
            assert_parse(next_token.name == ';', next_token)
        else:
            assert_parse(token.name == '{', token)
            self.namespace_stack.append(name)
            self.namespaces.append(True)
        return None

    def handle_using(self):
        tokens = self._get_tokens_up_to(';')
        assert tokens
        new_type = self.converter.to_type(tokens)
        if 'namespace' in new_type[0].modifiers:
            return Using(tokens[0].start, tokens[0].end, tokens)
        else:
            # aside from namespaces, "using" can be used just like a typedef
            # e.g., the following lines are equivalent
            # using Foo = Bar;
            # typedef Bar Foo;
            # There is already code written to handle the typedef case so
            # we return a Typdef object
            return Typedef(tokens[0].start, tokens[0].end, new_type[0].name,
                           new_type, self.namespace_stack)

    def handle_explicit(self):
        assert self.in_class
        # Nothing much to do.
        # TODO(nnorwitz): maybe verify the method name == class name.
        # This must be a ctor.
        return self.get_method(FUNCTION_CTOR, None)

    def handle_operator(self):
        # Pull off the next token(s?) and make that part of the method name.
        pass


def builder_from_source(source, filename, system_includes,
                        nonsystem_includes, quiet=False):
    """Utility method that returns an ASTBuilder from source code.

    Args:
      source: 'C++ source code'
      filename: 'file1'

    Returns:
      ASTBuilder
    """
    return ASTBuilder(tokenize.get_tokens(source),
                      filename,
                      system_includes,
                      nonsystem_includes,
                      quiet=quiet)


def assert_parse(value, message):
    """Raise ParseError on token if value is False."""
    if not value:
        raise ParseError(message)
