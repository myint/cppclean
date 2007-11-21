
"""C++ keywords"""

TYPES = 'bool char int long short double float void wchar_t unsigned signed struct union enum'.split()
TYPE_MODIFIERS = 'auto register const inline extern static virtual volatile mutable'.split()
ACCESS = 'public protected private friend'.split()

CASTS = 'static_cast const_cast dynamic_cast reinterpret_cast'.split()

OTHERS = 'true false asm class namespace using explicit this operator sizeof'.split()
OTHER_TYPES = 'new delete typedef typeid typename template'.split()

CONTROL = 'case switch default if else return goto'.split()
EXCEPTION = 'try catch throw'.split()
LOOP = 'while do for break continue'.split()

ALL = set(TYPES + TYPE_MODIFIERS + ACCESS + CASTS + OTHERS + OTHER_TYPES + CONTROL + EXCEPTION + LOOP)


def IsKeyword(token):
    return token in ALL

def IsBuiltinType(token):
    if token in ('virtual', 'inline'):
        # These only apply to methods, they can't be types by themselves.
        return False
    return token in TYPES or token in TYPE_MODIFIERS
