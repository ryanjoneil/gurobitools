from or782.model import ProxyModel

class LRModel(ProxyModel):
    # This is ridiculous.
    ATTR = {
        'penalties': {},
        'default_multiplier': {}
    }

    def __init__(self, *args, **kwds):
        super(LRModel, self).__init__(*args, **kwds)
        self.penalties = []
        self.default_multiplier = 2.0
        self.epsilon = 10e-6

    def addLRConstr(self, temp_constr):
        '''
        Adds a dualized constraint to the model. Instead of adding a hard
        constraint, this creates a penalty variable and changes the
        objective function accordingly.
        '''
        # TODO: make this accept the non-TempConstr args
        print temp_constr
        print dir(temp_constr)
        import sys
        sys.exit()


