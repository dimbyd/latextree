# latex2html.py

import os
from jinja2 import Environment, FileSystemLoader
import datetime 
import logging
log = logging.getLogger(__name__)

logging.basicConfig(
    filename = 'latextree.log', 
    format = '%(levelname)8s:%(name)8s:%(funcName)20s:%(lineno)4s %(message)s',
    level = logging.DEBUG,
)

from latextree.settings import LATEX_ROOT
from latextree.codec import accents_table
from latextree import LatexTree 
from latextree import settings

from latextree.parser.misc import parse_kv_opt_args, parse_length

# for copying static files to webserver
import fnmatch
import shutil

from collections import namedtuple
Xref = namedtuple('Xref', 'label url')

class WebsiteBuilder(object):
    '''
    Convert LaTeX documents to HTML
    '''
    # ==============================
    def __init__(self, tex_main=None, **kwargs):
        
        self.tex_main = tex_main
        self.tree = None
        self.LATEX_ROOT = None
        self.WEB_ROOT = None

        # input dir
        if not 'LATEX_ROOT' in kwargs:
            if self.tex_main:
                self.LATEX_ROOT = os.path.dirname(os.path.abspath(self.tex_main))
            else:
                self.LATEX_ROOT = settings.LATEX_ROOT

        # output dir
        if not 'WEB_ROOT' in kwargs:
            self.WEB_ROOT = settings.WEB_ROOT
        else:
            self.WEB_ROOT = kwargs['WEB_ROOT']

        # time stamp for output dir
        # from datetime import datetime
        # time_str = datetime.now().strftime('%m-%d-%H-%M-%S')
        # WEB_ROOT = os.path.join(WEB_ROOT, time_str)

        # create output dir if necessary
        if not os.path.exists(self.WEB_ROOT):
            os.makedirs(self.WEB_ROOT)

        # info
        log.info('input dir (LATEX_ROOT):  {}'.format(self.LATEX_ROOT))
        log.info('output dir (WEB_ROOT): {}'.format(self.WEB_ROOT))

        # build LatexTree object
        if self.tex_main:
            self.build_tree(self.tex_main)
        
    # ==============================
    def build_tree(self, tex_main):
        self.tex_main = tex_main 
        self.tree = LatexTree()
        self.tree.parse_file(tex_main)

    def write_xml(self):
        xtree = self.tree.write_xml()
        print(xtree)


    #----------------------------------------------
    # create urls - only needed for multipage site
    # and also for flask
    #----------------------------------------------

    def make_url(self, node, include_label=True):
        '''
        Generate URL for a Node object
        Defines the url structure for the HTML document.
        
        For documents containing chapters, sections etc. 
        we implement URL patterns of the form

            #chapter02-section03-eq:euler       (single page) 
            /chapter02-section03.html#eq:euler  (multiple pages)
        
        for an equation labelled `eq:euler` appearing in the
        third section of the second chapter.

        Labels are ignored by setting include_label=False. This is useful
        for tables of content in multi-page sites so that the browser hits
        the top of the page, not the chapter title.
        
        `label` attributes are set during post-processing by calling
         every Label object's `get_ancestor()` method to find the 
         nearest enclosing block. (Historical note: we no longer set 
         this during node creation because the parent attribute is now 
         set when the node is added to its parent's children. This is 
         a consequence of not passing an explicit stack through the
         recursive parse functions.

        '''

        # we don't need this for single-page

        # extract chapter/section numbers and create url
        # we could use slugs based on chapter-title etc.
        # chap = node.get_ancestor('chapter')
        # sect = node.get_ancestor('section')
        # cno = chap.number if chap and hasattr(chap, 'number') else 0
        # sno = sect.number if sect and hasattr(sect, 'number') else 0
        # url = (r'chapter%02dsection%02d.html' % (cno, sno))

        # append anchor if required
        url = ''
        if include_label:
            if hasattr(node, 'label') and node.label:
                url = ('#{}'.format(node.label))
        return url


    def create_context(self):
        '''
        Create context dictionary for passing to templates.
        We do post-processing Some of these shou
        We include the entirey LatexTree object
            context['tree'] = self.tree
        so we have access to everything contained in the tree.
        
        To reduce the amount of computation done in the templates,
        we extract some data into lookup tables
            chapters: list of chapters (if any)
            sections: list of sections (if any)
            xref_urls: Label -> URL table
            page_urls: Node -> URL table
        '''

        # initialise
        context = {}

        # create node -> url map 
        xrefs = {}
        for label, node in self.tree.labels.items():
            url = '#{}'.format(label)
            xref = Xref(label=label, url=url)
            xrefs.__setitem__(node, xref)
        for species_name in ['chapter','section','subsection']:
            for node in self.tree.get_phenotypes(species_name):
                if not node in xrefs:
                    label = node.get_mpath()
                    url = '#{}'.format(label) 
                    xref = Xref(label=label, url=url)
                    xrefs[node] = xref

        # create caption -> container map
        # Latex requires that labels for floats are put inside the caption, 
        # but we don't want the label associated with the caption, rather 
        # with the parent of the caption (usually a float). 
        # We could justassociating the label with  are put inside captions we don't want la
        containers = {}
        for cap in self.tree.get_phenotypes('caption'):
            cont = self.tree.get_container(cap)
            containers.__setitem__(cap, cont)

        # create includegraphics -> image file name map
        # and process attributes while we're at it .... !!
        image_files = {}
        for image in self.tree.get_phenotypes('includegraphics'):
            if 'options' in image.args and image.args['options']:
                opt_arg_str = image.args['options'].chars(nobrackets=True)
                kw = parse_kv_opt_args(opt_arg_str)[1]
                if 'scale' in kw:
                    image.width = str(int(100*float(kw['scale']))) + '%'
            src = image.args['file'].children[0].content
            image_files[src] = image
        
        image_files = {}
        for image in self.tree.get_phenotypes('includegraphics'):
            if 'options' in image.args and image.args['options']:
                opt_arg_str = image.args['options'].chars(nobrackets=True)
                kw = parse_kv_opt_args(opt_arg_str)[1]
                if 'scale' in kw:
                    image.width = str(int(100*float(kw['scale']))) + '%'
            src = image.args['file'].children[0].content
            image_files[src] = image
        
        # create context dict 
        # These should be computed in the LatexTree() class as far as
        # possible because they will be useful to other writer functions.
        # 
        # The whole purpose of the post-processing in tree.py is to 
        # extract data from the tree into more intuitive data structures 
        # for rendering (e.g. via templates).
        #
        # For example, video_urls maps `includevideo' objects
        # directly to the corresponding url (ascii). 
        # The url could be accessed in a template using:
        #   video.args['url'].chars(nobrackets=True)  
        # however it's less cluttered to use:
        #   if video in self.video_urls:
        #       <iframe src="{{ video_urls['video'] }}"></iframe>

        context['labels'] = self.tree.labels    # now computed in tree.py
        context['lang'] = 'cy'
        context['image_files'] = image_files    # now computed in tree.py
        context['containers'] = containers
        context['tree'] = self.tree
        context['xrefs'] = xrefs            # for single page
        context['accents'] = accents_table  # escape sequences
        context['today'] = datetime.datetime.today().strftime('%d/%m/%Y at %H:%M:%S')

        return context

    
    # ==============================
    def build_singlepage(self, lang='cy', copy_static=True, **kwargs):
        """Create single-page website from `LatexTree' object.
        
        :param lang: iso language code, defaults to 'cy'
        :type lang: str
        
        :param copy_static: copy static files to output directory
        :type copy_static: bool, defaults to True
        
        :return: Nothing - ouput written to file
        :rtype: None
        """
        # jinja2 stuff
        env = Environment(
            loader=FileSystemLoader(settings.TEMPLATE_ROOT), 
            # extensions=['jinja2.ext.do'], # not used
            # trim_blocks=True, 
            # lstrip_blocks=True,
        )

        # extract data and render template
        # single page = article always?
        # template = env.get_template('index.html.j2')
        template = env.get_template('article.html.j2')
        # if 'documentclass' in self.tree.preamble:
        #     if self.tree.preamble['documentclass'] == 'article':
        #         log.info('article class')
        #         template = env.get_template('article.html.j2')

        context = self.create_context()
        print(context)
        output = template.render(context)

        # write to file (should be index.html)
        output_file = os.path.join(self.WEB_ROOT, 'article.html')
        with open(output_file, "wb") as f:
            f.write(output.encode('utf-8')) 

        # copy static files across (.css, .js, etc.)
        # TODO: copy image files across (for includegraphics cmds)
        if copy_static:
            self.copy_static_files()
    
    # ------------------------------
    # multipage
    # ------------------------------
    def make_page_url(self, node, include_label=True):
        """Return URL of a node for multipage site.
         
        For documents containing chapters, sections etc. 
        URL patterns are of the form
            #chapter02-section03-eq:euler       (single page) 
            /chapter02-section03.html#eq:euler  (multiple pages)
        
        Labels are ignored by setting include_label=False. 
        This is useful for tables of contents etc.
        """

        # extract chapter/section numbers and create url
        # we could use slugs based on chapter-title etc.
        chap = node.get_ancestor('chapter')
        sect = node.get_ancestor('section')
        cno = chap.number if chap and hasattr(chap, 'number') else 0
        sno = sect.number if sect and hasattr(sect, 'number') else 0
        if not chap and not sect:
            url = 'index.html'
        else:
           url = r'chapter{:02}section{:02}.html'.format(cno, sno)

        # append anchor if required
        if include_label:
            if hasattr(node, 'label') and node.label:
                url = ('#{}'.format(node.label))

        return url

    def build_multipage(self, copy_static=True, **kwargs):
        """Create multi-page website for Latex documents."""

        # internal function
        def write_chapter_files(chapters):
            """Write chapters to separate files."""
            for cidx, chapter in enumerate(chapters):
                
                # set context
                context['chapter'] = chapter
                context['sections'] = [child for child in chapter.children if child.species == 'section']
                context["prv"] = chapters[cidx-1] if cidx > 0 else None
                context["nxt"] = chapters[cidx+1] if cidx+1 < len(chapters) else None
                
                # render and write to file
                template = env.get_template('chapter.html.j2')
                output = template.render(context)
                output_file = os.path.join(self.WEB_ROOT, self.make_page_url(chapter, include_label=False))
                with open(output_file, "wb") as f:
                    f.write(output.encode('utf-8'))
                
        # internal function
        def write_section_files(sections, chapters=None):
            """Write sections to separate files."""
            for sidx, section in enumerate(sections):
                
                # set context
                context['section'] = section
                context["prv"] = sections[sidx-1] if sidx > 0 else None
                context["nxt"] = sections[sidx+1] if sidx+1 < len(sections) else None
    
                # render and write to file
                template = env.get_template('section_detail.html.j2')
                output = template.render(context)
                output_file = os.path.join(self.WEB_ROOT, self.make_page_url(section, include_label=False))
                with open(output_file, "wb") as f:
                    f.write(output.encode('utf-8'))

        # jinja2 stuff
        env = Environment(
            loader=FileSystemLoader(settings.TEMPLATE_ROOT), 
            trim_blocks=True, 
            lstrip_blocks=True,
        )

        # no chapters and no sections (singlepage)
        if not self.tree.chapters and not self.tree.sections:
            self.build_singlepage(copy_static=copy_static, kwargs=kwargs)

        # create context 
        context = self.create_context()

        # create index page
        template = env.get_template('index.html.j2')
        output = template.render(context)
        output_file = os.path.join(self.WEB_ROOT, 'index.html')
        with open(output_file, "wb") as f:
            f.write(output.encode('utf-8'))

        # write chapter or section files
        if self.tree.chapters:
            write_chapter_files(self.tree.chapters)
        
        elif self.tree.sections:
            write_section_files(self.tree.sections)

        # copy static files to WEB_ROOT
        if copy_static:
            self.copy_static()


    def copy_static(self):
        self.copy_image_files()
        from_path = settings.STATIC_ROOT
        if os.path.exists(from_path):
            dest_path = os.path.join(self.WEB_ROOT, 'static/')
            if os.path.exists(dest_path):
                shutil.rmtree(dest_path)
            shutil.copytree(from_path, dest_path)

    def copy_static_files(self):
        '''
        Copy static files to webserver
            from:   STATIC_ROOT (current versions of css and js)
            to:     WEB_ROOT/static
        First we copy image files from LATEX_ROOT directory to the
        local STATIC_ROOT/img directory, then we copy the entire
        STATIC_ROOT directory over to WEB_ROOT/static (webserver)

        '''
        # copy image files (local)
        self.copy_image_files()

        # source dir
        from_path = settings.STATIC_ROOT

        # check it exists
        if os.path.exists(from_path):

            # target dir (webserver)
            to_path = os.path.join(self.WEB_ROOT, 'static/')
            
            # overwrite existing files if necessary
            if os.path.exists(to_path):
                shutil.rmtree(to_path)

            # copy everything over
            shutil.copytree(from_path, to_path)

    def copy_image_files(self):
        '''
        Copy image files from LATEX_ROOT to IMAGE_ROOT (local)
        These are then copied to the webserver by `copy_static_files`.
        '''
        
        # source dir
        from_path = self.LATEX_ROOT
        if 'graphicspath' in self.tree.preamble and self.tree.preamble['graphicspath']:
            # from_path = os.path.join(from_path, self.preamble['graphicspath'])
            pass

        # target dir (local)
        to_path = settings.IMAGE_ROOT
        if not os.path.exists(to_path):
            os.makedirs(to_path)

        # find image files in source dir
        file_list = os.listdir(from_path)
        formats = ('png', 'pdf',' jpg')
        image_files = []
        for fmt in formats:
            wildcard = r'*.%s' % fmt
            image_files.extend(fnmatch.filter(file_list, wildcard))

        # copy files to target dir
        for image_file in image_files:
            image_file = os.path.join(from_path, image_file)
            shutil.copy(image_file, to_path)


#------------------------------------------------
def main():

    print("LaTeX2HTML")

    
    # input file
    filename = 'tex/test_small/main.tex'
    filename = 'tex/test_article/main.tex'

    # create website builder
    b = WebsiteBuilder(filename)

    print('--------------------')
    print('Pretty:')
    print(b.tree.write_pretty())
    print('--------------------')
    print('Preamble:')
    # print(b.tree.preamble)
    # print('\n'.join(['{:16}:{}'.format(k,v.chars(nobrackets=True)) for k,v in b.tree.preamble.items()])) 
    print('\n'.join(['{:16}:{}'.format(k,v.chars(nobrackets=True)) for k,v in b.tree.preamble.items()])) 
    print('--------------------')
    print('Labels:')
    # print(b.tree.labels)
    print('\n'.join(['{:24}:{}'.format(k,v) for k,v in b.tree.labels.items()])) 
    print('--------------------')
    print('Sections:')
    print(b.tree.chapters)
    print(b.tree.sections)
    # print('\n'.join(['{:24}:{}'.format(k,v) for k,v in b.tree.sections.items()])) 
    print('--------------------')
    print('TOC:')
    toc = b.tree.toc
    def print_toc(toc):
        def _print_toc(toc, level=0):
            indent_str = '----'
            for sec, subsecs in toc.items():
                tit = ''
                if sec.genus == 'Section': 
                     tit = sec.args['title'].chars()
                print('{}{}{}'.format(level*indent_str, sec, tit))
                for subsec in subsecs:
                    _print_toc(subsec, level=level+1)
        _print_toc(toc)
    print_toc(toc)
    print('--------------------')
    print(b.tree.registry.marker_formats)
    print('--------------------')
    print(b.tree.registry.numbered)
    print('--------------------')
    print(b.tree.registry.names)
    print('--------------------')
    print('Website:')
    # b.build_website()
    b.build_singlepage()

if __name__ == '__main__':
    main()
    # help(WebsiteBuilder.build_singlepage)
    print(WebsiteBuilder.build_singlepage.__doc__)
