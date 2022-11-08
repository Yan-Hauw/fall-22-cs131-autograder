import copy
from enum import Enum
from intbase import InterpreterBase, ErrorType
from env_v1 import EnvironmentManager
from tokenize import Tokenizer
from func_v1 import FunctionManager

# Enumerated type for our different language data types
class Type(Enum):
    INT = 1
    BOOL = 2
    STRING = 3


# Represents a value, which has a type and its value
class Value:
    def __init__(self, type, defined_here, value=None):
        self.t = type
        self.v = value
        self.defined_in_this_scope = defined_here

    def get_value(self):
        return self.v

    def set(self, other):
        self.t = other.t
        self.v = other.v

    def get_type(self):
        return self.t

    def set_defined_here_flag(self, defined_here):
        self.defined_in_this_scope = defined_here
        return

    def set_value(self, value):
        print("success")
        self.value = value
        return

    def create_output_tuple(self):
        return (self.t, self.defined_in_this_scope, self.v)


class ScopeStack:
    def __init__(self):
        self.scope_stack = []
        self.scope_stack.append(EnvironmentManager())
        return

    def get_top_level_scope(self):
        return

    def get_current_scope(self):
        return self.scope_stack[-1] if self.scope_stack else EnvironmentManager()

    def create_new_inner_scope(self, scope):
        # print("enter")
        self.scope_stack.append(scope)
        return

    def leave_inner_scope(self):
        # print("leave")
        self.scope_stack.pop()
        return

    def create_output_list(self):
        return self.scope_stack

    def get_scope_by_index(self, index):
        return self.scope_stack[index]


class FunctionStack:
    def __init__(self):
        self.function_stack = []
        self.function_stack.append(ScopeStack())
        return

    def get_current_function(self):
        return self.function_stack[-1]

    def append_new_scope_stack(self):
        self.function_stack.append(ScopeStack())
        return

    def produce_output_object(self):
        out = []
        for scope_stack in self.function_stack:
            inner_list = []
            for scope in scope_stack.create_output_list():
                scope_dict = {
                    name: var.create_output_tuple()
                    for name, var in scope.create_output_dict().items()
                }
                inner_list.append(scope_dict)

            out.append(inner_list)

        return out

    def create_output_list(self):
        return self.function_stack


# Main interpreter class
class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, input=None, trace_output=True):
        super().__init__(console_output, input)
        self._setup_operations()  # setup all valid binary operations and the types they work on
        self.trace_output = trace_output

    # run a program, provided in an array of strings, one string per line of source code
    def run(self, program):
        self.program = program
        self._compute_indentation(program)  # determine indentation of every line
        self.tokenized_program = Tokenizer.tokenize_program(program)
        self.func_manager = FunctionManager(self.tokenized_program)
        self.ip = self._find_first_instruction(InterpreterBase.MAIN_FUNC)
        self.return_stack = []
        self.function_stack = FunctionStack()
        self.terminate = False

        # main interpreter run loop
        while not self.terminate:
            print(self.ip)
            self._process_line()
            print(self.function_stack.produce_output_object())

    def _process_line(self):
        if self.trace_output:
            print(f"{self.ip:04}: {self.program[self.ip].rstrip()}")
        tokens = self.tokenized_program[self.ip]
        if not tokens:
            self._blank_line()
            return

        args = tokens[1:]

        match tokens[0]:
            case InterpreterBase.VAR_DEF:
                self._define(args)
            case InterpreterBase.ASSIGN_DEF:
                self._assign(args)
            case InterpreterBase.FUNCCALL_DEF:
                self._funccall(args)
            case InterpreterBase.ENDFUNC_DEF:
                self._endfunc()
            case InterpreterBase.IF_DEF:
                self._if(args)
            case InterpreterBase.ELSE_DEF:
                self._else()
            case InterpreterBase.ENDIF_DEF:
                self._endif()
            case InterpreterBase.RETURN_DEF:
                self._return(args)
            case InterpreterBase.WHILE_DEF:
                self._while(args)
            case InterpreterBase.ENDWHILE_DEF:
                self._endwhile(args)
            case default:
                raise Exception(f"Unknown command: {tokens[0]}")

    def _blank_line(self):
        self._advance_to_next_statement()

    def _define(self, args):
        type = args[0]
        current_scope = self.function_stack.get_current_function().get_current_scope()

        for varname in args[1 : len(args)]:

            value_obj = current_scope.get(varname)

            # if variable already defined in this scope
            if value_obj and value_obj.defined_in_this_scope == True:
                super().error(
                    ErrorType.NAME_ERROR,
                    f"Trying to redefine var in same scope",
                    self.ip,
                )  # no

            # if definition of unknown type
            # not tested

            # else not yet defined or shadowing
            else:
                new_value_object = self.create_default_object(type)
                self._set_value(varname, new_value_object)

        self._advance_to_next_statement()

    def _assign(self, tokens):
        if len(tokens) < 2:
            super().error(ErrorType.SYNTAX_ERROR, "Invalid assignment statement")  # no
        vname = tokens[0]

        current_scope = self.function_stack.get_current_function().get_current_scope()

        if not current_scope.has_defined(vname):
            super().error(
                ErrorType.NAME_ERROR,
                f"Trying to assign undefined variable",
                self.ip,
            )  # no

        value_type = self._eval_expression(tokens[1:])

        # We just get the result of the operation,
        # then change the flag value after we get the result
        initial_value_obj = current_scope.get(vname)

        if initial_value_obj and initial_value_obj.defined_in_this_scope == True:
            value_type.defined_in_this_scope = True

        if initial_value_obj.get_type() != value_type.get_type():
            super().error(
                ErrorType.TYPE_ERROR,
                f"Mismatching types {initial_value_obj.get_type()} and {value_type.get_type()}",
                self.ip,
            )  #!

        # self._set_value(tokens[0], value_type)

        self.propagate_normal_variable(vname, value_type.get_value())
        self._advance_to_next_statement()

    def _funccall(self, args):
        if not args:
            super().error(
                ErrorType.SYNTAX_ERROR, "Missing function name to call", self.ip
            )  #!
        if args[0] == InterpreterBase.PRINT_DEF:
            self._print(args[1:])
            self._advance_to_next_statement()
        elif args[0] == InterpreterBase.INPUT_DEF:
            self._input(args[1:])
            self._advance_to_next_statement()
        elif args[0] == InterpreterBase.STRTOINT_DEF:
            self._strtoint(args[1:])
            self._advance_to_next_statement()
        else:
            self.return_stack.append(self.ip + 1)
            self.ip = self._find_first_instruction(args[0])

            # still need to append the arguments list to the end of previous stack
            self.function_stack.append_new_scope_stack()

    def _endfunc(self):
        if not self.return_stack:  # done with main!
            self.terminate = True
        else:
            self.ip = self.return_stack.pop()

    def _if(self, args):
        if not args:
            super().error(ErrorType.SYNTAX_ERROR, "Invalid if syntax", self.ip)  # no
        value_type = self._eval_expression(args)
        if value_type.get_type() != Type.BOOL:
            super().error(
                ErrorType.TYPE_ERROR, "Non-boolean if expression", self.ip
            )  #!
        if value_type.get_value():
            self._advance_to_next_statement()

            self.enter_new_scope()

            return
        else:
            for line_num in range(self.ip + 1, len(self.tokenized_program)):
                tokens = self.tokenized_program[line_num]
                if not tokens:
                    continue
                if (
                    tokens[0] == InterpreterBase.ENDIF_DEF
                    or tokens[0] == InterpreterBase.ELSE_DEF
                ) and self.indents[self.ip] == self.indents[line_num]:
                    self.ip = line_num + 1
                    if tokens[0] == InterpreterBase.ELSE_DEF:
                        self.enter_new_scope()
                    return
        super().error(ErrorType.SYNTAX_ERROR, "Missing endif", self.ip)  # no

    def _endif(self):
        self._advance_to_next_statement()
        self.leave_scope()

    def _else(self):
        for line_num in range(self.ip + 1, len(self.tokenized_program)):
            tokens = self.tokenized_program[line_num]
            if not tokens:
                continue
            if (
                tokens[0] == InterpreterBase.ENDIF_DEF
                and self.indents[self.ip] == self.indents[line_num]
            ):
                self.ip = line_num + 1
                self.leave_scope()
                return
        super().error(ErrorType.SYNTAX_ERROR, "Missing endif", self.ip)  # no

    def _return(self, args):
        if not args:
            self._endfunc()
            return
        value_type = self._eval_expression(args)
        self._set_value(
            InterpreterBase.RESULT_DEF, value_type
        )  # return always passed back in result
        self._endfunc()

    def _while(self, args):
        if not args:
            super().error(
                ErrorType.SYNTAX_ERROR, "Missing while expression", self.ip
            )  # no
        value_type = self._eval_expression(args)
        if value_type.get_type() != Type.BOOL:
            super().error(
                ErrorType.TYPE_ERROR, "Non-boolean while expression", self.ip
            )  #!
        if value_type.get_value() == False:
            self._exit_while()
            return

        # If true, we advance to the next statement
        self._advance_to_next_statement()
        self.enter_new_scope()

    def _exit_while(self):
        while_indent = self.indents[self.ip]
        cur_line = self.ip + 1
        while cur_line < len(self.tokenized_program):
            if (
                self.tokenized_program[cur_line][0] == InterpreterBase.ENDWHILE_DEF
                and self.indents[cur_line] == while_indent
            ):
                self.ip = cur_line + 1
                return
            if (
                self.tokenized_program[cur_line]
                and self.indents[cur_line] < self.indents[self.ip]
            ):
                break  # syntax error!
            cur_line += 1
        # didn't find endwhile
        super().error(ErrorType.SYNTAX_ERROR, "Missing endwhile", self.ip)  # no

    def _endwhile(self, args):
        while_indent = self.indents[self.ip]
        cur_line = self.ip - 1
        while cur_line >= 0:
            if (
                self.tokenized_program[cur_line][0] == InterpreterBase.WHILE_DEF
                and self.indents[cur_line] == while_indent
            ):
                self.ip = cur_line
                self.leave_scope()
                return
            if (
                self.tokenized_program[cur_line]
                and self.indents[cur_line] < self.indents[self.ip]
            ):
                break  # syntax error!
            cur_line -= 1
        # didn't find while
        super().error(ErrorType.SYNTAX_ERROR, "Missing while", self.ip)  # no

    def _print(self, args):
        if not args:
            super().error(
                ErrorType.SYNTAX_ERROR, "Invalid print call syntax", self.ip
            )  # no
        out = []
        for arg in args:
            val_type = self._get_value(arg)
            out.append(str(val_type.get_value()))
        super().output("".join(out))

    def _input(self, args):
        if args:
            self._print(args)
        result = super().get_input()
        self._set_value(
            InterpreterBase.RESULT_DEF, Value(Type.STRING, False, result)
        )  # return always passed back in result

    def _strtoint(self, args):
        if len(args) != 1:
            super().error(
                ErrorType.SYNTAX_ERROR, "Invalid strtoint call syntax", self.ip
            )  # no
        value_type = self._get_value(args[0])
        if value_type.get_type() != Type.STRING:
            super().error(
                ErrorType.TYPE_ERROR, "Non-string passed to strtoint", self.ip
            )  #!
        self._set_value(
            InterpreterBase.RESULT_DEF,
            Value(Type.INT, False, int(value_type.get_value())),
        )  # return always passed back in result

    def _advance_to_next_statement(self):
        # for now just increment IP, but later deal with loops, returns, end of functions, etc.
        self.ip += 1

    # create a lookup table of code to run for different operators on different types
    def _setup_operations(self):
        self.binary_op_list = [
            "+",
            "-",
            "*",
            "/",
            "%",
            "==",
            "!=",
            "<",
            "<=",
            ">",
            ">=",
            "&",
            "|",
        ]
        self.binary_ops = {}
        self.binary_ops[Type.INT] = {
            "+": lambda a, b: Value(Type.INT, False, a.get_value() + b.get_value()),
            "-": lambda a, b: Value(Type.INT, False, a.get_value() - b.get_value()),
            "*": lambda a, b: Value(Type.INT, False, a.get_value() * b.get_value()),
            "/": lambda a, b: Value(
                Type.INT, False, a.get_value() // b.get_value()
            ),  # // for integer ops
            "%": lambda a, b: Value(Type.INT, False, a.get_value() % b.get_value()),
            "==": lambda a, b: Value(Type.BOOL, False, a.get_value() == b.get_value()),
            "!=": lambda a, b: Value(Type.BOOL, False, a.get_value() != b.get_value()),
            ">": lambda a, b: Value(Type.BOOL, False, a.get_value() > b.get_value()),
            "<": lambda a, b: Value(Type.BOOL, False, a.get_value() < b.get_value()),
            ">=": lambda a, b: Value(Type.BOOL, False, a.get_value() >= b.get_value()),
            "<=": lambda a, b: Value(Type.BOOL, False, a.get_value() <= b.get_value()),
        }
        self.binary_ops[Type.STRING] = {
            "+": lambda a, b: Value(Type.STRING, False, a.get_value() + b.get_value()),
            "==": lambda a, b: Value(Type.BOOL, False, a.get_value() == b.get_value()),
            "!=": lambda a, b: Value(Type.BOOL, False, a.get_value() != b.get_value()),
            ">": lambda a, b: Value(Type.BOOL, False, a.get_value() > b.get_value()),
            "<": lambda a, b: Value(Type.BOOL, False, a.get_value() < b.get_value()),
            ">=": lambda a, b: Value(Type.BOOL, False, a.get_value() >= b.get_value()),
            "<=": lambda a, b: Value(Type.BOOL, False, a.get_value() <= b.get_value()),
        }
        self.binary_ops[Type.BOOL] = {
            "&": lambda a, b: Value(Type.BOOL, False, a.get_value() and b.get_value()),
            "==": lambda a, b: Value(Type.BOOL, False, a.get_value() == b.get_value()),
            "!=": lambda a, b: Value(Type.BOOL, False, a.get_value() != b.get_value()),
            "|": lambda a, b: Value(Type.BOOL, False, a.get_value() or b.get_value()),
        }

    def _compute_indentation(self, program):
        self.indents = [len(line) - len(line.lstrip(" ")) for line in program]

    def _find_first_instruction(self, funcname):
        func_info = self.func_manager.get_function_info(funcname)
        if func_info == None:
            super().error(
                ErrorType.NAME_ERROR, f"Unable to locate {funcname} function", self.ip
            )  #!
        return func_info.start_ip

    # given a token name (e.g., x, 17, True, "foo"), give us a Value object associated with it
    def _get_value(self, token):
        if not token:
            super().error(ErrorType.NAME_ERROR, f"Empty token", self.ip)  # no
        if token[0] == '"':
            return Value(Type.STRING, False, token.strip('"'))
        if token.isdigit() or token[0] == "-":
            return Value(Type.INT, False, int(token))
        if token == InterpreterBase.TRUE_DEF or token == InterpreterBase.FALSE_DEF:
            return Value(Type.BOOL, False, token == InterpreterBase.TRUE_DEF)

        value = (
            self.function_stack.get_current_function().get_current_scope().get(token)
        )
        #
        #
        #        value = self.env_manager.get(token)
        #
        #
        if value == None:
            super().error(
                ErrorType.NAME_ERROR, f"Unknown variable {token}", self.ip
            )  #!
        return value

    # given a variable name and a Value object, associate the name with the value
    def _set_value(self, varname, value_type):
        current_scope = self.function_stack.get_current_function().get_current_scope()
        current_scope.set(varname, value_type)

    #
    #
    #        self.env_manager.set(varname, value_type)
    #
    #

    # evaluate expressions in prefix notation: + 5 * 6 x
    def _eval_expression(self, tokens):
        stack = []

        for token in reversed(tokens):
            if token in self.binary_op_list:
                v1 = stack.pop()
                v2 = stack.pop()
                if v1.get_type() != v2.get_type():
                    super().error(
                        ErrorType.TYPE_ERROR,
                        f"Mismatching types {v1.get_type()} and {v2.get_type()}",
                        self.ip,
                    )  #!
                operations = self.binary_ops[v1.get_type()]
                if token not in operations:
                    super().error(
                        ErrorType.TYPE_ERROR,
                        f"Operator {token} is not compatible with {v1.get_type()}",
                        self.ip,
                    )  #!

                stack.append(operations[token](v1, v2))
                # print(stack)
            elif token == "!":
                v1 = stack.pop()
                if v1.get_type() != Type.BOOL:
                    super().error(
                        ErrorType.TYPE_ERROR,
                        f"Expecting boolean for ! {v1.get_type()}",
                        self.ip,
                    )  #!
                stack.append(Value(Type.BOOL, not v1.get_value()))
            else:
                value_type = self._get_value(token)
                stack.append(value_type)

        if len(stack) != 1:
            super().error(ErrorType.SYNTAX_ERROR, f"Invalid expression", self.ip)  # no

        return stack[0]

    def enter_new_scope(self):
        # copy variables from previous scope
        # need to loop through dictionary of scope to set all variable-defined-flags to False
        current_scope = self.function_stack.get_current_function().get_current_scope()
        # print(current_scope)

        new_scope = current_scope.create_new_scope()

        self.function_stack.get_current_function().create_new_inner_scope(new_scope)
        return

    def leave_scope(self):
        current_function = self.function_stack.get_current_function()
        current_function.leave_inner_scope()
        return

    def create_default_object(self, type):
        if type == "int":
            return Value(Type.INT, True, 0)
        elif type == "bool":
            return Value(Type.BOOL, True, False)
        elif type == "string":
            return Value(Type.STRING, True, "")

    def propagate_normal_variable(self, varname, value_to_propagate):

        current_scope_stack = self.function_stack.get_current_function()

        scope_stack_length = len(current_scope_stack.create_output_list())

        for i in range(scope_stack_length - 1, -1, -1):

            print(i)

            current_scope = (
                self.function_stack.get_current_function().get_scope_by_index(i)
            )

            old_obj = current_scope.get(varname)

            current_scope.set(
                varname,
                Value(
                    old_obj.get_type(),
                    old_obj.defined_in_this_scope,
                    value_to_propagate,
                ),
            )

            if (
                current_scope_stack.get_scope_by_index(i)
                .create_output_dict()[varname]
                .defined_in_this_scope
                == True
            ):
                break
