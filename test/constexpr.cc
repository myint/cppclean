#include "constexpr.h"


constexpr auto x = 1;

constexpr auto foo()
{
    return 2;
}


int test()
{
    return x + foo();
}
