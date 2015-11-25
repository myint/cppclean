class SharedCount {
  friend inline bool operator==(SharedCount const & a, SharedCount const & b)
  {
    return a._pi == b._pi;
  }
};
