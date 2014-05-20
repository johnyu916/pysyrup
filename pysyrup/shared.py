def get_program_dict(program):
    functions = []
    for function in program.functions:
        functions.append(function.get_dict())

    return {
        'functions': functions
    }
