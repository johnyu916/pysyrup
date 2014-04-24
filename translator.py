from .parser import (
    OPERATORS, BUILT_IN_FUNCTIONS, ARRAY_MAKE, ARRAY_GET, OBJECT_GET, KEYS, LENGTH, RANGE, SQUARE_ROOT, RADIANS, TAN, COS, SIN, APPEND, INSERT, EXTEND, POP, NULL, BREAK, RETURN, PRINT, STRING, BOOL, NUMBER, ARRAY, OBJECT, TRUE,
    PARENS, BRACKETS, BRACES,
    Object, While, For, If, Else, Elif, FlowControl, Expression, Assignment, Constant, Null, Name, Operator
)
import logging

def default_assignment(variable):
    type = variable.arg_type
    if type == STRING:
        return variable.name + ' = ""'
    elif type == BOOL:
        return variable.name + ' = False'
    elif type == NUMBER:
        return variable.name + ' = 0.0'
    elif type == ARRAY:
        return variable.name + ' = []'
    elif type == OBJECT:
        return variable.name + ' = {}'
    else:
        raise Exception("Unknown type: {}".format(type))

def import_translate(import_line):
    return "from " + ".".join(import_line.path) + " import " + ", ".join(import_line.functions)

def function_translate(function):
    tab = '    '
    lines = []
    first = 'def ' + function.name + '('
    input_names = []
    for input in function.inputs:
        input_names.append(input.name)

    first += ', '.join(input_names)
    first += '):'
    lines.append(first)

    setters = []
    for output in function.outputs:
        setters.append(tab + default_assignment(output))
    lines.extend(setters)
    lines.append(code_block_translate(function, tab, function))

    output_names = [output.name for output in function.outputs]
    lines.append(tab + 'return ' + ", ".join(output_names))

    return "\n".join(lines)

def structure_make(elements, grouper=PARENS, make_int=False):
    if grouper == BRACKETS:
        closers = ['[', ']']
    elif grouper == BRACES:
        closers = ['{', '}']
    else:
        closers = ['(', ')']
    value = [closers[0]]
    texts = []
    for text in elements:
        if make_int:
            try:
                text = str(int(float(text)))
            except:
                text = 'int(' + text + ')'
        texts.append(text)
    value.append(", ".join(texts))
    value.append(closers[1])
    return "".join(value)

def pair_translate(pair):
    return expression_translate(pair.key) + " : " + expression_translate(pair.value)

def expression_translate(expression):
    """
    This returns a string
    """
    data = expression.data

    if isinstance(data, Constant):
        if data.arg_type == STRING:
            return '"'+data.value+'"'
        elif data.arg_type == BOOL:
            if data.value:
                return 'True'
            else:
                return 'False'
        else:
            return str(data.value)
    elif isinstance(data, Null):
        return 'None'

    elif isinstance(data, Object):
        pairs = [pair_translate(pair) for pair in data.pairs]
        return structure_make(pairs, BRACES)

    if expression.children is None:
        children = None
    else:
        children = [expression_translate(child) for child in expression.children]

    if isinstance(data, str):
        if children is None:
            return data
        else:
            if data in BUILT_IN_FUNCTIONS:
                if data == ARRAY_MAKE:
                    return structure_make(children, BRACKETS)
                elif data == ARRAY_GET:
                    assert len(children) == 2, 'operation {} but does not have 2 args: {}'.format(data, len(children))
                    return children[0]+ structure_make(children[1:], BRACKETS, True)
                elif data == OBJECT_GET:
                    assert len(children) == 2, 'operation {} but does not have 2 args: {}'.format(data, len(children))
                    return children[0]+ structure_make(children[1:], BRACKETS)
                elif data == KEYS:
                    assert len(children) == 1, 'operation keys should only have 1 argument but has: {}'.format(children)
                    return children[0] + '.keys()'
                elif data == LENGTH:
                    #logging.debug("length of {}: {}".format(children[0], len(children[0])))
                    return "len(" + children[0] + ")"
                elif data == APPEND:
                    return children[0] + ".append(" + children[1] + ")"
                elif data == RANGE:
                    return 'range' + structure_make(children, make_int=True)
                elif data == INSERT:
                    assert len(children) == 3, 'operation {} but does not have 3 args: {}'.format(data, len(children))
                    children[1] = "int(" + children[1] + ")"
                    return children[0] + '.insert' + structure_make(children[1:])
                elif data == POP:
                    return children[0]+ '.pop' + structure_make(children[1:], make_int=True)
                elif data == EXTEND:
                    return children[0] + '.extend(' + children[1] + ')'
                elif data == SQUARE_ROOT:
                    return 'math.sqrt(' + children[0] + ')'
                elif data == RADIANS:
                    return 'math.radians(' + children[0] + ')'
                elif data == TAN:
                    return 'math.tan(' + children[0] + ')'
                elif data == COS:
                    return 'math.cos(' + children[0] + ')'
                elif data == SIN:
                    return 'math.sin(' + children[0] + ')'
                elif data == PRINT:
                    return 'print ' + children[0]
                else:
                    raise Exception("Not implemented: {}".format(data))
            else:
                # function call
                return data + structure_make(children)

    elif isinstance(data, Operator):
        assert children is not None and len(children) == 2, 'operation {} but does not have 2 args: {}'.format(data, len(children))
        operator = data.value
        if operator == '||':
            operator = 'or'
        elif operator == '&&':
            operator = 'and'
        return '(' + children[0] + ' ' + operator + ' ' + children[1] + ')'
    else:
        raise Exception("Unrecognized expression: {}".format(expression))

def assignment_translate(assignment):
    expression = expression_translate(assignment.expression)
    texts = []
    for destination in assignment.destinations:
        texts.append(expression_translate(destination))

    return ", ".join(texts) + ' ' + assignment.setter.value + ' ' + expression

def while_translate(loop, tab, function):
    text = 'while ' + expression_translate(loop.condition) + ':'
    return text + '\n' + code_block_translate(loop, tab + '    ', function)

def for_translate(loop, tab, function):
    text = 'for ' + loop.index + ' in ' + expression_translate(loop.condition) + ':'
    return text + '\n' + code_block_translate(loop, tab + '    ', function)

def if_translate(condition, tab, function):
    text = 'if ' + expression_translate(condition.condition)+ ':'
    return text + '\n' + code_block_translate(condition, tab + '    ', function)

def elif_translate(condition, tab, function):
    text = 'elif ' + expression_translate(condition.condition)+ ':'
    return text + '\n' +  code_block_translate(condition, tab + '    ', function)

def else_translate(condition, tab, function):
    text = 'else:'
    return text + '\n' + code_block_translate(condition, tab + '    ', function)

def code_block_translate(code_block, tab, function):
    lines = []
    for chunk in code_block.code:
        logging.debug("Running chunk: {}".format(chunk))
        if isinstance(chunk, Expression):
            line = expression_translate(chunk)
        elif isinstance(chunk, Assignment):
            line = assignment_translate(chunk)
        elif isinstance(chunk, While):
            line = while_translate(chunk, tab, function)
        elif isinstance(chunk, For):
            line = for_translate(chunk, tab, function)
        elif isinstance(chunk, If):
            line = if_translate(chunk, tab, function)
        elif isinstance(chunk, Elif):
            line = elif_translate(chunk, tab, function)
        elif isinstance(chunk, Else):
            line = else_translate(chunk, tab, function)
        elif isinstance(chunk, FlowControl):
            line = chunk.value
            if chunk.value == RETURN:
                output_names = [output.name for output in function.outputs]
                line += ' ' + ', '.join(output_names)
        else:
            raise Exception("Don't know what to do with: ", chunk)
        lines.append(tab + line)
    return "\n".join(lines)

class Translator(object):
    def __init__(self, output_path, parser):
        with open(output_path, 'w') as f:
            f.write('import math\n\n')
            for import_line in parser.imports:
                text = import_translate(import_line)
                f.write(text + '\n')
            f.write('\n')
            for function in parser.functions:
                text = function_translate(function)
                f.write(text + '\n\n')
