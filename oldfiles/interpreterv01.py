from intbase import *
from tokenize_helper import *
from utility_methods import *
from tests import *
from re import *
import sys


class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, input=None, trace_output=False):
        super().__init__(console_output, input)
        self.ip = 0
        self.name_to_value = {}
        self.indentations = []
        self.terminated = False
        self.prev_func_locations = []
        self.operators = [
            "+",
            "-",
            "*",
            "/",
            "%",
            "<",
            ">",
            "<=",
            ">=",
            "!=",
            "==",
            "&",
            "|",
        ]
        self.expression_stack = []
        self.show_trace_output = trace_output
        if not trace_output:
            sys.tracebacklimit = 0

    def run(self, program):
        self.program_statements = program
        super().reset()
        self.ip = func_def_location(program, "main")
        self.terminated = False

        self.indentations = get_indentations(program)  # returns a list of tuples

        print(f"indentations: {self.indentations}")

        while not self.terminated:
            self.interpret()

        print(self.name_to_value)

    def interpret(self):
        tokens = self.tokenize(self.program_statements[self.ip])

        print("on line: " + str(self.ip))

        print(tokens)

        if tokens and tokens[0] == "funccall":
            if tokens[1] == "input" or tokens[1] == "print":
                output = ""
                for t in tokens[2 : len(tokens)]:
                    output += str(self.get_value_from_token(t))
                super().output(output)

                if tokens[1] == "input":
                    input = super().get_input()
                    self.name_to_value["result"] = (input, 2)

            elif tokens[1] == "strtoint":
                val = self.get_value_from_token(tokens[2])

                if self.get_value_type(val) != 2:
                    super().error(ErrorType.TYPE_ERROR, "1", self.ip)

                val = int(val)

                self.name_to_value["result"] = (val, 1)

            else:
                self.prev_func_locations.append(self.ip + 1)

                self.ip = func_def_location(self.program_statements, tokens[1])

                if not self.ip:
                    super().error(ErrorType.NAME_ERROR, 2, self.ip)

                print(f"funccall {tokens[1]} at {self.ip}")
                return

        elif tokens and tokens[0] == "assign":
            # if len(tokens) == 3:

            if tokens[2] in self.operators:
                val = self.get_expression_value(tokens[2 : len(tokens)])
            else:
                val = self.get_value_from_token(tokens[2])

            self.name_to_value[tokens[1]] = self.create_tuple_with_type(val)

        elif tokens and tokens[0] == "return":
            if len(tokens) > 1:  # there is a return value

                if tokens[1] in self.operators:
                    val = self.get_expression_value(tokens[1 : len(tokens)])
                else:
                    val = self.get_value_from_token(tokens[1])

                self.name_to_value["result"] = self.create_tuple_with_type(val)

            self.ip = (
                self.prev_func_locations.pop() if self.prev_func_locations else self.ip
            )
            return

        elif tokens and tokens[0] == "endfunc":
            if self.prev_func_locations:
                self.ip = self.prev_func_locations.pop()
            else:
                self.terminated = True
            return

        elif tokens and tokens[0] == "if":

            if tokens[1] in self.operators:
                val = self.get_expression_value(tokens[1 : len(tokens)])
            else:
                val = self.get_value_from_token(tokens[1])

            if self.get_value_type(val) != 3:
                super().error(ErrorType.TYPE_ERROR, "1", self.ip)

            if not val:
                indentation = self.indentations[self.ip]

                if not self.else_location(
                    self.program_statements, self.ip + 1, indentation
                ):

                    self.ip = self.endif_location(
                        self.program_statements, self.ip + 1, indentation
                    )
                    return

                if self.else_location(
                    self.program_statements, self.ip + 1, indentation
                ) > self.endif_location(
                    self.program_statements, self.ip + 1, indentation
                ):

                    self.ip = self.endif_location(
                        self.program_statements, self.ip + 1, indentation
                    )
                    return

                self.ip = self.else_location(
                    self.program_statements, self.ip + 1, indentation
                )
                return

            self.ip += 1

            return

        elif tokens and tokens[0] == "else":  # must have gotten here after if True
            indentation = self.indentations[self.ip]
            self.ip = self.endif_location(
                self.program_statements, self.ip + 1, indentation
            )
            return

        elif tokens and tokens[0] == "while":

            if tokens[1] in self.operators:
                val = self.get_expression_value(tokens[1 : len(tokens)])
            else:
                val = self.get_value_from_token(tokens[1])

            if self.get_value_type(val) != 3:
                super().error(ErrorType.TYPE_ERROR, "1", self.ip)

            if not val:
                indentation = self.indentations[self.ip]

                self.ip = self.endwhile_location(
                    self.program_statements, self.ip + 1, indentation
                )
                return

        elif (
            tokens and tokens[0] == "endwhile"
        ):  # must have gotten here after while True
            indentation = self.indentations[self.ip]

            self.ip = self.while_location(
                self.program_statements, self.ip - 1, indentation
            )

            return

        self.ip += 1

        return

    def while_location(self, program, start_point, indentation):
        for i in range(start_point, -1, -1):
            print(self.indentations[i], indentation)

            if (
                match("^ *" + "while", program[i])
                and self.indentations[i] == indentation
            ):
                return i

    def endwhile_location(self, program, start_point, indentation):

        for i in range(start_point, len(program)):
            print(self.indentations[i], indentation)

            if (
                match("^ *" + "endwhile", program[i])
                and self.indentations[i] == indentation
            ):
                return i + 1

    def endif_location(self, program, start_point, indentation):

        for i in range(start_point, len(program)):
            print(self.indentations[i], indentation)

            if (
                match("^ *" + "endif", program[i])
                and self.indentations[i] == indentation
            ):
                return i + 1

    def else_location(self, program, start_point, indentation):
        position = False
        for i in range(start_point, len(program)):
            if (
                match("^ *" + "else", program[i])
                and self.indentations[i] == indentation
            ):
                return i + 1
        return position

    def tokenize(self, statement):

        statement = remove_comments(statement)

        # print(statement)

        tokens = remove_spaces(statement)

        # print(tokens)

        return tokens

    def get_expression_value(self, expression):
        for i in reversed(range(len(expression))):
            token_value = expression[i]

            # print("i" + str(self.get_value_from_token(token_value)))

            # print("bool: " + str(token_value not in self.operators))

            # print(self.expression_stack)

            if token_value not in self.operators:
                self.expression_stack.append(self.get_value_from_token(token_value))
            else:
                operand1 = self.expression_stack.pop()
                operand2 = self.expression_stack.pop()

                # print(
                #     "operand1: "
                #     + str(self.get_value_type(operand1))
                #     + ", operand2: "
                #     + str(self.get_value_type(operand2))
                # )

                lone_expression = [token_value, operand1, operand2]

                if self.is_valid_expression(lone_expression):
                    if self.get_value_type(operand1) == 1:
                        lone_expression_result = self.get_int_exp_result(
                            lone_expression
                        )
                    elif self.get_value_type(operand1) == 2:
                        lone_expression_result = self.get_string_exp_result(
                            lone_expression
                        )
                    elif self.get_value_type(operand1) == 3:
                        lone_expression_result = self.get_boolean_exp_result(
                            lone_expression
                        )

                    self.expression_stack.append(lone_expression_result)

        res = self.expression_stack.pop()

        return res

    def is_valid_expression(self, expression):
        t1 = self.get_value_type(expression[1])
        t2 = self.get_value_type(expression[2])

        # print(t1, t2)

        if t1 != t2:
            super().error(ErrorType.TYPE_ERROR, "1", self.ip)

        operator = expression[0]

        if (t1 == 1 or t2 == 1) and operator in ["&", "|"]:
            super().error(ErrorType.TYPE_ERROR, "1", self.ip)
        elif (t1 == 2 or t2 == 2) and operator in [
            "-",
            "*",
            "/",
            "%",
            "&",
            "|",
        ]:
            super().error(ErrorType.TYPE_ERROR, "1", self.ip)
        elif (t1 == 3 or t2 == 3) and operator in [
            "+",
            "-",
            "*",
            "/",
            "%",
            "<",
            ">",
            "<=",
            ">=",
        ]:
            super().error(ErrorType.TYPE_ERROR, "1", self.ip)

        return True

    def get_value_type(self, value):
        if type(value) == int:
            return 1
        elif value == "True" or value == True or value == "False" or value == False:
            return 3
        else:  # token is a string
            return 2

    def get_int_exp_result(self, expression):
        if expression[0] == "+":
            res = expression[1] + expression[2]
        elif expression[0] == "-":
            res = expression[1] - expression[2]
        elif expression[0] == "*":
            res = expression[1] * expression[2]
        elif expression[0] == "/":
            res = expression[1] // expression[2]
        elif expression[0] == "%":
            res = expression[1] % expression[2]
        elif expression[0] == "<":
            res = expression[1] < expression[2]
        elif expression[0] == ">":
            res = expression[1] > expression[2]
        elif expression[0] == "<=":
            res = expression[1] <= expression[2]
        elif expression[0] == ">=":
            res = expression[1] >= expression[2]
        elif expression[0] == "!=":
            res = expression[1] != expression[2]
        elif expression[0] == "==":
            res = expression[1] == expression[2]
        return res

    def get_string_exp_result(self, expression):
        if expression[0] == "+":
            res = expression[1] + expression[2]
        elif expression[0] == "<":
            res = expression[1] < expression[2]
        elif expression[0] == ">":
            res = expression[1] > expression[2]
        elif expression[0] == "<=":
            res = expression[1] <= expression[2]
        elif expression[0] == ">=":
            res = expression[1] >= expression[2]
        elif expression[0] == "!=":
            res = expression[1] != expression[2]
        elif expression[0] == "==":
            res = expression[1] == expression[2]
        return res

    def get_boolean_exp_result(self, expression):
        if expression[0] == "&":
            res = expression[1] and expression[2]
        elif expression[0] == "|":
            res = expression[1] or expression[2]
        elif expression[0] == "!=":
            res = expression[1] != expression[2]
        elif expression[0] == "==":
            res = expression[1] == expression[2]
        return res

    def get_value_from_token(self, token):
        if token == "True":
            val = True
        elif token == "False":
            val = False
        elif token[0] == '"':
            val = token[1 : (len(token) - 1)]
        elif match("^[0-9]", token):
            val = int(token)
        elif match("^-(?=[0-9])", token):
            val = int(token)
        elif token in self.name_to_value:
            val = self.name_to_value[token][0]
        elif token not in self.name_to_value:
            super().error(ErrorType.NAME_ERROR, "2", self.ip)
        else:
            pass

        return val

    def create_tuple_with_type(self, val):
        if type(val) == int:
            # print(val)
            return (val, 1)
        elif val == True:
            return (True, 3)
        elif val == False:
            return (False, 3)
        else:
            return (val, 2)

    # 'assign f + + "4#4" "5" "3#3"    # "asdf"  # 123   #ou     ',


interpreter = Interpreter(True, None, True)
