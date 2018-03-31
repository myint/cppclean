#include "const_define.h"

class A {
  public:
    A() :
      abc(CONST_DEFINE),
      efg(2),
      hij(3)
    {}
  private:
    int abc;
    int efg;
    int hij;
};

struct B {
  int arg1;

  B() :
    arg1(CONST_DEFINE)
  {}
};
