#include "bar.h"
#include "me.h"
#include "myenum.h"

class Test
{
  Test(const Bar& bar);
  const Bar bar_;

  void f(MyEnum & bar);
};
