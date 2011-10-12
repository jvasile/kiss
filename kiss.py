#!/usr/bin/python

import sys, os, copy, subprocess, shlex, argparse
from mako.template import Template

__version__ = "1.2"
__author__ = "James Vasile"
__copyright__ = "Copyright 2011, James Vasile"
__license__ = "GPLv3 or later"
__maintainer__ = "James Vasile"
__email__ = "james@jamesvasile.com"
__status__ = "Development"

BKGRND_DIR = "images/bkgrnd"

defaults = {
           'bg_color':'black',
           'bg_height':"100%",
           'bg_image':'',
           'bg_width':"100%",
           'bg_x':"0px",
           'bg_y':"0px",
           'duration':0,
           'fill':False,
           'fit':False,
           'font_family':'Helvetica, Verdana, Arial, Sans-serif',
           'font_size':'40px',
           'font_style':'normal',
           'font_weight':'100',
           'halign':'left',
           'hpos':'center',
           'opacity':55,
           'text_bg':'black',
           'text_color':'white',
           'title':'',
           'vpos':'middle',
}

def make_transparent_pixel(fname, foreground, opacity):
   subprocess.call(shlex.split("convert -size 70x70 xc:gray(%s%%) mask.gif" % opacity))
   subprocess.call(shlex.split("convert -size 70x70 xc:%s  mask.gif -alpha Off  -compose Copy_Opacity   -composite  %s" % (foreground, fname)))
   os.unlink('mask.gif')

def get_template(fname="template.html"):
   with open(fname, 'r') as INF:
      template = INF.read()
   return Template(template)

class Slide():
   num = 1
   def __init__(self, d=None, raw=None, count=1, opt=None, deck=None):
      self.opt = opt or {}
      if deck:
         self.deck = deck
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
      if lparam == 'fill' or lparam == "fit":
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
      elif '.' in param and os.path.exists(param):
         d['bg_image'] = param
      elif '.' in param and os.path.exists(os.path.join("images", param)):
         d['bg_image'] = os.path.join("images", param)
      else:
         sys.stderr.write("Unrecognized slide parameter: [%s]\n" % param)
         sys.exit(-1)

   def parse_raw(self, raw):
      d={}
      for param in raw[0].split('['):
         self.parse_param(param.strip()[:-1], d)
      d['content'] = raw[1]
      return d

   def no_extra_fields(self, d):
      fields = defaults.keys() + ['content', 'last_slide', 'next', 'opaque_image', 'prev']
      for k,v in d.items():
         if not k.lower() in fields:
            sys.stderr.write("Unknown field: %s (%s)\n" % (k, v))
            sys.exit(-1)

   def process_markup(self, content):
      p = subprocess.Popen(['pandoc', '--from=markdown', '--to=html'],
                           stdin=subprocess.PIPE, stdout=subprocess.PIPE)
      return p.communicate(content)[0].replace('<br />','<br />\n')


   def render(self, universal=None, template='', last=False):
      l = {
           'content':'',
           'last_slide': "slide_%02d.html" % self.deck.count,
           'next':"slide_%02d.html" % min(self.deck.count, self.num+1),
           'opaque_image':os.path.join(BKGRND_DIR, "opaque_%02d.png" % self.num),
           'prev':'slide_%02d.html' % max(1, self.num-1),
           }
      l.update(defaults)
      if universal:
         for k,v in universal.items():
            l[k] = v
      for k,v in self.fields.items():
         l[k] = v

      if self.opt['title_h1'] and l['title'] != '':
         l['content'] = '<h1>%s</h1>%s' % (l['title'], l['content'])
      l['content'] = self.process_markup(l['content'])
      if l['vpos'] == 'center':
         l['vpos'] = "middle"

      self.no_extra_fields(l)
      fname = "slide_%02d.html" % self.num
      print "Writing %s" % fname
      with open(fname, 'w') as OUTF:
         OUTF.write( template.render(**l))
      subprocess.call(shlex.split("mkdir -p %s" % BKGRND_DIR))
      make_transparent_pixel(l["opaque_image"], l['text_bg'], l['opacity'])

class Slides():
   def __init__(self, fname=None, template=None, opt=None):
      self.slides=[]
      self.opt = opt or {}
      self.fname = fname
      if self.fname:
         self.load()
      self.template = template
   def load(self, fname=None):
      if not fname:
         fname = self.fname
      self.slides=[]
      with open(fname, 'r') as INF:
         pinpoint = INF.readlines()

      self.count = 0
      params=''
      raw=''
      for line in pinpoint:
         if line.startswith(';'):
            continue
         elif line.startswith('--'):
            if len(self.slides) == 0:
               self.slides.append(Slide(raw=[raw.replace("\n", ' ').strip(),''], count=self.count, opt=self.opt, deck=self))
            else:
               self.slides.append(Slide(raw=[params,raw], count=self.count, opt=self.opt, deck=self))
               params = line[2:].strip()
            raw=''
            self.count += 1
         else:
            raw += line

      self.slides.append(Slide(raw=[params,raw], count=self.count, opt=self.opt, deck=self))

   def render(self):
      for s in self.slides[1:]:
         s.render(universal=self.slides[0].fields, template=self.template, last=(s.num == len(self.slides) - 1))

def run_tests():
   print "TODO: test suite"
def init_dir():
   print "TODO: implement init dir"

def parse_cmdline():
   parser = argparse.ArgumentParser(description="Easily produce image-heavy, browser-based, minimal text slide deck.",
                                    usage="%s [opts] --template TEMPLATE INPUTFILE " % sys.argv[0],
                                    epilog='KISS is copyright (c) 2011 by James Vasile.',
                                    )
   parser.add_argument('-t', '--template', action='store', metavar="FILE", help='specify template FILE')
   parser.add_argument('--title-h1', action='store_true', help='Insert title of each page as first line of slide with <h1> tags')
   parser.add_argument('-i','--init', action='store_true', help='create a KISS project in this directory')
   parser.add_argument('--skeleton', action='store', metavar="DIR", help='specify skeleton directory for init to copy')
   parser.add_argument('--test', action='store_true', help='run test suite')

   parser.add_argument('datafile')

   opt = parser.parse_args(sys.argv[1:])

   if opt.init:
      init_dir()
   elif opt.test:
      run_tests()
   else:
      return opt
   sys.exit()

def main():
   o = parse_cmdline()
   s = Slides(o.datafile, template=get_template(o.template), opt=o.__dict__)
   s.render()

if __name__=="__main__":
   main()
