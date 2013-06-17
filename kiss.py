#!/usr/bin/python
# -*- encoding:utf-8 -*-

"""
KISS is simple slide presentation tool.

It takes a file of (mostly) markdown and turns it into slides, as per
your (brief and easy) instructions.

KISS depends on Pandoc to handle your markdown.  If you don't have it
installed, KISS won't make proper slides.

KISS is copyright 2011-2012 James Vasile <james@jamesvasile.com>
Released under the GNU General Public License, version 3 or later.
See LICENSE file for copyright details.
"""

import sys, os, copy, subprocess, shlex, argparse, codecs, tarfile
from BeautifulSoup import BeautifulSoup
from mako.template import Template

__version__ = "1.2.2"
__author__ = "James Vasile"
__copyright__ = "Copyright 2011, James Vasile"
__license__ = "GPLv3 or later"
__maintainer__ = "James Vasile"
__email__ = "james@jamesvasile.com"
__status__ = "Development"

BKGRND_DIR = "images/tmp"

defaults = {
           'autorewind':'on',
           'bg_color':'black',
           'bg_height':"100%",
           'bg_image':'',
           'bg_width':"100%",
           'bg_x':"0px",
           'bg_y':"0px",
           'duration':"0",
           'fill':False,
           'fit':False,
           'font_family':'Helvetica, Verdana, Arial, Sans-serif',
           'font_size':'40px',
           'font_style':'normal',
           'font_weight':'100',
           'javascript':'',
           'halign':'left',
           'hpos':'center',
           'note':False,
           'opacity':"55",
           'text_bg':'black',
           'text_color':'white',
           'title':'',
           'vpos':'middle',
           'version':__version__
}

def encode_for_xml(unicode_data, encoding='ascii'):
   """
   Encode unicode_data for use as XML or HTML, with characters outside
   of the encoding converted to XML numeric character references.

   Downloaded from http://code.activestate.com/recipes/303668-encoding-unicode-data-for-xml-and-html/ on 13 Oct 2011
   "Licensed under the PSF License"
   """
   try:
      return unicode_data.encode(encoding, 'xmlcharrefreplace')
   except ValueError:
      # ValueError is raised if there are unencodable chars in the
      # data and the 'xmlcharrefreplace' error handler is not found.
      # Pre-2.3 Python doesn't support the 'xmlcharrefreplace' error
      # handler, so we'll emulate it.
      return _xmlcharref_encode(unicode_data, encoding)

def _xmlcharref_encode(unicode_data, encoding):
   """Emulate Python 2.3's 'xmlcharrefreplace' encoding error handler.

   Downloaded from http://code.activestate.com/recipes/303668-encoding-unicode-data-for-xml-and-html/ on 13 Oct 2011
   "Licensed under the PSF License"
   """
   chars = []
   # Step through the unicode_data string one character at a time in
   # order to catch unencodable characters:
   for char in unicode_data:
      try:
         chars.append(char.encode(encoding, 'strict'))
      except UnicodeError:
         chars.append('&#%i;' % ord(char))
   return ''.join(chars)

def make_transparent_pixel(fname, foreground, opacity):
   subprocess.call(shlex.split("convert -size 70x70 xc:gray(%s%%) mask.gif" % str(opacity)))
   subprocess.call(shlex.split("convert -size 70x70 xc:%s  mask.gif -alpha Off  -compose Copy_Opacity   -composite  %s" % (str(foreground), str(fname))))
   os.unlink('mask.gif')

def get_template(fname=None):
   if not fname:
      fname = "template.html"
   with open(fname, 'r') as INF:
      template = INF.read()
   return Template(template, input_encoding='utf-8',
                   output_encoding='utf-8')

class Slide():
   num = 1
   def __init__(self, d=None, raw=None, count=1, opt=None, deck=None):
      self.opt = opt or {}
      if deck:
         self.deck = deck # store pointer to parent object
      if d:
         self.fields = d
      elif raw:
         self.fields = self.parse_raw(raw)
      if count:
         self.num = count

   def parse_param(self, param, d):
      if not param:
         return

      if '=' in param:
         key, val = param.split('=',2)
         key = key.lower()
      else:
         key = param.lower()
         val = ''

      lparam = param.lower()
      if lparam == 'note':
         d['note'] = True
      elif lparam == 'fill' or lparam == "fit":
         d['fill'] = param == 'fill'
         d['fit'] = param == 'fit'
      elif lparam in 'aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue blueviolet brown burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk crimson cyan darkblue darkcyan darkgoldenrod darkgray darkgrey darkgreen darkkhaki darkmagenta darkolivegreen darkorange darkorchid darkred darksalmon darkseagreen darkslateblue darkslategray darkslategrey darkturquoise darkviolet deeppink deepskyblue dimgray dimgrey dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite gold goldenrod gray grey green greenyellow honeydew hotpink indianred indigo ivory khaki lavender lavenderblush lawngreen lemonchiffon lightblue lightcoral lightcyan lightgoldenrodyellow lightgray lightgrey lightgreen lightpink lightsalmon lightseagreen lightskyblue lightslategray lightslategrey lightsteelblue lightyellow lime limegreen linen magenta maroon mediumaquamarine mediumblue mediumorchid mediumpurple mediumseagreen mediumslateblue mediumspringgreen mediumturquoise mediumvioletred midnightblue mintcream mistyrose moccasin navajowhite navy oldlace olive olivedrab orange orangered orchid palegoldenrod palegreen paleturquoise palevioletred papayawhip peachpuff peru pink plum powderblue purple red rosybrown royalblue saddlebrown salmon sandybrown seagreen seashell sienna silver skyblue slateblue slategray slategrey snow springgreen steelblue tan teal thistle tomato turquoise violet wheat white whitesmoke yellow yellowgreen':
         d['bg_color'] =  param
         d['bg_image'] = ''
      elif key == 'bg_color':
         d['bg_color'] = val
         d['bg_image'] = ''
      elif '=' in param:
         d[key]=val
      elif lparam in ['top', 'bottom', 'left', 'right', 'center', 'top_left', 'top_right', 'bottom_right', 'bottom_left']:
         if 'top' in lparam:
            d['vpos'] = 'top'
         elif 'bottom' in lparam:
            d['vpos'] = 'bottom'
         elif lparam in ['left', 'right', 'center']:
            d['vpos'] = 'middle'

         if 'left' in lparam:
            d['hpos'] = 'left'
         elif 'right' in lparam:
            d['hpos'] = 'right'
         elif lparam in ['top', 'center', 'bottom']:
            d['hpos']='center'
      elif lparam == "bold":
         d['font_weight']="bold"
      elif param.endswith(".js") and os.path.exists(os.path.join("js", param)):
         if not 'javascript' in d:
            d['javascript'] = ''
         d['javascript'] += '<script type="text/javascript" language="Javascript1.2" src="%s"></script>\n' % os.path.join("js", param)
      elif '.' in param and os.path.exists(param):
         d['bg_image'] = param
      elif '.' in param and os.path.exists(os.path.join("images", param)):
         d['bg_image'] = os.path.join("images", param)
      else:
         sys.stderr.write("Unrecognized slide parameter: [%s]\n" % param)
         sys.exit(-1)

      if 'bg_image' in d and d['bg_image']:
         self.deck.images[d['bg_image']] = d['bg_image']

   def parse_raw(self, raw):
      d={}
      for param in raw[0].split('['):
         self.parse_param(param.strip()[:-1], d)
      d['content'] = raw[1]
      return d

   def no_extra_fields(self, d):
      fields = defaults.keys() + ['content', 'javascript', 'last', 'last_slide', 'next', 'opaque_image', 'prev']
      for k,v in d.items():
         if not k.lower() in fields:
            sys.stderr.write("Unknown field: %s (%s)\n" % (k, v))
            sys.exit(-1)

   def process_markup(self, content):
      try:
         p = subprocess.Popen(['pandoc', '--from=markdown', '--to=html'],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE)
      except OSError, e:
         if e.errno == 2:
            sys.stderr.write("Couldn't run Pandoc.  Is it installed?\n")
            sys.exit(1)
         else:
            raise
      return p.communicate(content)[0].replace('<br />','<br />\n')
      

   def get_fields(self, universal = None):
      """return all the fields in the slide, taking into account the
      universal slide and the defaults and the per-slide options"""

      l = {
           'content':'',
           'last':self.num == self.deck.count,
           'last_slide': "slide_%02d.html" % self.deck.count,
           'next':"slide_%02d.html" % min(self.deck.count, self.num+1),
           'opaque_image':os.path.join(BKGRND_DIR, "opaque_%02d.png" % self.num),
           'prev':'slide_%02d.html' % max(1, self.num-1),

           }

      l.update(defaults)
      if not universal:
         universal = self.deck.slides[0].fields
      for k,v in universal.items():
         l[k] = v
      for k,v in self.fields.items():
         l[k] = v
      return l
   def render(self, universal=None, template='', last=False):
      l = self.get_fields()
      l['content'] = self.process_markup(l['content'].encode('utf8')).strip()
      if not l['title']:
          soup= BeautifulSoup(l['content'])
          body = soup.find('h1')
          if body:
              l['title'] = body.contents[0]
      if l['vpos'] == 'center':
         l['vpos'] = "middle"

      if l['duration'] != "0":
         l['duration'] = int(l['duration']) * 1000
      self.no_extra_fields(l)
      if l['note']:
         fname = "note_%02d.html" % (self.num-1)
      else:
         fname = "slide_%02d.html" % self.num
      print "Writing %s" % fname
      with open(fname, 'w') as OUTF:
         l['content'] = encode_for_xml(l['content'].decode('UTF-8', "ignore"), 'ascii')
         OUTF.write( template.render(**l))
      subprocess.call(shlex.split("mkdir -p %s" % BKGRND_DIR))
      make_transparent_pixel(l["opaque_image"], l['text_bg'], l['opacity'])

class Slides():
   def __init__(self, fname=None, template=None, opt=None):
      self.slides=[]
      self.images = {}
      self.opt = opt or {}
      self.fname = fname
      if self.fname:
         self.load()
      self.template = template
   def load(self, fname=None):
      if not fname:
         fname = self.fname
      self.slides=[]
      with codecs.open(fname, "r", "utf-8" ) as INF:
         pinpoint = INF.readlines()

      self.count = 0
      params=''
      raw=''
      for line in pinpoint:
         if line.startswith(';'):
            continue
         elif line.startswith('--'):
            if len(self.slides) == 0:
               ## Universal slide
               self.slides.append(Slide(raw=[raw.replace("\n", ' ').strip(),''], count=self.count, opt=self.opt, deck=self))
            else:
               self.slides.append(Slide(raw=[params,raw], count=self.count, opt=self.opt, deck=self))
            params = line[2:].strip()
            raw=''
            if not self.slides[-1].get_fields()['note']:
               self.count += 1
         else:
            raw += line

      self.slides.append(Slide(raw=[params,raw], count=self.count, opt=self.opt, deck=self))

   def render(self):
      for s in self.slides[1:]:
         s.render(universal=self.slides[0].fields, template=self.template, last=(s.num == len(self.slides) - 1))

def check_init_dir(d):
   """ Check that a skeleton dir has the cs and js directories. """
   return (os.path.exists(d) and 
           os.path.exists(os.path.join(d, 'css')) and
           os.path.exists(os.path.join(d, 'js')))
def init_dir(opt):
   script_name = os.path.splitext(os.path.basename(sys.path[0]))[0]
   script_dir = os.path.abspath(sys.path[0])
   share = "/usr/share/%s" % script_name
   local = "/usr/local/share/%s" % script_name

   ## Find skeleton directory
   if opt.skeleton:
      skel = opt.skeleton
   elif check_init_dir(script_dir):
      skel = script_dir
   elif check_init_dir(share):
      skel = share
   elif check_init_dir(local):
      skel = local
   else:
      sys.stderr.write("Can't find css or javascript files for %s.  You can specify a directory for them with the --skeleton option.\n" % script_name)
      sys.exit(-1)
      
   
   subprocess.call(shlex.split("cp -r %(d)s/css %(d)s/js %(d)s/template.html %(d)s/example.mdwn ." % {'d': skel}))
   subprocess.call(shlex.split("mkdir -p %s" % BKGRND_DIR))
   subprocess.call(shlex.split("cp -r %(d)s/images/example_cactus.jpg  %(d)s/images/example_ottoman.jpg  %(d)s/images/example.png images" % {'d': skel}))

def parse_cmdline():
   parser = argparse.ArgumentParser(description="Easily produce image-heavy, browser-based, minimal text slide deck.",
                                    usage="%s [opts] [TEMPLATE] INPUTFILE " % sys.argv[0],
                                    epilog='KISS is copyright (c) 2011 by James Vasile.',
                                    )
   parser.add_argument('-i','--init', action='store_true', help='create a KISS project in this directory')
   parser.add_argument('--skeleton', action='store', metavar="DIR", help='specify skeleton directory for init to copy', default=None)
   parser.add_argument('-z','--zip', action='store_true', help='build then pack a KISS project into a .tar.gz')

   parser.add_argument('template', nargs='?', default=None)
   parser.add_argument('inputfile', nargs='?', default=None)

   opt = parser.parse_args(sys.argv[1:])

   if opt.init:
      init_dir(opt)
      sys.exit()
   elif not opt.template:
      parser.print_usage()
      sys.stderr.write("%s: error: too few arguments\n" % os.path.basename(sys.argv[0]))
      sys.exit(-1)
   elif not opt.inputfile:
      opt.inputfile = opt.template
      opt.template = None
   return opt

def targz_project(inputfile, templatefile, slides):
   
   images = {}
   with tarfile.open(os.path.splitext(inputfile)[0]+ ".tar.gz", 'w:gz') as OUTF:
      for f in os.listdir('.'):
         if f.startswith('slide_') and f.endswith('.html'):
            OUTF.add(f)
            with open(f, 'r') as INF:
               b = BeautifulSoup(INF.read())
               for i in b.findAll('img'):
                  images[i['src']] = i['src']

      for f in slides.images.keys():
         images[f] = f

      for i in images.keys():
         print i
         OUTF.add(i)

      OUTF.add("css")
      OUTF.add("js")
      OUTF.add(inputfile)
      OUTF.add(templatefile or "template.html")

def main():
   o = parse_cmdline()
   s = Slides(o.inputfile, template=get_template(o.template), opt=o.__dict__)
   for f in os.listdir('.'):
      if f.startswith('slide_') and f.endswith('.html'):
         os.unlink(f)
   s.render()
   if o.zip:
      targz_project(o.inputfile, o.template, s)


if __name__=="__main__":
   main()
