C Minifier
==========

A basic, portable C/C++ minifier I initially wrote to minify shaders.

This basically trims whitespace and removes comments. It doesn't do any lexical analyzing, so complex or twisted cases may make it fail.

I hope it will be as useful to you as it is to me.

Requirements
============

- Python 2.7.6 and higher


Use
===

- `python minifier.py source.c`


Example
=======

Given the following input file, `test.c`:
```
void	do_math(int * x) {
  *x += 5;
}

int	main(void) {
  int	result = -1, val = 4;

  do_math(&val);
  return result;
}
```
,

`python minifier.py test.c` will output the following result:

```
void do_math(int*x){*x+=5;}int main(void){int result=-1,val=4;do_math(&val);return result;}
```

License
=======

GPL v3
