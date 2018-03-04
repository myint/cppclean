class QSomeClass;

class QSomeOtherClass {
    QPointer<QSomeClass> ptr1;
    QSharedDataPointer<QSomeClass> ptr2;
    QSharedPointer<QSomeClass> ptr3;
    QWeakPointer<QSomeClass> ptr4;
    QScopedPointer<QSomeClass> ptr5;
    QScopedArrayPointer<QSomeClass> ptr6;
};
