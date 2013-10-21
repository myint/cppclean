static int x = 1;
static int y = 1;
static const int z = 1;

class Foo
{
    void fct()
    {
        x = 2;
    }
};

int main()
{
    y = 3;
}
