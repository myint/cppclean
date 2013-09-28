
void SomeFunction() {}

static void static_functions_are_fine()
{
}

template <typename T>
void templated_functions_are_fine()
{
    T t;
    t.foo();
}
