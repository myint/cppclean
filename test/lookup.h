class A;

namespace ns1
{
  typedef ::A a;
}


namespace ns1
{
  namespace ns2
  {
    template <typename T>
    class B;
  }
}

namespace ns1
{
  typedef ns2::B<int> b;
}


class C;

namespace ns3
{
  class C;
  
  void f1(::C& c);
  void f2(C& c);
}


namespace ns4
{
  namespace
  {
    namespace ns5
    {
      class D;
      void f(D& d);
    }
  }
}


class E;

namespace ns6
{
  class E
  {      
  };
}
