from parser import read_expression_line, read_expression_lines, read_assignment_line, read_import_line, Import

def test_expression():
    lines = ['[a+b]']
    expression, left = read_expression_lines(lines)
    assert expression is not None
    print "{} {}".format(expression, left)

    lines = [
        'get_name({',
        '"first":"mike",',
        '"last":"yu"',
        '}):'
    ]
    expression, leftt = read_expression_lines(lines)
    assert expression is not None
    print "{} {}".format(expression, left)

    lines = [
        '[a[0]*b[1]]',
    ]
    expression, left = read_expression_lines(lines)
    assert expression is not None
    print "{} {}".format(expression, left)

    lines = [
        '[a[0]*b[1] - c[2]*d[3],'
        'e]',
    ]
    expression, left = read_expression_lines(lines)
    assert expression is not None
    print "{} {}".format(expression, left)

    lines = [
        '(vector[i] * vector[i])'
    ]
    expression, left = read_expression_lines(lines)
    assert expression is not None
    print "{} {}".format(expression, left)
    lines = [
        #'if value >= 0 && value < lengths[axis]:'
        'value >= 0 && value < lengths[axis]'
        #'value >= 0 && value < lengths[axis]'
        #'value < 0'
            ]
    expression, left = read_expression_lines(lines)
    print "test_expression {} {}".format(expression, left)
    assert expression is not None and len(left) == 0

    lines = [
        'assert(matrix == [[1,2,3],[4,5,6]])'
    ]
    expression, left = read_expression_lines(lines)
    print "test_expression assert {} {}".format(expression, left)
    assert expression is not None and len(left) == 0

def test_assignment():
    print "Testing assignments"
    expression = read_assignment_line('a = 5')
    assert expression is not None
    print "{}".format(expression)

    line = 'text = null'
    expression = read_assignment_line(line)
    assert expression is not None
    print "test assignment 0: {}".format(expression)

    expression = read_assignment_line('sum += 5')
    assert expression is not None
    print "{}".format(expression)

    expression = read_assignment_line('some[axis] += value')
    assert expression is not None
    print "{}".format(expression)

    expression = read_assignment_line('sum_indices = [indices[0], indices[1], indices[2]]')
    assert expression is not None
    print "{}".format(expression)
    text = 'faces[0][0] = true'
    expression = read_assignment_line(text)
    assert expression is not None
    print "{}\n {}".format(text, expression)
    text = 'face.arm = true'
    expression = read_assignment_line(text)
    assert expression is not None
    print "test asignment {}\n {}".format(text, expression)
    text = '(a, b, c) = bob()'
    expression = read_assignment_line(text)
    assert expression is not None
    print "test asignment 2 {}\n {}".format(text, expression)

def test_parser():
    expression, left = read_import_line("from shared import translate")
    assert expression is not None
    assert isinstance(expression, Import)
    print "test_parser: {}".format(expression)

    expression, left = read_import_line("from shared import (translate, bob)")
    assert expression is not None
    assert isinstance(expression, Import)
    print "test_parser 2 : {}".format(expression)

    lines = ['"john"']
    expression, left = read_expression_line(lines[0])
    assert expression is not None
    lines = ['a + b']
    expression, left = read_expression_line(lines[0])
    assert expression is not None
    lines = ['0']
    expression, left = read_expression_line(lines[0])
    assert expression is not None
    lines = ['length(c)']
    expression, left = read_expression_line(lines[0])
    assert expression is not None
    lines = ['length(c)[0][1][2]']
    expression, left = read_expression_line(lines[0])
    assert expression is not None
    lines = ['(length(c))[0][1][2]']
    expression, left = read_expression_line(lines[0])
    assert expression is not None
    print "test parser: {}".format(expression)
    assert expression is not None
    lines = ['d[0]']
    expression, left = read_expression_line(lines[0])
    assert expression is not None
    lines = ['[e, f]']
    expression, left = read_expression_line(lines[0])
    assert expression is not None
    lines = ['[g, str(h)]']
    expression, left = read_expression_line(lines[0])
    assert expression is not None
    print "starting dict test 1"
    lines = ['{"name":"mike"}']
    expression, left = read_expression_line(lines[0])
    assert expression is not None
    lines = ['{"first":"alex", "last":"oh"}']
    expression, left = read_expression_line(lines[0])
    assert expression is not None
    line = '((position[0] - middleX)/middleX)*width'
    expression, left = read_expression_line(line)
    assert expression is not None
    line = 'keyboard.key_state.bob'
    expression, left = read_expression_line(line)
    assert expression is not None
    print "test parser 3: {}".format(expression)

    line = 'mouse.button[2]'
    expression, left = read_expression_line(line)
    assert expression is not None
    print "test parser 4: {}".format(expression)

    line = '{ "position": [0,0,0], "bob": "dole", "nice": "brother" }'
    expression, left = read_expression_line(line)
    assert expression is not None
    print "test parser 5: {}".format(expression)

    line = 'file_read(join([state.things_dir, "/", state.thing_name]), text)'
    expression, left = read_expression_line(line)
    assert expression is not None
    print "test parser 6: {}".format(expression)


if __name__ == '__main__':
    test_parser()
    test_expression()
    test_assignment()
