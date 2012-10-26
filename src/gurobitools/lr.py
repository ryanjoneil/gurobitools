from gurobipy import GRB
from gurobitools.model import ProxyModel

class LRModel(ProxyModel):
    def __init__(self, *args, **kwds):
        super(LRModel, self).__init__(*args, **kwds)

        self.dualized_constraints = {}
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

    def addLRConstr(self, temp_constr):
        '''
        Adds a dualized constraint to the model. Instead of adding a hard
        constraint, this creates a penalty variable and changes the
        objective function accordingly.

        Returns the equality constraint for the new penalty variable.
        '''
        # First add a variable. Bounds are determined by constraint type:
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

        # Save the original constraint that's being dualized.
        self.dualized_constraints[c] = temp_constr
        return c

    def setObjective(self, expr):
        '''
        Adds the normal objective to the model, but includes dualized
        constraints in the objective function based on their senses.
        '''
        self.default_objective = expr
        super(LRModel, self).setObjective(expr)

    def LRoptimize(self):
        # TODO: docs

        # Penalty variables & multipliers are indexed by penalty constraints.
        penalty_cons = self.penalties.keys()

        # Start values for multipliers and other things.
        self.multipliers = {pc: self.default_multiplier for pc in penalty_cons}
        self.denominator = self.start_denominator

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

    def primal_feasible(self):
        '''
        Tests for feasibilty of the current solution against the original
        dualized constraints within an error of self.epsilon. That is, if the
        constraints were of the the following forms, they are subject to the
        corresponding tests:

            expr <= rhs     ->      expr <= rhs + epsilon
            expr == rhs     ->      rhs - epsilon <= expr <= rhs + epsilon
            expr >= rhs     ->      expr >= rhs - epsilon

        Return True if the current solution is primal feasible, False if not.
        '''
        for pc in self.penalties:
            # Pull out info on the original constraint.
            c = self.dualized_constraints[pc]
            sense = getattr(c, '__sense')
            lhs = getattr(c, '__lhs')
            rhs = getattr(c, '__rhs')
            eps = self.epsilon

            # Convert to numeric values if these are expressions.
            try:
                lhs_val = lhs.getValue()
            except AttributeError:
                lhs_val = lhs

            try:
                rhs_val = rhs.getValue()
            except AttributeError:
                rhs_val = rhs

            # Test for feasibility.
            if sense == '<' and lhs_val > rhs_val + eps:
                return False
            elif sense == '>' and lhs_val < rhs_val - eps:
                return False
            elif lhs_val < rhs_val - eps or lhs_val > rhs_val + eps:
                return False

        return True

    def complementary_slackness(self):
        '''
        Tests for complementary slackness conditions against the penalty
        variable values and their associated multipliers. For each pair,
        these conditions are met if either is with self.epsilon of 0.

        Return True if the current solution meets complementary slackness
        conditions for all dualized constraints, False otherwise.
        '''
        for pc in self.penalties:
            if abs(self.multipliers[pc]) > self.epsilon:
                return False
            elif abs(self.penalties[pc].x) > self.epsilon:
                return False

        return True

