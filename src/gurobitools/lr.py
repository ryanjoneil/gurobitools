from gurobipy import GRB
from gurobitools.model import ProxyModel

class LRModel(ProxyModel):
    '''
    A Gurobi Model that handles the details of dualizing constraints for
    Lagrangian Relaxation in integer programs. The following methods are
    introduced to make this possible:

        - model.addLRConstr(expr): add a dualized constraint to the model
        - model.LRoptimize(): optimizes the dualized model repeatedly,
          until either primal feasibility and complementary slackness
          conditions are met, or a certain number of iterations have passed

    The following attributes are kept on the LRModel instance and available
    after calling LRModel.optimize. They can be set before the call to change
    the behavior of the model. Most of the automatically created variables
    and constraints are indexed by their respective penalty constraints.

        - model.default_multiplier: starting value for multipliers (2.0)
        - model.start_denominator: starting value for denominator (1.0)

        - model.max_iterations: max # of iterations (default=1000)
        - model.update_iterations: # of iterations to update step size (10)
        - model.epsilon: allowable error on termination conditions (10e-6)

    These fields are set and updated during optimization:

        - model.iteration: current iteration number
        - model.denominator: current denominator for computing step size
        - model.step_size: current step size

    These fields are filled in by calls to model.addLRConstr:

        - model.dualized_constraints: {penalty constr.: original constr.}
        - model.penalties: {penalty constr.: penalty variable}
        - model.multipliers: {penalty constr.: multiplier}
    '''
    def __init__(self, *args, **kwds):
        super(LRModel, self).__init__(*args, **kwds)

        self.dualized_constraints = {}
        self.penalties = {}
        self.multipliers = {}

        self.max_iterations = 1000
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
        # Save the objective for future use.
        super(LRModel, self).setObjective(expr)
        self.default_objective = expr

    def LRoptimize(self, debug=False):
        '''
        Iteratively optimizes the dualized model, adjusting penalty
        multiplier values and step size along the way. This will keep
        iterating until either max_iterations have been run or both primal
        feasibility and complementary slackness conditions are met.
        '''
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

            if debug:
                self.print_status()

            # Stopping criteria
            if self.primal_feasible() and self.complementary_slackness():
                break

            # Always update multipliers
            for pc in penalty_cons:
                self.multipliers[pc] -= self.step_size * self.penalties[pc].x

        self.setObjective(self.default_objective)

    def primal_feasible(self):
        '''
        Tests for feasibilty of the current solution against the original
        dualized constraints within an error of self.epsilon. That is, if the
        constraints were of the the following forms, they are subject to the
        corresponding tests:

            lhs <= rhs     ->      lhs <= rhs + epsilon
            lhs == rhs     ->      rhs - epsilon <= lhs <= rhs + epsilon
            lhs >= rhs     ->      lhs >= rhs - epsilon

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
            elif sense == '=':
                if lhs_val < rhs_val - eps or lhs_val > rhs_val + eps:
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
            if abs(self.multipliers[pc]) > self.epsilon and \
               abs(self.penalties[pc].x) > self.epsilon:
                return False

        return True

    def print_status(self):
        '''Prints a debugging status message to stdout.'''
        penalty_cons = self.penalties.keys()
        multipliers = [self.multipliers[pc] for pc in penalty_cons]
        penalty_vars = [self.penalties[pc] for pc in penalty_cons]

        print '[%d]' % self.iteration,
        print 'obj =', '%.02f' % self.objVal,
        print '| u =', ' '.join(['%.02f' % u for u in multipliers]),
        print '| penalties =', ' '.join(['%.2f' % p.x for p in penalty_vars]),
        print '| primal feasible =', self.primal_feasible(),
        print '| comp. slackness =', self.complementary_slackness()

