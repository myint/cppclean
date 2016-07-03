template <
      std::size_t size_
    , std::size_t alignment_ = std::size_t(-1)
>
class aligned_storage : 
#ifndef __BORLANDC__
   private 
#else
   public
#endif
   ::boost::detail::aligned_storage::aligned_storage_imp<size_, alignment_> 
{
};
