struct VariadicFunction {
  LLVM_DEFINE_OVERLOAD(1)
#undef LLVM_DEFINE_OVERLOAD
};

#define MY_THROW() throw ()
void Foo() MY_THROW() {}
