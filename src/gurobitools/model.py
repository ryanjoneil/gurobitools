from gurobipy import Model, quicksum
from itertools import izip

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

def copy_model(model, to_class):
    '''Takes in a Gurobi Model instance and copies it to a subtype.'''
    # TODO: This only does linear constraints right now..
    # TODO: There *has* to be a better way to do this.
    m = to_class()

    # Add all variables and their bounds.
    var_map = {}
    for v in model.getVars():
        v2 = m.addVar(
            lb=v.lb, ub=v.ub, obj=v.obj, vtype=v.vtype, name=v.varName
        )
        var_map[v] = v2

    m.update()

    # Add all constraints, constructing expressions for them.
    for c in model.getConstrs():
        mexpr = model.getRow(c)
        expr = mexpr.getConstant()
        expr += quicksum(
            c*var_map[v] for c, v in izip(mexpr.__coeffs, mexpr.__vars)
        )

        if expr:
            if c.sense == '<':
                m.addConstr(expr <= c.rhs)
            elif c.sense == '>':
                m.addConstr(expr >= c.rhs)
            else:
                m.addConstr(expr == c.rhs)

    # And finally add the objective function.
    obj = model.getObjective()
    expr = obj.getConstant()
    for i in xrange(obj.size()):
        v = obj.getVar(i)
        coeff = obj.getCoeff(i)
        expr += coeff * var_map[v]

    m.setObjective(expr)

    m.modelSense = model.modelSense
    return m
