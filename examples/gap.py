#!/usr/bin/env python

# This is the GAP per Wolsey.
from gurobipy import GRB, quicksum as sum
from gurobitools import LRModel

model = LRModel('GAP per Wolsey')
model.modelSense = GRB.MAXIMIZE
model.setParam('OutputFlag', False) # turns off solver chatter

b = [15, 15, 15]
c = [
    [ 6, 10,  1],
    [12, 12,  5],
    [15,  4,  3],
    [10,  3,  9],
    [ 8,  9,  5]
]
a = [
    [ 5,  7,  2],
    [14,  8,  7],
    [10,  6, 12],
    [ 8,  4, 15],
    [ 6, 12,  5]
]

# x[i][j] = 1 if i is assigned to j
x = []
for i in range(len(c)):
    x_i = []
    for j in c[i]:
        x_i.append(model.addVar(vtype=GRB.BINARY))
    x.append(x_i)

# We have to update the model so it knows about new variables.
model.update()

# sum <j> x_ij <= 1 for all i
for x_i in x:
    model.addLRConstr(sum(x_i) <= 1)

# sum <i> a_ij * x_ij <= b[j] for all j
for j in range(len(b)):
    model.addConstr(sum(a[i][j] * x[i][j] for i in range(len(x))) <= b[j])

# max sum <i,j> c_ij * x_ij
model.setObjective(
    sum(
        sum(c_ij * x_ij for c_ij, x_ij in zip(c_i, x_i))
        for c_i, x_i in zip(c, x)
    )
)

# Iteratively optimize using the LR model.
for m in model.LRoptimize():
    penalty_cons = m.penalties.keys()
    multipliers = [m.multipliers[pc] for pc in penalty_cons]
    penalty_vars = [m.penalties[pc] for pc in penalty_cons]

    print '[%d]' % m.iteration,
    print 'obj =', '%.02f' % m.objVal,
    print '| u =', ' '.join(['%.02f' % u for u in multipliers]),
    print '| penalties =', ' '.join(['%.2f' % p.x for p in penalty_vars]),
    print '| primal feasible =', m.primal_feasible(),
    print '| comp. slackness =', m.complementary_slackness()

# Pull objective and variable values out of model
print 'objective =', model.objVal
print 'x = ['
for x_i in x:
    print '   ', [1 if x_ij.x >= 0.5 else 0 for x_ij in x_i]
print ']'
