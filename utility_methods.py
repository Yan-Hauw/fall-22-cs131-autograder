from re import *


def get_indentations(program):
    indentations = []

    default_indent = -1

    for line in program:
        if line == "" or match("^ *#", line):
            indentations.append(default_indent)
        else:
            spaces = 0

            for char in line:
                if char != " ":
                    break
                else:
                    spaces += 1

            indentations.append(spaces)

    return indentations


def func_def_location(program, func_name):

    for ind, line in enumerate(program):
        if match("^ *" + "func " + func_name, line):
            return ind + 1


str1 = '"func main"'
str2 = "func main"
str3 = "#func main"
str4 = '"#"func main'


# print(func_def_location(str2, "main"))
