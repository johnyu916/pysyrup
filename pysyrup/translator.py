from .parser import (
    BUILT_IN_FUNCTIONS, ARRAY_MAKE, ARRAY_GET, OBJECT_GET, KEYS, UPDATE, LENGTH, RANGE, JOIN, SPLIT, SQUARE_ROOT, RADIANS, TAN, COS, SIN, ABS, APPEND, INSERT, EXTEND, POP, REMOVE, INTEGER_STRING, INTEGER, NULL, BREAK, RETURN, PRINT, TO_JSON, FROM_JSON, STRING, BOOL, NUMBER, ARRAY, OBJECT, TRUE, FILE_READ, FILE_WRITE, FILE_IS_FILE, FILE_LIST_DIR, ASSERT, ARRAY_FLOAT,
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
    lines.extend(code_block_translate(function, tab, function))

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
    return expression_translate(pair.key)[0] + " : " + expression_translate(pair.value)[0]

def expression_translate(expression):
    """
    This returns a list of strings.
    """
    data = expression.data

    if isinstance(data, Constant):
        if data.arg_type == STRING:
            return ['"'+data.value+'"']
        elif data.arg_type == BOOL:
            if data.value:
                return ['True']
            else:
                return ['False']
        else:
            return [str(data.value)]
    elif isinstance(data, Null):
        return ['None']

    elif isinstance(data, Object):
        pairs = [pair_translate(pair) for pair in data.pairs]
        return [structure_make(pairs, BRACES)]

    if expression.children is None:
        children = None
    else:
        children = [expression_translate(child)[0] for child in expression.children]

    if isinstance(data, str):
        if children is None:
            return [data]
        else:
            if data in BUILT_IN_FUNCTIONS:
                if data == FILE_READ:
                    first = 'with open(' + children[0] + ') as f:'
                    second = '    ' + children[1] + ' = f.read()'
                    return [first, second]
                elif data == FILE_WRITE:
                    first = 'with open(' + children[0] + ', "w") as f:'
                    second = '    f.write(' + children[1] + ')'
                    return [first, second]
                elif data == FILE_IS_FILE:
                    return ["os.path.isfile(" + children[0] + ")"]
                elif data == FILE_LIST_DIR:
                    return ["os.listdir(" + children[0] + ")"]
                elif data == ARRAY_MAKE:
                    return [structure_make(children, BRACKETS)]
                elif data == ARRAY_GET:
                    assert len(children) == 2, 'operation {} but does not have 2 args: {}'.format(data, len(children))
                    return [children[0]+ structure_make(children[1:], BRACKETS, True)]
                elif data == OBJECT_GET:
                    assert len(children) == 2, 'operation {} but does not have 2 args: {}'.format(data, len(children))
                    return [children[0]+ structure_make(children[1:], BRACKETS)]
                elif data == KEYS:
                    assert len(children) == 1, 'operation keys should only have 1 argument but has: {}'.format(children)
                    return [children[0] + '.keys()']
                elif data == UPDATE:
                    return [children[0] + '.update(' + children[1] + ')']
                elif data == LENGTH:
                    #logging.debug("length of {}: {}".format(children[0], len(children[0])))
                    return ["len(" + children[0] + ")"]
                elif data == APPEND:
                    return [children[0] + ".append(" + children[1] + ")"]
                elif data == RANGE:
                    return ['range' + structure_make(children, make_int=True)]
                elif data == INSERT:
                    assert len(children) == 3, 'operation {} but does not have 3 args: {}'.format(data, len(children))
                    children[1] = "int(" + children[1] + ")"
                    return [children[0] + '.insert' + structure_make(children[1:])]
                elif data == POP:
                    result = children[0]+ '.pop'
                    if len(children) == 1:
                        result += '()'
                    else:
                        result += structure_make(children[1:], make_int=True)
                    return [result]
                elif data == REMOVE:
                    return [children[0]+ '.remove(' + children[1] + ')']
                elif data == EXTEND:
                    return [children[0] + '.extend(' + children[1] + ')']
                elif data == JOIN:
                    return [children[1] + '.join(' + children[0] + ')']
                elif data == SPLIT:
                    return [children[0] + '.split(' + children[1] + ')']
                elif data == SQUARE_ROOT:
                    return ['math.sqrt(' + children[0] + ')']
                elif data == RADIANS:
                    return ['math.radians(' + children[0] + ')']
                elif data == TAN:
                    return ['math.tan(' + children[0] + ')']
                elif data == COS:
                    return ['math.cos(' + children[0] + ')']
                elif data == SIN:
                    return ['math.sin(' + children[0] + ')']
                elif data == ABS:
                    return ['math.abs(' + children[0] + ')']
                elif data == PRINT:
                    return ['print json.dumps(' + children[0] + ', cls=SyrupEncoder)']
                    #return ['print json.dumps(' + children[0] + ')']
                elif data == INTEGER_STRING:
                    return ['str(int(' + children[0] + '))']
                elif data == INTEGER:
                    return ['float(int(' + children[0] + '))']
                elif data == TO_JSON:
                    return ['json.dumps(' + children[0] + ', cls=SyrupEncoder)']
                elif data == FROM_JSON:
                    return ['json.loads(' + children[0] + ')']
                elif data == ASSERT:
                    return ['assert ' + children[0] + ', ' + children[1]]
                elif data == ARRAY_FLOAT:
                    return ['numpy.array(' + children[0] + ', "f")']
                else:
                    raise Exception("Not implemented: {}".format(data))
            else:
                # function call
                return [data + structure_make(children)]

    elif isinstance(data, Operator):
        assert children is not None and len(children) == 2, 'operation {} but does not have 2 args: {}'.format(data, len(children))
        operator = data.value
        if operator == '||':
            operator = 'or'
        elif operator == '&&':
            operator = 'and'
        return ['(' + children[0] + ' ' + operator + ' ' + children[1] + ')']
    else:
        raise Exception("Unrecognized expression: {}".format(expression))

def assignment_translate(assignment):
    expression = expression_translate(assignment.expression)[0]
    texts = []
    for destination in assignment.destinations:
        texts.append(expression_translate(destination)[0])

    return [", ".join(texts) + ' ' + assignment.setter.value + ' ' + expression]

def while_translate(loop, tab, function):
    text = ['while ' + expression_translate(loop.condition)[0] + ':']
    text.extend(code_block_translate(loop, tab + '    ', function))
    return text

def for_translate(loop, tab, function):
    text = ['for ' + loop.index + ' in ' + expression_translate(loop.condition)[0] + ':']
    text.extend(code_block_translate(loop, tab + '    ', function))
    return text

def if_translate(condition, tab, function):
    text = ['if ' + expression_translate(condition.condition)[0] + ':']
    text.extend(code_block_translate(condition, tab + '    ', function))
    return text


def elif_translate(condition, tab, function):
    text = ['elif ' + expression_translate(condition.condition)[0] + ':']
    text.extend(code_block_translate(condition, tab + '    ', function))
    return text

def else_translate(condition, tab, function):
    text = ['else:']
    text.extend(code_block_translate(condition, tab + '    ', function))
    return text

# tab is a string of some number of spaces.
# returns lines
def code_block_translate(code_block, tab, function):
    all_lines = []
    for chunk in code_block.code:
        logging.debug("Running chunk: {}".format(chunk))
        if isinstance(chunk, Expression):
            lines = expression_translate(chunk)
        elif isinstance(chunk, Assignment):
            lines = assignment_translate(chunk)
        elif isinstance(chunk, While):
            lines = while_translate(chunk, tab, function)
        elif isinstance(chunk, For):
            lines = for_translate(chunk, tab, function)
        elif isinstance(chunk, If):
            lines = if_translate(chunk, tab, function)
        elif isinstance(chunk, Elif):
            lines = elif_translate(chunk, tab, function)
        elif isinstance(chunk, Else):
            lines = else_translate(chunk, tab, function)
        elif isinstance(chunk, FlowControl):
            line = chunk.value
            if chunk.value == RETURN:
                output_names = [output.name for output in function.outputs]
                line += ' ' + ', '.join(output_names)
            lines = [line]
        else:
            raise Exception("Don't know what to do with: ", chunk)
        for line in lines:
            all_lines.append(tab + line)
    return all_lines

class Translator(object):
    def __init__(self, output_path, parser):
        with open(output_path, 'w') as f:
            try:
                f.write('import json\n')
                f.write('from plugins.jsonsyrup import SyrupEncoder\n')
                f.write('import math\n')
                f.write('import os.path\n')
                f.write('from random import random\n')
                f.write('from time import time\n')
                f.write('import numpy\n\n')
                for import_line in parser.imports:
                    text = import_translate(import_line)
                    f.write(text + '\n')
                f.write('\n')
                for function in parser.functions:
                    try:
                        text = function_translate(function)
                        f.write(text + '\n\n')
                    except Exception as e:
                        raise Exception("Function translate error for {}: {}".format(function.name, e))
            except Exception as e:
                raise Exception("File translate error at {}: {}".format(output_path, e))
