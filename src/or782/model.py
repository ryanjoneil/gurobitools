from gurobipy import GurobiError, Model

# I'm not sure exactly why. Maybe it's because Model is written in
# Cython, or perhaps Gurobi is doing something to error out on invalid
# uses of gettattr/setattr. Either way, we can't set arbitrary
# attributes on anything that inherits from Model. This is one of
# many possible workarounds, in which we store instance attributes
# that are not part of the Cython API on a proxy object.

class ProxyModel(type):
    '''A Gurobi `Model` that allows arbitary attributes on subclasses.'''
    def __new__(cls, *args, **kwds):
        print *args, **kwds
        type.__new__(cls, *args, **kwds)
        cls.PROXY = {}

    def __init__(self, *args, **kwds):
        # Create a proxy object on which to store extra attributes.
        type(self).PROXY[self] = object()
        super(ProxyModel, self).__init__(self, *args, **kwds)

    def __getattr__(self, attr):
        try:
            return super(LRModel, self).__getattr__(attr)
        except GurobiError, ge:
            try:
                return getattr(ProxyModel[self], attr)
            except AttributeError:
                raise ge

    def __setattr__(self, attr, value):
        try:
            return super(LRModel, self).__setattr__(attr, value)
        except GurobiError, ge:
            try:
                return setattr(ProxyModel[self], attr, value)
            except AttributeError:
                raise ge
