template <class T>
std::function<void(T)>
foo() {
    return [&](T a) {return a.method();};
}
