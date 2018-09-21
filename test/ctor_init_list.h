class Foo {
public:
    int first,
#if defined(TEST)
    int second;
#endif
};

Foo::Foo():
    first(1)
    #if defined(TEST)   // this 3 lines
    ,second(2)          // generated
    #endif              // IndexError: list index out of range
{}
