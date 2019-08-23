# codec.py
r'''
For converting say \'{o} to U+00E9
In HTML documents this can be rendered using &#x00e9

We could use unicode in mathmode as an alternative to MathJax
From the example `pylatexenc.readthedocs.io` it appears that
the package can't convert \[\int_0^1 x^2\,dx = \frac{1}{3}\]
very well but it was only one test ...
'''

unicode_accents = (
    ("'", u"\N{COMBINING ACUTE ACCENT}"),
    ("`", u"\N{COMBINING GRAVE ACCENT}"),
    ('"', u"\N{COMBINING DIAERESIS}"),
    ("c", u"\N{COMBINING CEDILLA}"),
    ("^", u"\N{COMBINING CIRCUMFLEX ACCENT}"),
    ("~", u"\N{COMBINING TILDE}"),
    ("H", u"\N{COMBINING DOUBLE ACUTE ACCENT}"),
    ("k", u"\N{COMBINING OGONEK}"),
    ("=", u"\N{COMBINING MACRON}"),
    ("b", u"\N{COMBINING MACRON BELOW}"),
    (".", u"\N{COMBINING DOT ABOVE}"),
    ("d", u"\N{COMBINING DOT BELOW}"),
    ("r", u"\N{COMBINING RING ABOVE}"),
    ("u", u"\N{COMBINING BREVE}"),
    ("v", u"\N{COMBINING CARON}"),
)

# convert character names to hex values (a dict keyed on the accent character)
accents_table = {acc[0]:ord(acc[1]) for acc in unicode_accents}

def main():
    ac = "`"
    ch = 'o'
    if ac in accents_table:
        tt = ch+str(accents_table[ac])
        print(tt + '<')
        print(ord(ac))

    # tt = {}
    # for x in unicode_accents:
    #     tt 

if __name__ == '__main__':
    main()

