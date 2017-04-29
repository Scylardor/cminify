#!/usr/bin/env python2.7
#     C Minify Copyright (C) 2015 Alexandre Baron
#     This program comes with ABSOLUTELY NO WARRANTY; for details read LICENSE.
#     This is free software, and you are welcome to redistribute it
#     under certain conditions; read LICENSE for details.

import argparse
import sys
import re
import os  # SEEK_END etc.

# Ops: ops that may be spaced out in the code but we can trim the whitespace before and after
# Spaced ops are operators that we need to append with one trailing space because of their syntax (e.g. keywords).
# NB: theses ops are the SUPPORTED ones and these lists may not be complete as per the Standard
OPS = [
    '+', '-', '*', '/', '%', '++', '--',
    '+=', '-=', '*=', '/=', '%=', '=', '==', '!=',
    '&&', '||', '!', '&', '|', '^', '<<', '>>',
    '<', '>', '<=', '>=', '<<=', '>>=', '&=', '|=', '^=', ',',
    '(', ')', '{', '}', ';', 'else'
]
SPACED_OPS = ['else']
UNARY_OPS= ["+", "-", "&", "!", "*"]

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
    start, end = '/*', '*/'
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


def minify_operator(op):
    """Returns a function applying a regex to strip away spaces on each side of an operator
    Makes a special escape for operators that could be mistaken for regex control characters."""
    to_compile = " *{} *".format(re.escape(op))
    regex = re.compile(to_compile)
    repl = op
    if op in SPACED_OPS:
        repl += " "
    return lambda string: regex.sub(repl, string)


def show_stats(orig_text, minified_text):
    # After "f.readlines", the file pointer is at file's end so tell() will return current file size.
    orig_size = len(orig_text)
    mini_size = len(minified_text)
    delta = orig_size - mini_size
    print(
        "Original: {0} characters, Minified: {1} characters, {2} removed ({3:.1f}%)"
        .format(orig_size, mini_size, delta, (float(delta) / float(orig_size)) * 100.0)
    )


def fix_spaced_ops(minified_txt):
    """This will walk the spaced ops list and search the text for all "[OP] {" sequences occurrences
    and replace them by "[OP]{" since there is no operator in the C syntax for which the spacing
    between the op and the '{' is mandatory.
    We do this because to manage spaced ops that may or may not be used with braces (e.g. "else"),
    we may have added unnecessary spaces (e.g. because the brace was on next line),
    so we can fix it here."""
    for op in SPACED_OPS:
        pattern = "{} {{".format(op)  # {{ for literal braces
        repl = "{}{{".format(op)
        minified_txt = re.sub(pattern, repl, minified_txt)
    return minified_txt


def fix_unary_operators(lines):
    """Ops processing can have eliminated necessary space when using unary ops
    e.g. "#define ABC -1" becomes "#define ABC-1", because the unary '-' is being
    mistaken for a binary '-', so the space has been trimmed.
    We can fix this kind of thing here, but it pretty much highlights the limits of such
    a parser..."""
    regex_unary_ops = '[{}]'.format(''.join(UNARY_OPS))
    regex_unary_ops = re.escape(regex_unary_ops)
    # Use capture groups to separate, e.g. in "#define MACROVALUE", "#define MACRO" from "VALUE"
    # pattern will detect problems like "#define FLUSH-2"
    # Format braces here -----------v
    pattern = "^(#[a-z]+ +[\w\d]+)([{}][\w\d]+)$".format(regex_unary_ops)
    # Simply add one more space between macro name and value
    repl = r'\1' + " " + r'\2'
    # Process each preprocessor line and modify it inplace as we need to keep order
    for (idx, line) in enumerate(lines):
        if line.startswith('#'):
            for op in UNARY_OPS:
                line = re.sub(pattern, repl, line)
            lines[idx] = line
    return lines


def minify_source_file(args, orig_source):
    lines = orig_source.split('\n')
    intermediate_string = ""

    lines = map(lambda x: x.replace('\t', ' '), lines)
    # erase leading and trailing whitespace but do it BEFORE processing spaced ops!
    # and specify only spaces so it doesn't strip newlines
    lines = map(lambda x: x.strip(' '), lines)
    # for each operator: remove space on each side of the op, on every line.
    # Escape ops that could be regex control characters.
    for op in OPS:
        lines = map(minify_operator(op), lines)
    if args.keep_inline is False:
        lines = remove_inline_comments(lines)
    if args.keep_multiline is False:
        lines = remove_multiline_comments(lines)
    # Finally convert all remaining multispaces to a single space
    multi_spaces = re.compile(r'[  ]+ *')
    lines = map(lambda string: multi_spaces.sub(' ', string), lines)
    # Ops processing can have eliminated necessary space when using unary ops
    # e.g. "#define ABC -1" becomes "#define ABC-1", so we can fix it here
    lines = fix_unary_operators(lines)

    if args.keep_newlines is True:
        minified = args.newline.join(lines)
    else:
        minified = ''.join(lines)

    # There is no syntactic requirement of an operator being spaced from a '{' in C so
    # if we added unnecessary space when processing spaced ops, we can fix it here
    minified = fix_spaced_ops(minified)
    intermediate_string += minified
    if args.stats is True:
        show_stats(orig_source, minified)
    # Add a newline before every hash if neccessary
    for i, c in enumerate(intermediate_string):
        if i >= 1:
            if c == '#':
                if intermediate_string[i-1] != '\n':
                    intermediate_string = intermediate_string[:i] + '\n' + intermediate_string[i:]
    # Delete empty lines inserted by previous loop
    for i, c in enumerate(intermediate_string):
        if i >= 1:
            if intermediate_string[i] == '\n' and intermediate_string[i+1] == '\n':
                final_string = intermediate_string[:i] + intermediate_string[i+1:]

    return final_string


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs='+', help="Input files")
    parser.add_argument("-c", "--crlf",
                        help="Use CRLF as newline control character (\r\n)",
                        default='\n',
                        action='store_const', const='\r\n')
    parser.add_argument("-n", "--names",
                        help="Show name of processed files",
                        action='store_true')
    parser.add_argument("-s", "--stats",
                        help="Show statistics on minified version",
                        action='store_true')
    parser.add_argument("-m", "--keep-multiline",
                        help="Don't strip multiline comments (/* ... */)",
                        action='store_true')
    parser.add_argument("-i", "--keep-inline",
                        help="Do not strip inline comments (// ...)",
                        action='store_true')
    parser.add_argument("-w", "--keep-newlines",
                        help="Keep newline control characters",
                        action='store_true')
    args = parser.parse_args()
    return args



def get_minification_delta(source_file, minified_text):
    """Computes how much the code size has been reduced after minification"""
    # TODO : this function is completely broken at the moment
    orig_size = source_file.tell()
    mini_size = len(minified_source)
    delta = orig_size - mini_size
    return delta


def print_additional_info(orig_source, minified_source, filename, args):
    """Prints out additional info on the minification based on given args"""
    if args.names is True:
        print("{}:".format(filename))

    if args.stats is True:
        orig_size = len(orig_source)
        mini_size = len(minified_source)
        delta = get_minification_delta(orig_source_code, minified_source_code)
        if orig_size != 0:
            print(
                "Original: {0} characters, Minified: {1} characters, {2} removed ({3:.1f}%)"
                .format(orig_size, mini_size, delta, (float(delta) / float(orig_size)) * 100.0)
            )


def process_files(args):
    """Minifies a list of code files and displays additional info based on
    given args"""
    for filename in args.files:
        orig_source_code = ""
        newline = None  # would use \n by default
        # No matter the original newline character used (LF or CRLF), python
        # will always use \n in code. But when outputting the minified
        # source, we need to know which newline character was used, and
        # specifying 'U' tells open to store it in f.newlines
        # cf. https://docs.python.org/2/library/functions.html#open
        with open(filename, 'U') as f:
            orig_source_code = f.read()
            newline = f.newlines

        if type(newline) is tuple:
            print(
                "Mixed newlines are unsupported, skipping file {}."
                .format(filename)
            )
            continue

        args.newline = newline  # storing the wanted newline character
        minified_source_code = minify_source_file(args, orig_source_code)

        print_additional_info(
            orig_source_code, minified_source_code, filename, args
        )

        # Finally output the minified code
        print(minified_source_code)


def main():
    args = get_args()
    process_files(args)


if __name__ == "__main__":
    main()
