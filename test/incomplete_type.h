class Foo;
void fn(Foo f);
void fn(Foo* f = 0);
void fn(Foo* f = NULL);
void fn(Foo* f = nullptr);

#include "bar.h"
void fn(Bar* b = new Bar);
