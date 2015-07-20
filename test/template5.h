const std::vector<std::pair<int,int>> v;

class RegionNode : public RegionNodeBase<RegionTraits<Function>> {
};

template <typename T1, typename T2>
struct FoldingSetTrait<std::pair<T1, T2>> {
};
