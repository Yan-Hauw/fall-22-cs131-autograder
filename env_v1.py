# The EnvironmentManager class keeps a mapping between each global variable (aka symbol)
# in a brewin program and the value of that variable - the value that's passed in can be
# anything you like. In our implementation we pass in a Value object which holds a type
# and a value (e.g., Int, 10).

import copy


class EnvironmentManager:
    def __init__(self):
        self.environment = {}

    # Gets the data associated a variable name
    def get(self, symbol):
        if symbol in self.environment:
            return self.environment[symbol]

        return None

    # Sets the data associated with a variable name
    def set(self, symbol, value):
        self.environment[symbol] = value

    def has_defined(self, symbol):
        return symbol in self.environment

    def create_new_scope(self):
        new_scope = EnvironmentManager()

        environment_copy = copy.deepcopy(self.environment)

        for name, value in environment_copy.items():
            value.defined_in_this_scope = False
            new_scope.set(name, value)
        return new_scope

    def create_output_dict(self):
        return self.environment
