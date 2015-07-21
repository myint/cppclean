class CMyClass
{
public:
  CMyClass();

private:
  std::function<void(double, double)> mFunctor;
  static const bool b1 = sizeof(int) > 4;
};
