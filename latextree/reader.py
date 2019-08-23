# reader.py 
#   read_json_defs
#   read_latex_document (recursive)
#   parse_tokens_length

import os, re
import json
import logging
log = logging.getLogger(__name__)

def read_json_defs(defs_file=None):
    r'''
    Read command and environment definitions from a json file
    The file should consist of a single dictionary structure
    The following keys will be processed:
        1. control_chars 
        2. commands
        3. environments
        4. block_commands 
        5. declarations
        6. counters
    '''        
    try:
        with open(defs_file, 'r') as input_file:
            log.info('Reading definitions from {}'.format(defs_file))           
            defs = json.load(input_file)
            return defs

    except FileNotFoundError as e:
        log.warning("File {} not found".format(e.filename))
        return None

def read_latex_file(filename):
    r'''
    Read from command source file
    Recursive down through \input or \include commands
    '''
    def read_source(filename, level=0):
        '''
        Recursive function (max depth = 4)
        Uses regular expressions, which seems a bit anti-stream-processing!!
        '''
        
        # careful now!
        if level > 4:
            log.warning('Recursion depth limit exceeded')
            return ''
        
        with open(filename) as f:
            log.info('Reading from %s', filename)
            text = f.read()
            
        # find input commands
        pattern = re.compile(r'[^%+]\\(input|include)\{([^\}]*)\}')
        matches = re.finditer(pattern, text)
        
        # return contents if none found (end recursion)
        if not matches:
            return text
        
        # otherwise process input commands (recursive calls)
        else:
            s = ''
            start_index = 0
            for match in matches:
                
                end_index = match.start()
                s += text[start_index:end_index]
                start_index = match.end()
                nested_filename = match.groups()[1]
                
                # append .tex extension if necessary
                if not re.search(r'\.', nested_filename):
                    nested_filename = nested_filename + '.tex'
                
                nested_filename = os.path.join(os.path.dirname(filename), nested_filename)
                log.info('Reading from %s', nested_filename)
                
                # recursive call
                s += read_source(nested_filename, level=level+1)
            s += text[start_index:]
            return s
    
    return read_source(filename)
    
    

def main():
    import settings
    defs_file = os.path.join(settings.EXTENSIONS_ROOT, 'examdef.json')
    x = read_json_defs(defs_file)
    print(x)

if __name__ == '__main__':
    main()

