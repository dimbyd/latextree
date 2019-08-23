# registry.py
r'''
Here we define the ClassFactory() method to produce classes from
    1. name
    2. argnames
    3. base_class
    
We also define the Registry class to organise definitions so
that information is more easily available to the parser.
The Registry class contains the following dicts:
        species
        params
        block_commands
        declarations
        numbered
        numbered_like
        marker_formats
        custom
        names

The parser initializes the registry from coredefs.py the and updates
the tables in response to \newcommand, \newcounter etc.
'''

from logging import getLogger
log = getLogger(__name__)
import json

from .tokens import Token
from .node import Node
from .parameter import ArgTable, parse_definition
from .command import Command, Environment, Declaration

from .coredefs import character_names

def ClassFactory(name, argnames, BaseClass):
    '''
    Class registry.
    '''
    def __init__(self, **kwargs):
        
        # init the base class
        BaseClass.__init__(self)
        
        # is this defined in the calling environment for __init___? (confused)
        # it's only for convenience, so that a Dollar object doesn't need to
        # access coredefs.character_names in output functions (and to avoid having 
        # to test whether each name is a single non-alpha numeric character). 
        # Python allows classes to be called '$' or '&' but XML does not. Control 
        # words can be serialized easily because the corresponding classes have 
        # the same names, but control symbols do not. But why not? We only have
        # to perform the conversion for XML ...
        if symbol:
            setattr(self, 'symbol', symbol)

        # init ArgTable from .argnames
        if argnames:
            args = ArgTable.fromkeys(argnames, None)
            setattr(self, 'args', args)    
    
        # set argument values defined in kwargs
        for key, value in kwargs.items():
            if key not in argnames:
                raise AttributeError("Argument \'{}\' not valid for {}".format(key, self.__class__.__name__))
            self.args[key] = value
    
    # we use character names instead of symbols for control characters
    # because xml cannot handle element names like '$' 
    symbol = None
    if name and len(name) == 1 and ord(name) < 128 and not name.isalnum():
        if name in character_names:
            symbol = name
            name = character_names[name]
    
    # return the new class
    return type(name, (BaseClass,), {"__init__": __init__})


class Registry():
    '''
    Registry class. New definitions are added as the document is 
    parsed e.g. through \newcommand etc. These are recorded as
    Latex source in the `custom' table (keyed on species name)
    
    We also keep track of the enumerate nesting depth in `enum_depth'
    '''
    def __init__(self, defs=None):

        # definitions
        self.defs = {}  

        # registers keyed on species name
        self.species = {}               # types (all species are registered here)
        self.params = {}                # parameter definitions (type, name)
        
        self.block_commands = {}        # stop tokens for block commands (\section, \item)
        self.block_declarations = {}    # stop tokens for block declarations (\bf, \cy)

        # registers keyed on counter name (numbered species)
        self.numbered = {}              # reset counters for numbered species 
        self.numbered_like = {}         # shared counter for arbitrary species
        self.marker_formats = {}        # keyed on species name 
        self.names = {}                 # keyed on node.species + 'name' e.g. 'chaptername'

        # registers for runtime expansion
        self.custom = {}            # on-the-fly macro definitions  keyed on species_name: ascii
        self.theorem_names = {}             # on-the-fly theorem headings   species_name: Group()
        
        # enumerate nesting tracker (needed for enumi, enumii, ...)
        self.is_enum = False
        self.enum_depth = 0
        
        if defs:
            self.update_defs(defs)

    def pretty_print(self):
        print('--------------------')
        print('Registry')
        for key, val in self.species.items():
            print('\t{:15}{}'.format(key, val))
        print('--------------------')


    def update_defs(self, defs):
        '''
        Parse definitions dictionary. 
        '''
        
        # update defs
        self.defs.update(defs)

        # species and arguments
        if 'commands' in defs:
            self.update_species(defs['commands'], base_class=Command)

        if 'environments' in defs:
            self.update_species(defs['environments'], base_class=Environment)

        if 'declarations' in defs:
            self.update_species(defs['declarations'], base_class=Declaration)

        # stop tokens
        if 'block_commands' in defs:
            self.update_block_commands(defs['block_commands'])

        if 'block_declarations' in defs:
            self.update_block_declarations(defs['block_declarations'])

        # numbers
        if 'numbered' in defs:
            self.update_numbered(defs['numbered'])

        if 'numbered_like' in defs:
            self.update_numbered_like(defs['numbered_like'])

        # names
        if 'marker_formats' in defs:
            self.update_marker_formats(defs['marker_formats'])

        if 'names' in defs:
            self.update_names(defs['names'])

        # close (for debugging)
        print(self.defs)

    def update_species(self, genera, base_class=Node):
        '''
        Update species.
        '''
        # iterate over genera
        for genus in genera:

            # create class for this genus 
            parent_class = ClassFactory(genus, [], BaseClass=base_class)
            
            # iterate over species
            for species_def in genera[genus]:
                
                # parse the definition
                species_name, params = parse_definition(species_def)

                # # register declaration (hack - to make update_block_declarations easy)
                # if base_class == Declaration:
                #     dict.__setitem__(self.declarations, species_name, [])    
            
                # record parameters
                if params:
                    dict.__setitem__(self.params, species_name, params)    

                # record species class
                param_names = [p.name for p in params]
                new_class = ClassFactory(species_name, param_names, BaseClass=parent_class)
                dict.__setitem__(self.species, species_name, new_class)    



    def update_block_commands(self, block_commands):
        '''
        Update stop tokens for block commands (section, item ...). 
        We should include the species_name too here (currently checked in the parser)
        '''
        for species_name, stop_tokens in block_commands.items():
            if not species_name in self.species:
                log.warning('Warning: command {} not defined, stop tokens ignored').format(species_name)
                continue
            dict.__setitem__(self.block_commands, species_name, stop_tokens)


    def update_block_declarations(self, genus_names):
        '''
        Update stop tokens for block_declaration declarations.
        Tokens (2,'}') and (0,'end') are automatically added by the parser.
        Input: `block_declarations' is a list of Genus names
        '''
        # iterate over species
        for genus_name in genus_names:
            if not genus_name in self.defs['declarations']:
                log.warning('Warning: block declaration set {} not defined, stop tokens ignored').format(species_name)
                continue
            species_defs = self.defs['declarations'][genus_name]
            species_names = [parse_definition(sdef)[0] for sdef in species_defs]
            for species_name in species_names:
                stop_tokens = [Token(0,x) for x in species_names if not x == species_name]        
                dict.__setitem__(self.block_declarations, species_name, stop_tokens)



    def update_numbered(self, numbered):
        '''
        Update numbered species and reset counters.
        '''
        for species_name, master_name in numbered.items():
            if not species_name in self.numbered:
                dict.__setitem__(self.numbered, species_name, [])
            
            # create/update reset list
            if master_name in self.numbered:
                self.numbered[master_name].append(species_name)
            else:
                dict.__setitem__(self.numbered, master_name, [species_name])


    def update_numbered_like(self, numbered_like):
        '''
        Update shared counters (numbered_like).
        '''
        for species_name, numbered_name in numbered_like.items():
            if not numbered_name in self.numbered:
                log.warning('Warning: numbered species {} not defined. Ignored').format(numbered_name)
                continue
            dict.__setitem__(self.numbered_like, species_name, numbered_name)


    def update_marker_formats(self, marker_formats):
        for species_name, numeric_label in marker_formats.items():
            if not species_name in self.numbered:
                log.warning('Warning: numbered species {} not defined. Ignored'.format(species_name))
                continue
            for counter_name, counter_label in self.marker_formats.items():
                seed = '\\the' + counter_name
                numeric_label = numeric_label.replace(seed, counter_label)    

            dict.__setitem__(self.marker_formats, species_name, numeric_label)


    def update_names(self, names):
        for tex_name, name_defs in names.items():
            if not len(tex_name) > 4 or not tex_name[-4:] == 'name':
                continue
            if not tex_name in self.names:
                dict.__setitem__(self.names, tex_name, {})
            for iso_code, name in name_defs.items():
                dict.__setitem__(self.names[tex_name], iso_code, name)


    # ------------------------------
    # (relatively) interesting stuff starts here!
    # ------------------------------
    def is_genus(self, species_name, genus_name):
        if species_name in self.species:
            return self.species[species_name].__bases__[0].__name__ == genus_name
        return False

    def is_environment(self, species_name):
        if species_name in self.species:
            return self.species[species_name].__bases__[0].__bases__[0] == Environment
        return False

    def create_phenotype(self, species_name, base_class=Node):
        if not species_name in self.species:
            log.info('Creating new species: {}'.format(species_name))
            species_type = ClassFactory(species_name, [], BaseClass=base_class)
            dict.__setitem__(self.species, species_name, species_type)
            dict.__setitem__(self.params, species_name, [])
        return self.species[species_name]()

