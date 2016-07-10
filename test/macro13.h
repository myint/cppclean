class bad_any_cast :
#ifndef BOOST_NO_RTTI
  public std::bad_cast
#else
  public std::exception
#endif
{
};
