from gurobipy import Model

# I'm not sure exactly why. Maybe it's because Model is written in
# Cython, or perhaps Gurobi is doing something to error out on invalid
# uses of gettattr/setattr. Either way, we can't set arbitrary
# attributes on anything that inherits from Model. This is one of
# many possible workarounds, in which we store instance attributes
# that are not part of the Cython API on a proxy object.


class ProxyModel(Model):
    '''A Gurobi `Model` that allows arbitary attributes on subclasses.'''
    PROXY = {}

    class Proxy(object):
        '''This class does nothing but store attributes.'''

    def __init__(self, *args, **kwds):
        # Create a proxy object on which to store extra attributes.
        ProxyModel.PROXY[self] = ProxyModel.Proxy()
        super(ProxyModel, self).__init__(*args, **kwds)

    def __getattr__(self, attr):
        try:
            return super(ProxyModel, self).__getattr__(attr)
        except Exception, e:
            try:
                return getattr(ProxyModel.PROXY[self], attr)
            except AttributeError:
                raise e

    def __setattr__(self, attr, value):
        try:
            return super(ProxyModel, self).__setattr__(attr, value)
        except Exception, e:
            try:
                return setattr(ProxyModel.PROXY[self], attr, value)
            except AttributeError:
                raise e
