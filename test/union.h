template <typename T>
union SizerImpl {
  char arr1[sizeof(T)];
};

class Foo;

union U {
  Foo* foo;
};
