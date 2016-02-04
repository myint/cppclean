namespace undefined
{
  void function();
}

template <typename T>
inline void f(T value)
{
}

template <>
inline void f<int>(int value)
{
}
