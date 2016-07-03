#ifndef TEST_NOEXCEPT_H
#define TEST_NOEXCEPT_H

inline int no_except_test() noexcept
{
    return 0;
};

inline int no_except_test() noexcept(false)
{
    return 0;
};

#endif
