class AssertingVH
#ifndef NDEBUG
  : public ValueHandleBase
#endif
{
};

template<typename T>
struct is_noncopyable
#if !defined(BOOST_BROKEN_IS_BASE_AND_DERIVED) && !defined(BOOST_NO_IS_ABSTRACT)
  : boost::mpl::or_<
        boost::is_abstract<T>
      , boost::is_base_and_derived<boost::noncopyable, T>
    >
#elif !defined(BOOST_BROKEN_IS_BASE_AND_DERIVED)
  : boost::is_base_and_derived<boost::noncopyable, T>
#elif !defined(BOOST_NO_IS_ABSTRACT)
  : boost::is_abstract<T>
#else
  : boost::mpl::false_
#endif
{
};
