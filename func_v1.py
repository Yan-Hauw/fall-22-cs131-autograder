from intbase import InterpreterBase
from type_class import Type

# FuncInfo is a class that represents information about a function
# Right now, the only thing this tracks is the line number of the first executable instruction
# of the function (i.e., the line after the function prototype: func foo)
class FuncInfo:
  def __init__(self, start_ip, parameters, return_type):
    self.start_ip = start_ip    # line number, zero-based
    self.return_type = return_type
    self.parameters = parameters

# FunctionManager keeps track of every function in the program, mapping the function name
# to a FuncInfo object (which has the starting line number/instruction pointer) of that function.
class FunctionManager:
  def __init__(self, tokenized_program):
    self.func_cache = {}
    self._cache_function_line_numbers(tokenized_program)

  def get_function_info(self, func_name):
    if func_name not in self.func_cache:
      return None
    return self.func_cache[func_name]

  def _cache_function_line_numbers(self, tokenized_program):
    for line_num, line in enumerate(tokenized_program):
      if line and line[0] == InterpreterBase.FUNC_DEF:
        func_name = line[1]
        arguments = []
        if len(line) > 3:
          for arg in line[2:-1]:
            var_name, var_type = arg.split(":")
            match var_type:
              case InterpreterBase.INT_DEF:
                var_type = Type.INT
              case InterpreterBase.BOOL_DEF:
                var_type = Type.BOOL
              case InterpreterBase.STRING_DEF:
                var_type = Type.STRING
              case InterpreterBase.REFINT_DEF:
                var_type = Type.REFINT
              case InterpreterBase.REFBOOL_DEF:
                var_type = Type.REFBOOL
              case InterpreterBase.REFSTRING_DEF:
                var_type = Type.REFSTRING
            arguments.append((var_name, var_type))
        match line[-1]:
          case InterpreterBase.VOID_DEF:
            return_type = Type.NONE
          case InterpreterBase.INT_DEF:
            return_type = Type.INT
          case InterpreterBase.BOOL_DEF:
            return_type = Type.BOOL
          case InterpreterBase.STRING_DEF:
            return_type = Type.STRING           
        func_info = FuncInfo(line_num + 1, arguments, return_type)   # function starts executing on line after funcdef
        self.func_cache[func_name] = func_info
