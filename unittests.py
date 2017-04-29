import unittest
from minifier import minify_source  # this is what we test

class DummyArgs:
    """A "fake" args class that allows us to define ad hoc parameters"""
    pass

class TestMinify(unittest.TestCase):

    def test_basic(self):
        inputTxt = """
void	do_math(int * x) {
    *x += 5;
}

int	main(void) {
    int	result = -1, val = 4;

    do_math(&val);

	typedef int toto;
	sizeof (toto);
	sizeof toto;

    return result;
}
"""
        expected = "void do_math(int*x){*x+=5;}int main(void){int result=-1,val=4;do_math(&val);typedef int toto;sizeof(toto);sizeof toto;return result;}"
        minified = minify_source(inputTxt, None)
        self.assertEqual(minified, expected)


    def test_negative_macros(self):
        inputTxt = """#define MAXIMUM_SCALE 16383
#define ESCAPE 256
#define DONE -1
#define FLUSH -2

int main() {
#define INFUNC -1

return 0;
}
"""
        expected = """#define MAXIMUM_SCALE 16383
#define ESCAPE 256
#define DONE -1
#define FLUSH -2
int main(){
#define INFUNC -1
return 0;}"""
        minified = minify_source(inputTxt, None)
        self.assertEqual(minified, expected)



    def test_if_without_braces(self):
        inputTxt = """
void printval(long long val)
{
    if (val)
        printf("%lli", val);
    else
        printf("val is null");
}
"""
        expected = """void printval(long long val){if(val)printf("%lli",val);else printf("val is null");}"""
        minified = minify_source(inputTxt, None)
        self.assertEqual(minified, expected)



    def test_multiline_comments(self):
        inputTxt = """int main() {
int a = 42;
/*
here be dragons
more dragons
a lot of dragons
*/
int b = -1;

return 0;
}
"""

        # are they removed ?
        expected = "int main(){int a=42;int b=-1;return 0;}"
        minified = minify_source(inputTxt, None)
        self.assertEqual(minified, expected)

        # are they kept ?
        args = DummyArgs()
        args.keep_multiline = True
        minified = minify_source(inputTxt, args)
        expected = "int main(){int a=42;/*here be dragonsmore dragonsa lot of dragons*/int b=-1;return 0;}"
        self.assertEqual(minified, expected)


    def test_inline_comments(self):
        inputTxt = """int main() {
int a = 42; // The only answer
int b = -1; // Not the only answer
// Below: an empty comment
//
return 0;
}
"""
        # are they removed ?
        expected = "int main(){int a=42;int b=-1;return 0;}"
        minified = minify_source(inputTxt, None)
        self.assertEqual(minified, expected)

        # are they kept ?
        args = DummyArgs()
        args.keep_inline = True
        minified = minify_source(inputTxt, args)
        # This is "expected" but kind of bogus since the code now won't compile.
        # Maybe it would be cool to fix it someday, but anyway, it's kinda weird
        # to keep inline comments without keeping newlines.
        expected = "int main(){int a=42;//The only answerint b=-1;//Not the only answer//Below: an empty comment//return 0;}"
        self.assertEqual(minified, expected)


if __name__ == '__main__':
    unittest.main()
