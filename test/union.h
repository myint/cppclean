template <typename T>
union SizerImpl {
  char arr1[sizeof(T)];
};

class Foo;

union U {
  Foo* foo;
};

template<class OffsetType>
union offset_ptr_internal
{
  offset_ptr_internal(OffsetType off)
  {}
};
