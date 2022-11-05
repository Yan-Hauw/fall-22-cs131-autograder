from re import *


def remove_comments(line):
    inQuotes = False

    commentStart = -1

    for i, char in enumerate(line):
        if char == '"':
            inQuotes = not inQuotes

        if not inQuotes and char == "#":
            commentStart = i
            break

    return line[:commentStart] if commentStart != -1 else line


def remove_spaces(statement):

    statement = statement.strip()

    statement = split('"', statement)

    # the first or last chars of the line may be double quotes
    if statement[0] == "":
        statement.pop(0)
    if len(statement) > 0 and statement[-1] == "":
        statement.pop()

    tokens = []

    # print(statement)

    for i, chunk in enumerate(statement):
        if i % 2 == 0:
            stripped_chunk = chunk.strip()

            if stripped_chunk != "":
                tokens_in_chunk = stripped_chunk.split(" ")
                tokens += tokens_in_chunk

            # print(tokens_in_chunk)
        else:
            tokens += ['"' + chunk + '"']

            # print(chunk)

    # print(tokens)

    return tokens
