# misc.py
r'''
Some useful parse functions:
    parse_kv_opt_args 
    parse_length

To deal with:
    \includegraphics[width=0.5\textwidth]{pic.png}
    \tabular*{0.5\textwidth}{|ccc|}
'''

from collections import OrderedDict

def write_roman(num):
    '''
    Function to convert integer to roman numeral
    '''
    roman = OrderedDict()
    roman[1000] = "M"
    roman[900] = "CM"
    roman[500] = "D"
    roman[400] = "CD"
    roman[100] = "C"
    roman[90] = "XC"
    roman[50] = "L"
    roman[40] = "XL"
    roman[10] = "X"
    roman[9] = "IX"
    roman[5] = "V"
    roman[4] = "IV"
    roman[1] = "I"

    def roman_num(num):
        for r in roman.keys():
            x, y = divmod(num, r)
            yield roman[r] * x
            num -= (r * x)
            if num <= 0:
                break

    return "".join([a for a in roman_num(num)])

def parse_kv_opt_args(text):
    '''
    Parse contents of simple optional argument
    A mixture of atomic and key-value pairs is permitted
    e.g. '[arg1, arg2, key1=val1, key2=val2]'
    '''
    if text[0]=='[' and text[-1]==']':
        text = text[1:-1]
    items =  text.split(',')
    args = [item.strip() for item in items if '=' not in item]
    pairs = [item.split('=') for item in items if '=' in item]
    pairs = [(x.strip(), y.strip())for x,y in pairs]
    kwargs = dict(pairs)
    return (args, kwargs)


def parse_length(text, paperwidth_mm='210'):
    '''
    Converts Latex lengths (e.g 0.25\textwidth) into percentages,
    more suitable for rendering HTML
    '''
    scale_factor_mm = {
        'px': 0.26,
        'pt': 0.35,
        'mm': 1.0,
        'cm': 10.0,
        'ex': 1.5,  # approx.
        'em': 3.5,  # approx. (depends on font size)
        'bp': 0.35,
        'dd': 0.38,
        'pc': 4.22,
        'in': 25.4,
    }
    
    # naughty!
    import re   

    print('Parsing length x{}x'.format(text))

    # textwidth and linewidth
    match = re.search(r'(.*)\\[textwidth,linewidth]', text)
    if match:
        prop = match.groups()[0]
        if not prop:
            prop = '1.0'
        pct = 99*float(prop)
        return r'{}%'.format(int(pct))
    
    # css lengths
    match = re.search(r'(.+)(em|ex|mm|cm|in|pt|px)', text)
    if match:
        length = match.groups()[0]
        unit = match.groups()[1]
        if unit in scale_factor_mm:
            length_mm = float(length)*scale_factor_mm[unit]
        pct = 100*length_mm/float(paperwidth_mm)
        return (r'{}\%'.format(int(pct)))

    # failed
    return None
