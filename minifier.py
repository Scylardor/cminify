import sys
import re

OPS = [ '+', '-', '*', '/', '+=', '-=', '*=', '/=', '=', '<', '>', '<=', '>=', ',', '(', ')', '{', '}', ';']
SPECIAL_OPS = [ '+', '*', '+=', '*=', '(', ')']


def remove_everything_between(subs1, subs2, line):
    regex = re.compile(subs1 + r'.*' + subs2)
    return regex.sub('', line)

def remove_everything_before(subs, line):
    regex = re.compile(r'.*' + subs)
    return regex.sub('', line)

def remove_everything_past(subs, line):
    regex = re.compile(subs + r'.*')
    return regex.sub('', line)

def remove_multiline_comments(lines):
    start,end = '/*', '*/'
    escaped_start, escaped_end = '/\*', '\*/'
    in_comment = False
    newlines = []
    for line in lines:
        if not in_comment:
            start_pos = line.find(start)
            if start_pos != -1:
                in_comment = True
                end_pos = line.find(end)
                # inline multiline comment
                if start_pos < end_pos:
                    line = remove_everything_between(escaped_start, escaped_end, line)
                    in_comment = False
                else:
                    line = remove_everything_past(escaped_start, line)
        else:
            end_pos = line.find(end)
            if end_pos != -1:
                line = remove_everything_before(escaped_end, line)
                in_comment = False
                start_pos = line.find(start)
                # start of another comment on the same line
                if start_pos != -1:
                    line = remove_everything_past(escaped_start, line)
                    in_comment = True
            else:
                line = ''
        newlines.append(line)
    return newlines

def remove_inline_comments(lines):
    return map(lambda x: remove_everything_past('//', x), lines)

def trim(lines):
    return map(lambda x: x.strip(" \t"), lines)

def minify_operator(op):
    to_compile = r' *'
    if op in SPECIAL_OPS:
        to_compile += "\\"
    to_compile += op + r" *"
    regex = re.compile(to_compile)
    return lambda string: regex.sub(op, string)

with open(sys.argv[1]) as f:
    lines = f.readlines()
    lines = map(lambda x: x.replace('\n', '') if not x.startswith('#') else x, lines)
    lines = map(lambda x: x.replace('\t', ' '), lines)
    for op in OPS:
        lines = map(minify_operator(op), lines)
    lines = trim(lines)
    lines = remove_inline_comments(lines)
    lines = remove_multiline_comments(lines)
    multi_spaces = re.compile(r'[  ]+ *')
    lines = map(lambda string: multi_spaces.sub(' ', string), lines)
    print ''.join(lines)
