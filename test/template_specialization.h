class A;

template <>
template <>
A* Foo<0>::fn<1>();

class B;

template<>
void foo<B>();

class C;
class D;

template<>
void foo<C<D>>();
