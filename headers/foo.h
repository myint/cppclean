
#include <map>
#include <string>

#include "bar.h"
#include "xss_module.h"


typedef std::map<std::string, int> Mapper;
typedef struct { int zz; } AnonStruct;
typedef union NamedUnion { bool xx; } *NamedPtr;

class Baz;
class Unused;
class Local;
class DataMember;
class Ptr;

class Data;
extern Data* d;

namespace somespace {
class Jj;
}

namespace FooNS {

class Foo : public Bar {
 public:
  explicit Foo();
  Foo(register const unsigned long& a, Baz* output) {}
  virtual ~Foo() = 0;

 protected:
  virtual const somespace::Jj& Get() const;
  const somespace::Jj& Get2() const = 0;
  int Get3() const { return 0; }

  template <class T>
  T& foo(T* bar);

 private:
  void Method(const Mapper& mapper, somespace::Jj* j);
  Mapper& Blah();
  Mapper data_;
  DataMember* data;
  auto_ptr<Ptr*> ptr;
};

void Function(const Foo& foo, Bar* bar);
extern const ws::RMM *full;
void Function2(const Local& local);

}

class FooModule : public XSS::Module {
 public:
  FooModule() : XSS::Module("mod") { }
};

template<class> class ProtoArray;

class Experiment {
  explicit Experiment();

  struct Foo {
    bool operator() (const Foo *a, const Foo *b) {
      return true;
    }
  };

 private:
};


namespace noname {
enum nn {
  bar,
};
};

namespace {
// Anon namespace
};

#include "bar.h"  // foo
#include <string>  // foo

class Abc::Xyz {};

class Fool : public Bar, public Baz {};


namespace {
// Anon namespace with something
void lkjsdfkd();
};

class TT : public TTbase<Bar> {};

void (*ptof)(const TT& tt);

typedef void(*Setter)(int*, int);

// filling data.
Fool data[] = { NULL, };

class def_var {
  static const int kConstant1 = 5;
  static const int kConstant = (kConstant2 - 1) / 4;
};

#include "not-used.h"

namespace {
class LaunchNameEquals {
 public: 
  bool operator()(void* launch) {
    return true;
  } 
};
}  // namespace

enum {boo};

class Blashdfdf {
 public: 
  bool operator()(void* launch) const = 0;
};

const char kBS[] = "~!@#$%^&*()-+{}|`[]\\:\";'<>?,./ =\t\r\n\v\f\177";

class FooOnYou {
  void (sq_type::*field_)(string&);
};

namespace wtf = noname;
