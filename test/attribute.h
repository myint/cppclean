static buffers_iterator begin(const BufferSequence& buffers)
#if defined(__GNUC__) && (__GNUC__ == 4) && (__GNUC_MINOR__ == 3)
  __attribute__ ((__noinline__))
#endif // defined(__GNUC__) && (__GNUC__ == 4) && (__GNUC_MINOR__ == 3)
{
}

class Args;

struct sum_kahan_impl
{
  void 
#if BOOST_ACCUMULATORS_GCC_VERSION > 40305
  __attribute__((__optimize__("no-associative-math")))
#endif
  operator ()(Args const & args)
  {
  }
};
