from gurobipy import GRB
from or782.model import ProxyModel

class LRModel(ProxyModel):
    def __init__(self, *args, **kwds):
        super(LRModel, self).__init__(*args, **kwds)

        self.penalties = {}
        self.multipliers = {}

        self.max_iterations = 100
        self.update_iterations = 10
        self.epsilon = 10e-6

        self.iteration = 0
        self.denominator = 0
        self.step_size = 0

        self.default_multiplier = 2.0
        self.start_denominator = 1.0
        self.start_step_size = 1.0

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

        # Save the constraint, penalty variable, and multiplier.
        self.penalties[c] = p
        return c

    def setObjective(self, expr):
        '''
        Adds the normal objective to the model, but includes dualized
        constraints in the objective function based on their senses.
        '''
        self.default_objective = expr

    def optimize(self):
        # TODO: docs

        # Penalty variables & multipliers are indexed by penalty constraints.
        penalty_cons = self.penalties.keys()

        # Start values for multipliers and other things.
        self.multipliers = {pc: self.default_multiplier for pc in penalty_cons}
        self.denominator = self.start_denominator
        self.step_size = self.start_step_size

        for i in xrange(self.max_iterations):
            self.iteration = i+1

            # Add the LR multipliers and penalties to the objective function.
            lr_objective = self.default_objective + 0
            for j, pc in enumerate(penalty_cons):
                multiplier = self.multipliers[pc]
                penalty = self.penalties[pc]
                lr_objective = lr_objective + multiplier * penalty

            # Set the altered objective and optimize.
            super(LRModel, self).setObjective(lr_objective)
            super(LRModel, self).optimize()

            # Only update step size every n iterations.
            if not i % self.update_iterations:
                self.step_size = 1.0 / self.denominator
                self.denominator += 1

            # Always update multipliers
            for pc in penalty_cons:
                self.multipliers[pc] -= self.step_size * self.penalties[pc].x

            # TODO: test for stopping criteria
            yield self

        self.setObjective(self.default_objective)

