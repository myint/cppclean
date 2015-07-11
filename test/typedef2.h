class Bar;
class Barr;
class Baz;

namespace A {
  class B;
  class C;
}

class Foo {
  friend class A::B;
  friend A::C;
  friend class Bar;
  friend Barr;
  friend void fn(Baz* baz);
};
