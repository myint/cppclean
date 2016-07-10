class Foo :
#if defined(WCHAR_MIN) && defined(WCHAR_MAX)
    public Bar
#else
#error ERROR
#endif
{
};
