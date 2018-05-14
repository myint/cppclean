struct MyClass
{
	int A;
#if DEFINE
	int B;
#endif

	MyClass() : A(-1) 
#if DEFINE
		,B(42)
#endif
	{}
};