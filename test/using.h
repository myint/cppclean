// Forward declare Foo::Bar
namespace Foo
{
class Bar;
}

// So we can reference Bar without qualification below.
using namespace Foo;

class A
{
  // The namespaced forward declaration is required for this line of code.
  void f(Bar & bar);
};
