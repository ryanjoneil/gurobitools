from or782.model import ProxyModel

class LRModel(ProxyModel):
    def __init__(self, *args, **kwds):
        super(LRModel, self).__init__(*args, **kwds)
        self.penalties = {}
        self.multipliers = {}
        self.default_multiplier = 2.0
        self.start_step_size = 5.0
        self.epsilon = 10e-6

    def addLRConstr(self, temp_constr):
        '''
        Adds a dualized constraint to the model. Instead of adding a hard
        constraint, this creates a penalty variable and changes the
        objective function accordingly.
        '''
        # First add a variable.
        # Bound are determined by the constraint type:
        #       <=      penalty >= 0
        #       ==      penalty URS
        #       >=      penalty <= 0
        sense = getattr(temp_constr, '__sense')
        if sense == '<':
            p = self.addVar(lb=0)
        elif sense == '>':
            p = self.addVar(lb=-GRB.INFINITY, ub=0)
        else:
            p = self.addVar(lb=-GRB.INFINITY)

        # Now add a new constraint for the value of p.
        self.update()
        c = self.addConstr(
            p == getattr(temp_constr, '__rhs') - getattr(temp_constr, '__lhs')
        )
        self.update()
        print dir(c)

        # Save the constraint, penalty variable, and multiplier.
        self.penalties[c] = p
        return c

    def setObjective(self, expr):
        '''
        Adds the normal objective to the model, but includes dualized
        constraints in the objective function based on their senses.
        '''
        self.default_objective = expr

    def optimize(self, max_iterations=10):
        # TODO: docs
        # Copy the objective function into another expression so we can
        # play with it.
        penalty_cons = self.penalties.keys()

        self.multipliers = {pc: self.default_multiplier for pc in penalty_cons}

        denom = 1
        s = 10.0
        for i in xrange(max_iterations):
            lr_objective = self.default_objective + 0
            for j, pc in enumerate(penalty_cons):
                lr_objective = lr_objective + self.multipliers[pc] * self.penalties[pc]

            self.setObjective(lr_objective)
            super(LRModel, self).optimize()

            print 'iteration', i, 'obj =', '%.02f' % self.objVal, '| u =', \
                ' '.join(['%.02f' % self.multipliers[pc] for pc in penalty_cons]), \
                '| penalties = ', \
                ' '.join(['%.2f' % self.penalties[pc].x for pc in penalty_cons])

            # Only update step size every 100 iterations
            if not i % 10:
                s = 1.0 / denom
                denom += 1

            # Always update multipliers
            for pc in penalty_cons:
                self.multipliers[pc] -= s*(self.penalties[pc].x)

        self.setObjective(self.default_objective)


        # default multpliers...
        # step size

