template<class R> struct bind_t_generator
{
template<class F, class L> class implementation
{
};
};

template<class R2, class F, class L>
class bind_t: public bind_t_generator<R2>::template implementation<F, L>
{
};

template<class R2, class F, class L>
class bind_t: public bind_t_generator<R2>::BOOST_NESTED_TEMPLATE implementation<F, L>
{
};
