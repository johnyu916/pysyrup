import json
import logging
import copy
import re
import string
from StringIO import StringIO
USHORT_SIZE = 16

NUMBER = 'number'
ARRAY = 'array'
OBJECT = 'object'
BOOL = 'bool'
STRING = 'string'

TYPES = [
    NUMBER,
    ARRAY,
    OBJECT,
    BOOL,
    STRING
]
CONDITIONAL_WORDS = ['if', 'elif', 'else', 'while', 'for']
TRUE = 'true'
FALSE = 'false'
BOOLEANS = ['true', 'false']
NULL = 'null'
OPERATORS = ['==', '&&', '||', '!=', '+', '-', '*', '/','>=', '<=', '>', '<', '%']
SETTERS = ['=', '+=', '-=', '*=', '/=']
SYMBOLS_PATTERN = '=|!|>|<|\+|-|\*|/|&|\||%'
#SETTER_PATTERN = '=|\+=|-='
RESERVED_WORDS = copy.copy(TYPES)
RESERVED_WORDS.extend(CONDITIONAL_WORDS)
VARIABLE_PATTERN = '[a-zA-Z][a-zA-Z0-9_]*'
#STRING_PATTERN = '\"[a-zA-Z0-9_]+\"'
STRING_PATTERN ='\"(?P<word>[a-zA-Z0-9_ .,/:]*)\"'

BUILT_IN_FUNCTIONS = set()

# file functions
FILE_READ = 'file_read'
FILE_WRITE = 'file_write'
FILE_IS_FILE = 'file_is_file'
BUILT_IN_FUNCTIONS.update([FILE_READ, FILE_WRITE, FILE_IS_FILE])

# object methods
KEYS = 'keys'
OBJECT_GET = '__object_get__'
UPDATE = 'update'

BUILT_IN_FUNCTIONS.update([KEYS, UPDATE, OBJECT_GET])

# array methods
ARRAY_MAKE = '__array_make__'
ARRAY_GET = '__array_get__'
LENGTH = 'length'
APPEND = 'append'
INSERT = 'insert'
EXTEND = 'extend'
RANGE = 'range'
POP = 'pop'
REMOVE = 'remove'
BUILT_IN_FUNCTIONS.update( [ARRAY_MAKE, ARRAY_GET, LENGTH, RANGE, POP, REMOVE, APPEND, INSERT, EXTEND] )

# string methods
JOIN = 'join'
BUILT_IN_FUNCTIONS.update( [JOIN] )

# math functions
SQUARE_ROOT = 'square_root'
RADIANS = 'radians'
TAN = 'tan'
COS = 'cos'
SIN = 'sin'

BUILT_IN_FUNCTIONS.update([SQUARE_ROOT, RADIANS, TAN, COS, SIN])

# etc
TIME = 'time'
PRINT = 'print'
INTEGER_STRING = 'integer_string'
TO_JSON = 'to_json'
FROM_JSON = 'from_json'
ASSERT = 'assert'
BUILT_IN_FUNCTIONS.update( [PRINT, INTEGER_STRING, TO_JSON, FROM_JSON, ASSERT])

# control statements
CONTINUE = 'continue'
BREAK = 'break'
RETURN = 'return'


PARENS = 'parens'
BRACKETS = 'brackets'
BRACES = 'braces'
class Token(object):
    KINDS = ['left_par', 'right_par', 'operator', 'constant', 'name']
    def __init__(self, value):
        """
        Value is a string?
        """
        self.value = value

    def __str__(self):
        return str(self.value)

    def get_dict(self):
        return {
            'value': str(self)
        }

class Ignore(Token):
    pass

class Pound(Token):
    def __init__(self):
        super(Pound, self).__init__('#')

class LeftBrace(Token):
    def __init__(self):
        super(LeftBrace, self).__init__('{')

class LeftParen(Token):
    def __init__(self):
        super(LeftParen, self).__init__('(')

class LeftBracket(Token):
    def __init__(self):
        super(LeftBracket, self).__init__('[')

class RightParen(Token):
    def __init__(self):
        super(RightParen, self).__init__(')')

class RightBracket(Token):
    def __init__(self):
        super(RightBracket, self).__init__(']')

class RightBrace(Token):
    def __init__(self):
        super(RightBrace, self).__init__('}')

GROUP_CLASSES = ((LeftParen, RightParen), (LeftBracket, RightBracket), (LeftBrace, RightBrace))


class Comma(Token):
    def __init__(self):
        super(Comma, self).__init__(',')

class Period(Token):
    def __init__(self):
        super(Period, self).__init__('.')

class Colon(Token):
    def __init__(self):
        super(Colon, self).__init__(':')

class Setter(Token):
    pass

class Operator(Token):
    pass

class Symbol(Token):
    pass

class Constant(object):
    def __init__(self, arg_type, value):
        self.value = value # value (str, int, float, etc)
        self.arg_type = arg_type # string

    def __str__(self):
        return json.dumps(self.get_dict())

    def get_dict(self):
        return {
            'arg_type': self.arg_type,
            'value': self.value
        }

class FlowControl(Token):
    pass

class Null(Token):
    pass

class Name(Token):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Object(object):
    def __init__(self, pairs):
        """
        pairs is a list of Pair objects
        """
        self.pairs = pairs

    def get_dict(self):
        return {
            "pairs": [pair.get_dict() for pair in self.pairs]
        }

class ParenGroup(object):
    def __init__(self, values):
        self.values = values

    def __str__(self):
        tokens = []
        for value in self.values:
            tokens.append(str(value))
        return json.dumps(tokens)

class BracketGroup(object):
    def __init__(self, values):
        self.values = values

class BraceGroup(object):
    def __init__(self, values):
        self.values = values

class Destination():
    def __init__(self, name, index):
        """
        name is a Name
        Index can be Name or Integer
        """
        self.name = name
        self.index = index

def get_group_direction(grouper):
    for classes in GROUP_CLASSES:
        if isinstance(grouper, classes[0]):
            return 0
        elif isinstance(grouper, classes[0]):
            return 1
    return None


def get_group_type_old(grouper):
    if isinstance(grouper, LeftParen) or isinstance(grouper, RightParen):
        return PARENS
    if isinstance(grouper, LeftBracket) or isinstance(grouper, RightBracket):
        return BRACKETS
    if isinstance(grouper, LeftBrace) or isinstance(grouper, RightBrace):
        return BRACES
    return None

def is_same_group(left, right):
    for classes in GROUP_CLASSES:
        if isinstance(left, classes[0]) and isinstance(right, classes[1]):
            return True
    return False

class Variable(object):
    '''
    Variable has type and name.
    Type is a primitive, str.
    name is a string.
    '''
    def __init__(self, type, name):
        if not type in TYPES:
            raise Exception("Invalid type: {}".format(type))
        self.arg_type = type
        self.name = name

    def __str__(self):
        return json.dumps(self.get_dict())

    def get_dict(self):
        return {
            'arg_type': self.arg_type,
            'name': self.name
        }


class Block(object):
    def __init__(self):
        self.code = []  # code is expressions and blocks

    def get_dict(self):
        codes = []
        for line in self.code:
            codes.append(line.get_dict())
        return {
            'code': codes
        }


class Import(object):
    def __init__(self, path, functions):
        """
        path is a list of strings
        functions is a list of strings
        """
        self.path = path
        self.functions = functions

    def __str__(self):
        print "import get_dict: ", self.get_dict()
        return json.dumps(self.get_dict())

    def get_dict(self):
        return { 'path': self.path, 'functions': self.functions}

class Function(Block):
    def __init__(self, name, inputs=[], outputs=[]):
        '''
        name is the function name (string).
        inputs is a list of variables. ditto outputs.
        '''
        self.name = name
        self.inputs = inputs
        self.outputs = outputs
        super(Function, self).__init__()

    def get_dict(self):
        inputs = []
        for inpu in self.inputs:
            inputs.append(inpu.get_dict())

        outputs = []
        for output in self.outputs:
            outputs.append(output.get_dict())

        block_dict = super(Function, self).get_dict()

        this_dict = {
            'name': self.name,
            'inputs': inputs,
            'outputs': outputs
        }
        this_dict.update(block_dict)
        return this_dict

    def __str__(self):
        return json.dumps(self.get_dict())


class Conditional(Block):
    def __init__(self, condition=None):
        self.condition = condition
        super(Conditional, self).__init__()

    def get_dict(self):
        this_dict = {}
        if self.condition is not None:
            this_dict['condition'] = self.condition.get_dict()
        codes = super(Conditional, self).get_dict()
        this_dict.update(codes)
        return this_dict


class While(Conditional):
    pass

class For(Conditional):
    def __init__(self, index, condition):
        """
        index is Name
        """
        self.index = index
        super(For, self).__init__(condition)

    def get_dict(self):
        this_dict = super(For, self).get_dict()
        this_dict['index'] = self.index
        return this_dict


class If(Conditional):
    pass

class Elif(Conditional):
    pass

class Else(Conditional):
    pass


class Assignment(object):
    def __init__(self, destinations, setter, expression):
        '''
        a = add(3,5)
        destinations is a list of expressions.
        expression is Expression
        setter is a Setter object.
        '''
        self.destinations = destinations  # destinations is a list
        self.setter = setter
        self.expression = expression

    def get_dict(self):
        dest_list = []
        for dest in self.destinations:
            dest_list.append(dest.get_dict())
        return {
            'destinations': dest_list,
            'setter': self.setter.get_dict(),
            'expression': self.expression.get_dict()
        }

    def __str__(self):
        return json.dumps(self.get_dict())

class Pair(object):
    '''
    Key and value are both expressions.
    '''
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __str__(self):
        return json.dumps(self.get_dict())

    def get_dict(self):
        return {
            'key': self.key.get_dict(),
            'value': self.value.get_dict()
        }

class Expression(object):
    '''
    Expression is a node that carries data.
    children can be Expressions or empty.
    data can be a Token (Operator, Constant) or string (name of variable) or Object (dictionary)
    if children is None, then there are no children (i.e variable)
    an empty list of children is a function call with no parameters.
    '''
    def __init__(self, data, children=None):
        if children is not None:
            assert isinstance(children, list) or isinstance(children, tuple)

        #self.data = 'add'  # data is either function names or variables
        self.data = data
        self.children = children

    def __str__(self):
        return json.dumps(self.get_dict())

    def get_dict(self):
        children = []
        if self.children is not None:
            for child in self.children:
                children.append(child.get_dict())
        else:
            children = None

        if type(self.data) == str:
            data = self.data
        else:
            data = self.data.get_dict()

        return {
            'data': data,
            'children':children
        }

def get_num_front_spaces(line):
    line2 = line.rstrip()
    line3 = line.strip()
    return len(line2) - len(line3)

def get_stack_index(line):
    '''
    return 0 if 0, 1 if 4, 2 if 8, etc.
    '''
    num = get_num_front_spaces(line)
    if not (num % 4) == 0:
        raise Exception("Wrong number of spaces: {}".format(num))
    return num/4

def read_flow_control(tokens):
    """
    read break and continue
    """
    stack = copy.copy(tokens)
    token = list_pop(stack)
    if isinstance(token, Name):
        name = str(token)
        if name == BREAK:
            return FlowControl(BREAK), stack
        elif name == CONTINUE:
            return FlowControl(CONTINUE), stack
        elif name == RETURN:
            return FlowControl(RETURN), stack
        else:
            return None, tokens
    else:
        return None, tokens

def read_if(orig):
    '''
    Read line of text. If the assignment is read, then return
    assignment and the next line that should be read.
    '''
    stack = copy.copy(orig)
    name = list_pop(stack)
    if not isinstance(name, Name) or str(name) != 'if':
        return None, orig

    # read expression
    expr, stack = build_expression(stack)
    if expr is None:
        return None, orig

    colon = list_pop(stack)
    if not isinstance(colon, Colon):
        return None, orig

    return If(expr), stack


def read_elif(orig):
    '''
    Return clause and next line index
    '''
    stack = copy.copy(orig)
    name = list_pop(stack)
    if not isinstance(name, Name) or str(name) != 'elif':
        return None, orig

    # read expression
    expr, stack = build_expression(stack)
    if expr is None:
        return None, orig

    colon = list_pop(stack)
    if not isinstance(colon, Colon):
        return None, orig

    return Elif(expr), stack


def read_else(orig):
    stack = copy.copy(orig)
    name = list_pop(stack)
    if not isinstance(name, Name) or str(name) != 'else':
        return None, orig

    colon = list_pop(stack)
    if not isinstance(colon, Colon):
        return None, orig

    return Else(), stack


def read_while(orig):
    stack = copy.copy(orig)
    # if, elif ,else, while
    #print "while text matching against: " + text
    whil = list_pop(stack)
    if not isinstance(whil, Name) or str(whil) != 'while':
        return None, orig

    # read expression
    expr, stack = build_expression(stack)
    if expr is None:
        return None, orig

    colon = list_pop(stack)
    if not isinstance(colon, Colon):
        return None, orig
    return While(expr), stack

def read_for(orig):
    stack = copy.copy(orig)
    for_str = list_pop(stack)
    if not isinstance(for_str, Name) or str(for_str) != 'for':
        return None, orig

    index = list_pop(stack)
    if not isinstance(index, Name):
        return None, orig

    in_str = list_pop(stack)
    if not isinstance(in_str, Name) or str(in_str) != 'in':
        return None, orig

    expr, stack = build_expression(stack)
    if expr is None:
        return None, orig

    colon = list_pop(stack)
    if not isinstance(colon, Colon):
        return None, orig

    return For(str(index), expr), stack


def has_grouper(orig):
    """
    Return True if there are unmatched groupers.
    """
    tokens = copy.copy(orig)
    stack = []
    # see if things have been properly closed or not.
    for element in tokens:
        direction = get_group_direction(element)
        if direction is not None:
            if direction == 0:
                stack.append(element)
            else:
                back = stack.pop()
                if not is_same_group(back, element):
                    raise Exception("Error encountered with grouping")

    return len(stack) > 0

class EOFException(Exception):
    pass

# tokens is None if end of file.
def read_tokens(descriptor):
    text = descriptor.readline()
    if len(text) == 0: # end of file
        raise EOFException()
    tokens = []
    texts = [text]
    stack_index = get_stack_index(text)
    text = text.strip()
    while True:
        try:
            read_tokens_from_text(text, tokens)
        except Exception as e:
            raise Exception("Error during text: {}\n{}".format(text, e))
        #print "read_expression stack: ", stack
        if has_grouper(tokens):
            text = descriptor.readline()
            if len(text) == 0:
                raise Exception("End of file reached wih unclosed statemnt")
            texts.append(text)
            text = text.rstrip()
        else:
            break
    return tokens, stack_index, texts

def print_tokens(tokens):
    strings = [str(token) for token in tokens]
    print "print tokens: ", ", ".join(strings)

def read_expression_lines(lines):
    """
    Lines is a list of strings
    """
    tokens, stack_index, texts = read_tokens(StringIO(string.join(lines)))
    print_tokens(tokens)
    return build_expression(tokens)

def read_expression_line(text):
    tokens = []
    read_tokens_from_text(text, tokens)
    print "read tokens: {}".format(tokens)
    return build_expression(tokens)

def read_import_line(text):
    tokens = []
    read_tokens_from_text(text, tokens)
    print "read tokens: {}".format(tokens)
    return read_import(tokens)


def read_assignment_line(text):
    tokens = []
    read_tokens_from_text(text, tokens)
    print "read tokens: {}".format(tokens)
    return read_assignment(tokens)


def read_tokens_from_text(text, stack):
    '''
    Read text and fill up the stack. As closing groupers are
    encountered, reduce the stack.
    '''
    while len(text) > 0:
        space, text = re_match(' *', text)
        # don't  really care whether a space was read or not

        par, text = re_match('\(', text)
        if par is not None:
            stack.append(LeftParen())
            continue

        number, text = re_match('-?[0-9]+(\.[0-9]+)?', text)
        if number is not None:
            stack.append(Constant(NUMBER, float(number)))
            continue

        string, text = re_match(STRING_PATTERN, text, 1)
        if string is not None:
            # NOTE: assuming int for now. add more later.
            stack.append(Constant(STRING, string))
            continue

        variable, text = read_name(text)
        if variable is not None:
            stack.append(variable)
            continue

        period, text = re_match('\.', text)
        if period is not None:
            stack.append(Period())
            continue

        comma, text = re_match(',', text)
        if comma is not None:
            stack.append(Comma())
            continue

        operator, text = re_match(SYMBOLS_PATTERN, text)
        if operator is not None:
            stack.append(Symbol(operator))
            continue

        left_brace, text = re_match('{', text)
        if left_brace is not None:
            stack.append(LeftBrace())
            continue

        left_brack, text = re_match('\[', text)
        if left_brack is not None:
            stack.append(LeftBracket())
            continue

        right_brace, text = re_match('}', text)
        if right_brace is not None:
            # time to pop off some stuff
            stack.append(RightBrace())
            stuff = read_enclosed(stack)
            # can return list
            if stuff is not None:
                stack.append(stuff)
                continue
            else:
                raise Exception("Failed to make dict or index it")

        right_brack, text = re_match(']', text)
        if right_brack is not None:
            # time to pop off some stuff
            stack.append(RightBracket())
            stuff = read_enclosed(stack)
            if stuff is not None:
                stack.append(stuff)
                continue
            else:
                raise Exception("Failed to make list or index it")

        par, text = re_match('\)', text)
        if par is not None:
            # time to pop some stuff out
            stack.append(RightParen())
            text_node = read_enclosed(stack)
            if text_node is not None:
                stack.append(text_node)
            # we just ignore empty expressions ()
            continue

        colon, text = re_match(':', text)
        if colon is not None:
            stack.append(Colon())
            continue

        pound, text = re_match('#', text)
        if pound is not None:
            stack.append(Pound())
            continue

        char = text[0]
        stack.append(Ignore(char))
        text = text[1:]

        #raise Exception("Unknown character encountered: {}".format(text))


def read_enclosed(stack):
    close = stack.pop()
    if isinstance(close, RightParen):
        close_type = LeftParen
    elif isinstance(close, RightBracket):
        close_type = LeftBracket
    elif isinstance(close, RightBrace):
        close_type = LeftBrace
    else:
        raise Exception("Top of stack needs to be a right closing type but it isn't: {}".format(close))
    tokens = []
    terms = []
    is_left_hit = False
    while len(stack) > 0:
        token = stack.pop()
        #print "popped token: ", token
        if isinstance(token, close_type):
            is_left_hit = True
            if len(terms) > 0:
                tokens.insert(0, terms)
            break
        elif isinstance(token, Comma):
            if len(terms) > 0:
                tokens.insert(0, terms)
            else:
                raise Exception("Must have tokens before comma")
            terms = []
        else:
            terms.insert(0, token)

    if not is_left_hit:
        logging.debug("read_enclosed stack: {0}".format(stack))
        raise Exception("Should have hit left parenthesis.")

    if isinstance(close, RightParen):
        return ParenGroup(tokens)
    elif isinstance(close, RightBracket):
        return BracketGroup(tokens)
    else:
        return BraceGroup(tokens)


def build_expression(orig):
    stack = copy.copy(orig)
    """
    Returns tokenList
    """
    expression, tokens = build_operation(stack)
    if expression is not None:
        return expression, tokens

    expression, tokens = build_function_call(stack)
    if expression is not None:
        return expression, tokens

    expression, tokens = build_nest(stack)
    if expression is not None:
        return expression, tokens

    expression, left_tokens = build_array_make(stack)
    if expression is not None:
        return expression, left_tokens

    expression, left_tokens = build_dict_make(stack)
    if expression is not None:
        return expression, left_tokens

    expression, left_tokens = build_constant_or_variable(stack)
    if expression is not None:
        return expression, left_tokens

    return None, orig

def build_pair(orig):
    '''
    a pair is expression:expression
    '''
    stack = copy.copy(orig)
    key, stack = build_expression(stack)
    if key is None:
        return None, orig

    colon = list_pop(stack)
    if not isinstance(colon, Colon):
        return None, orig

    value, stack = build_expression(stack)
    if value is None:
        return None, orig

    return Pair(key, value), stack


def list_pop(objects, index=0):
    if len(objects) == 0:
        return None
    return objects.pop(index)


def build_non_operation(orig):
    tokens = copy.copy(orig)
    expression, tokens = build_function_call(tokens)
    if expression is not None:
        return expression, tokens

    expression, tokens = build_nest(tokens)
    if expression is not None:
        return expression, tokens

    expression, left_tokens = build_array_make(tokens)
    if expression is not None:
        return expression, left_tokens

    expression, left_tokens = build_dict_make(tokens)
    if expression is not None:
        return expression, left_tokens

    expression, tokens = build_constant_or_variable(tokens)
    if expression is not None:
        return expression, tokens

    return None, tokens

def matched_operator(chars, cls):
    """
    """
    if cls == Operator:
        matches = OPERATORS
    else:
        matches = SETTERS
    for operator in matches:
        if operator == chars:
            return True
    return False


def read_symbols(orig, cls):
    tokens = copy.copy(orig)

    chars = ''
    while True:
        if len(tokens) > 0 and isinstance(tokens[0], Symbol):
            symbol = tokens.pop(0)
            chars += symbol.value
        else:
            break

    if not matched_operator(chars, cls):
        return None, orig
    return cls(chars), tokens


def build_operation(orig):
    '''
    Try to read operation (i.e 3+5). If read successful,
    return ones that are left.
    '''
    tokens = copy.copy(orig)
    op_terms = []
    #print "build_operation 1"
    left_expression, tokens = build_non_operation(tokens)
    if left_expression is None:
        return None, orig
    op_terms.append(left_expression)
    #print "build_operation 2"
    while True:
        if len(tokens) < 2:
            break

        #print "build_operation 3"
        operator, tokens = read_symbols(tokens, Operator)
        if not isinstance(operator, Operator):
            break

        #print "build_operation 4"
        right_expression, tokens = build_non_operation(tokens)
        if right_expression is None:
            return None, orig

        op_terms.extend([operator, right_expression])

    if len(op_terms) == 1:
        return None, orig

    #print "build_operation 5"
    # now make expressions out of them.
    expression = order_operations(op_terms)

    return expression, tokens

def order_operations(terms):
    '''
    Output is a single expression.
    Do multiple iterations of tokens in this order:
    1.mutiplications and divisions.
    2.addition/subtractions.
    3.comparisons.
    4. logical operators.
    '''
    #print "order terms: ", terms
    operator_sets =[['*', '/'],['+','-'], ['>','>=','<','<=','==','!=']]
    for operator_set in operator_sets:
        left = terms.pop(0)
        checkpoint = [left]
        while len(terms) > 1:
            operator = terms.pop(0)
            right = terms.pop(0)
            if operator.value in operator_set:
                left = checkpoint.pop()
                expression = Expression(operator, [left,right])
                checkpoint.append(expression)
            else:
                checkpoint.append(operator)
                checkpoint.append(right)
        terms = checkpoint

    #print "order checkpoint array: ", checkpoint

    # last pass for the remaining operators.
    if len(terms) == 1:
        return terms[0]
    left = terms.pop(0)
    while len(terms) > 1:
        operator = terms.pop(0)
        right = terms.pop(0)
        left = Expression(operator, [left,right])

    return left


def build_array_make(orig):
    tokens = copy.copy(orig)
    group = list_pop(tokens, 0)
    if not isinstance(group, BracketGroup):
        return None, orig

    children = []
    for term in group.values:
        # term is a list of tokens
        expression, left = build_expression(term)
        if expression is None:
            return None, orig
        children.append(expression)

    expression = Expression(ARRAY_MAKE, children)
    return build_get_indices(tokens, expression)


def build_nest(orig):
    tokens = copy.copy(orig)
    group = list_pop(tokens, 0)
    if not isinstance(group, ParenGroup):
        return None, orig

    if len(group.values) != 1:
        return None, orig

    expression, child_tokens = build_expression(group.values[0])

    print "build_next print tokens ", tokens
    # read 0 or more get_index
    return build_get_indices(tokens, expression)


def build_dict_make(orig):
    tokens = copy.copy(orig)
    group = list_pop(tokens, 0)
    if not isinstance(group, BraceGroup):
        return None, orig

    pairs = []
    for term in group.values:
        # term is a list of tokens
        pair, left = build_pair(term)
        if pair is None:
            return None, orig
        if len(left) > 0: # term has leftover tokens.
            return None, orig
        pairs.append(pair)

    expression = Expression(Object(pairs))
    # read 0 or more get_index
    return build_get_indices(tokens, expression)


def build_function_call(orig):
    tokens = copy.copy(orig)
    name = list_pop(tokens, 0)
    if not isinstance(name, Name):
        return None, orig
    group = list_pop(tokens, 0)
    if not isinstance(group, ParenGroup):
        return None, orig

    children = []
    for term in group.values:
        print "function call term: ", term
        child, left = build_expression(term)
        if child is None:
            return None, orig
        children.append(child)

    expression = Expression(str(name), children)

    # read 0 or more get_index
    return build_get_indices(tokens, expression)


def build_get_indices(orig, expression):
    """
    Expression already exists. this will do a 'get' operation at some key/index.
    """
    tokens = copy.copy(orig)
    while True:
        # try reading [0] or {"hi"}
        child, tokens, group_cls = build_get_index(tokens)
        if child is not None:
            if group_cls == BracketGroup:
                action = ARRAY_GET
            else:
                action = OBJECT_GET

            expression = Expression(action, [expression, child])
            continue

        # try reading .arm.hand.finger
        names, tokens = build_dotted_names(tokens)
        if names is not None:
            for name in names:
                child = Expression(Constant(STRING, name), None)
                expression = Expression(OBJECT_GET, [expression, child])
            continue

        # coudn't read any, we're done
        break
    return expression, tokens

def build_get_index(orig):
    """
    Read [0] or {'hello'} and return this as expression.
    """
    tokens = copy.copy(orig)
    expression, tokens = build_group_get(tokens, BracketGroup)
    if expression is not None:
        return expression, tokens, BracketGroup

    expression, tokens = build_group_get(tokens, BraceGroup)
    if expression is not None:
        return expression, tokens, BraceGroup

    return None, orig, None


def build_group_get(orig, group_cls):
    tokens = copy.copy(orig)
    group = list_pop(tokens, 0)
    if not isinstance(group, group_cls):
        return None, orig

    if len(group.values) != 1:
        return None, orig
    #print "get_index: ", group.values[0]
    child, left = build_expression(group.values[0])
    if child is None:
        return None, orig

    return child, tokens

def make_tokens_expression_old(orig, expression=None):
    """
    Orig is a Name. It is completely consumed here, hence not
    returning remaining tokens
    """
    tokens = copy.copy(orig)
    if len(tokens) == 0:
        return None
    elif len(tokens) == 1:
        return Expression(tokens[0])
    else:
        print "make_tokens_exp 1: ", tokens
        first = Expression(list_pop(tokens))
        if expression is None:
            expression = first
        else:
            expression = Expression(OBJECT_GET, [expression, first])
        print "make_tokens_exp 2: ", tokens
        for token in tokens:
            child = Expression(token, None)
            expression = Expression(OBJECT_GET, [expression, child])
        return expression


def build_variable(orig):
    tokens = copy.copy(orig)
    name = list_pop(tokens)
    if not isinstance(name, Name) or str(name) in RESERVED_WORDS:
        return None, orig

    expression = Expression(str(name))
    # read 0 or more get_index
    #print "build_variable 1: ", expression
    return build_get_indices(tokens, expression)


def build_constant_or_variable(orig):
    tokens = copy.copy(orig)
    expression, tokens = build_variable(tokens)
    if expression is not None:
        return expression, tokens

    name = list_pop(tokens, 0)
    if isinstance(name, Constant) or isinstance(name, Null):
        return Expression(name), tokens
    else:
        logging.debug('not a constant or variable')
        return None, orig


def read_name(orig):
    """
    Read names and constant values (true, false, null)
    """
    text = orig
    dest, text = re_match(VARIABLE_PATTERN, text)
    if dest is None:
        return None, orig
    elif dest in [TRUE, FALSE]:
        value = False if dest == FALSE else True
        return Constant(BOOL, value), text
    elif dest == NULL:
        return Null('null'), text
    else:
        return Name(dest), text

def build_dotted_names(orig):
    """
    Parse person.hand.finger
    Return list of strings 
    """
    text = copy.copy(orig)
    tokens = []
    # read dots and more strings
    while len(text) >= 2:
        if isinstance(text[0], Period):
            list_pop(text)
        else:
            break

        name = list_pop(text)
        if not isinstance(name, Name):
            return None, orig

        tokens.append(str(name))
    if len(tokens) == 0: return None, orig
    else: return tokens, text

def read_assignment_destination_token(orig):
    tokens = copy.copy(orig)
    destination, tokens = build_variable(tokens)
    if destination is None:
        return None, orig
    else:
        return destination, tokens

def read_assignment_destination_group(orig):
    tokens = copy.copy(orig)
    group = list_pop(tokens, 0)
    if not isinstance(group, ParenGroup):
        return None, orig

    destinations = []
    for term in group.values:
        expression, left = read_assignment_destination_token(term)
        if expression is None:
            return None, orig
        else:
            destinations.append(expression)
    return destinations, tokens


def read_assignment(orig):
    '''
    Assignment example: counter = 5
    '''
    tokens = copy.copy(orig)
    #print "assignment remaining0: ", tokens
    destinations, tokens = read_assignment_destination_group(tokens)
    if destinations is None:
        # try reading just one
        destination, tokens = read_assignment_destination_token(tokens)
        destinations = [destination]

   # print "assignment remaining 1: ", tokens
    setter, tokens = read_symbols(tokens, Setter)
    if not isinstance(setter, Setter):
        return None, orig

    # read expression on right side
    expression, tokens = build_expression(tokens)
    if expression != None:
        return Assignment(destinations, setter, expression), tokens

    return None, orig

def read_import_functions(orig):
    tokens = copy.copy(orig)
    group = list_pop(tokens)
    if not isinstance(group, ParenGroup):
        return None, orig

    functions = []
    print "read_import values: ", group.values
    for term in group.values:
        if len(term) != 1:
            return None, orig
        name = term[0]
        if not isinstance(name, Name):
            return None, orig
        functions.append(str(name))

    return functions, tokens

def read_import(orig):
    stack = copy.copy(orig)
    name = list_pop(stack)
    if not isinstance(name, Name) or str(name) != 'from':
        return None, orig

    root = list_pop(stack)
    if not isinstance(root, Name):
        return None, orig

    path = [str(root)]

    rest, stack = build_dotted_names(stack)
    if rest is not None:
        path.extend(rest)

    token = list_pop(stack)
    if not isinstance(token, Name) or str(token) != 'import':
        return None, orig

    functions, stack = read_import_functions(stack)
    if functions is None:
        function = list_pop(stack)
        if not isinstance(function, Name):
            return None, orig
        functions = [str(function)]

    return Import(path, functions), stack

def read_function_definition(orig):
    '''
    ex1: (int current) fibonacci(int index):
    return (Function, text_left)
    return (None, orig) if not function
    '''
    stack = copy.copy(orig)

    outputs, stack = read_arguments_definition(stack)
    if outputs is None:
        return None, orig

    function_name = list_pop(stack)
    if not isinstance(function_name, Name):
        return None, orig

    inputs, stack = read_arguments_definition(stack)
    if inputs is None:
        return None, orig

    colon = list_pop(stack)
    if not isinstance(colon, Colon):
        return None, orig

    if len(stack) > 0:
        return None, orig
    return Function(str(function_name), inputs, outputs), stack


def read_arg_definition(orig):
    '''
    Read int continue
    Return Variable()
    '''
    stack = copy.copy(orig)
    arg_type = list_pop(stack)
    if not isinstance(arg_type, Name):
        return None, orig
    # name
    name = list_pop(stack)
    if not isinstance(name, Name):
        return None, orig

    var = Variable(str(arg_type), str(name))
    return var, stack


def re_match(regex, text, index=0):
    m = re.match(regex, text)
    if m:
        return m.group(index), text[m.end():]
    else:
        return None, text


def read_arguments_definition(orig):
    '''
    (int a)
    ()
    (int a, string b)
    return variabes, text_left
    return None, text if not matched.
    '''
    stack = copy.copy(orig)

    group = list_pop(stack)
    # left paren
    if not isinstance(group, ParenGroup):
        return None, orig

    tokens = group.values
    # arguments
    variables = []
    for term in tokens:
        # match type name
        var, new_term = read_arg_definition(term)
        if var is None:
            raise Exception("Unable to read argument: {}".format(term))
        else:
            variables.append(var)

    # see if ended
    return variables, stack

def is_reserved(text):
    return text in RESERVED_WORDS


def empty_or_exception(tokens):
    if len(tokens) > 0:
        raise Exception("Syntax error")

text = ""

class Parser(object):
    # parse program text.
    def __init__(self, source_path):
        self.stack = []
        self.functions = []
        self.imports = []
        lines = 0
        texts = []
        tokens = []
        with open(source_path) as descriptor:
            while True:
                try:
                    tokens, stack_index, texts = read_tokens(descriptor)
                    lines += len(texts)
                    tokens = self.parse_statement(tokens, stack_index)
                except EOFException:
                    break
                except Exception as e:
                    raise Exception("{}. line: {} Error occurred after: {}\n {}", source_path, lines, texts, e)
                if len(tokens) != 0:
                    raise Exception("{}. line: {} Syntax error occurred during: {}. tokens = {}", source_path, lines, texts, tokens)

    def parse_statement(self, tokens, stack_index):
        """
        tokens is a list of length 0 or more.
        stack_index is number of spaces divided by 0.
        """
        #line = descriptor.readline()
        #logging.debug("parse_statement: <{}>".format(line))
        #if len(line) == 0:
        #    return False, []
        #line = line.rstrip()

        # how many spaces are in front?
        #stack_index = get_stack_index(line)
        #line = line.strip()
        if len(tokens) == 0:
            return tokens
        if isinstance(tokens[0], Pound):
            return []

        if stack_index < len(self.stack):
            num_pop = len(self.stack) - stack_index
            while num_pop > 0:
                self.stack.pop()
                num_pop -= 1
        elif stack_index > len(self.stack):
            logging.debug("stack index: {} stack: {}".format(stack_index, self.stack))
            raise Exception("spaced too much")

        # Either function or import
        if stack_index == 0:
            function, tokens = read_function_definition(tokens)
            if function is not None:
                #print "function_definition: {0}".format(function.get_dict())
                self.functions.append(function)
                self.stack.append(function)
                logging.debug("Read function defition")
                return tokens

            import_statement, tokens = read_import(tokens)
            if import_statement is not None:
                empty_or_exception(tokens)
                self.imports.append(import_statement)
                return tokens
            raise Exception("Function not found with no spaces")

        block = self.stack[-1]

        control_clause, tokens = read_flow_control(tokens)
        if control_clause is not None:
            block.code.append(control_clause)
            return tokens

        # conditional (if, elif, else, while)
        while_clause, tokens = read_while(tokens)
        if while_clause is not None:
            block.code.append(while_clause)
            self.stack.append(while_clause)
            logging.debug("Read while statement")
            return tokens

        for_clause, tokens = read_for(tokens)
        if for_clause:
            block.code.append(for_clause)
            self.stack.append(for_clause)
            logging.debug("Read for statement")
            return tokens

        if_clause, tokens = read_if(tokens)
        if if_clause:
            #print "if read: {0}".format(if_clause.get_dict())
            block.code.append(if_clause)
            self.stack.append(if_clause)
            logging.debug("Read if statement")
            return tokens

        elif_clause, tokens = read_elif(tokens)
        if elif_clause:
            #print "elif read: {0}".format(elif_clause.get_dict())
            logging.debug("Read elif statement")
            block.code.append(elif_clause)
            self.stack.append(elif_clause)
            return tokens

        else_clause, tokens = read_else(tokens)
        if else_clause:
            logging.debug("Read else statement")
            #print "else read: {0}".format(else_clause.get_dict())
            block.code.append(else_clause)
            self.stack.append(else_clause)
            return tokens

        assignment, tokens = read_assignment(tokens)
        if assignment:
            logging.debug("Read assignment")
            #print "assignment read: {0}. appending to: {1}".format(assignment, block)
            block.code.append(assignment)
            return tokens

        expression, tokens = build_expression(tokens)
        if expression is not None:
            logging.debug("Read expression")
            #print "expression read: {0}".format(expression)
            block.code.append(expression)
            return tokens

        return tokens
