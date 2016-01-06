class X {
  X& operator=(const X&) = delete;
  X(const X&) = delete;
};

class Y {
  Y& operator=(const Y&) = default;
  Y(const Y&) = default;
};

auto bar(void) -> void;

const struct {
char c[2];
} c = {.c={'\1'}};
