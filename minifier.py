import argparse
import sys
import re


OPS = ['+', '-', '*', '/', '+=', '-=', '*=', '/=', '=', '<', '>', '<=', '>=', ',', '(', ')', '{', '}', ';']
SPECIAL_OPS = ['+', '*', '+=', '*=', '(', ')']


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
    parser.add_argument("-w", "--keep-newline",
                        help="Keep newline control characters",
                        action='store_true')
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    newline = args.crlf
    for source_file in args.files:
        with open(source_file) as f:
            if args.names is True:
                print("File {}:".format(source_file))
            lines = f.readlines()
            if args.keep_newline is False:
                # Keep preprocessor lines (starting with #)
                lines = map(lambda x: x.replace(newline, '') if not x.startswith('#') else x, lines)
            lines = map(lambda x: x.replace('\t', ' '), lines)
            for op in OPS:
                lines = map(minify_operator(op), lines)
            lines = trim(lines)
            if args.keep_inline is False:
                lines = remove_inline_comments(lines)
            if args.keep_multiline is False:
                lines = remove_multiline_comments(lines)
            multi_spaces = re.compile(r'[  ]+ *')
            lines = map(lambda string: multi_spaces.sub(' ', string), lines)
            minified = ''.join(lines)
            print(minified)
            if args.stats is True:
                f.seek(0)
                contents = f.read()
                orig_size = len(contents)
                mini_size = len(minified)
                delta = orig_size - mini_size
                print("Original: {0} characters, Minified: {1} characters, {2} removed ({3:.1f}%)"
                      .format(orig_size, mini_size, delta, (float(delta) / float(orig_size)) * 100.0))


main()
