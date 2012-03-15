import sys, unittest
from unittest import TestCase
import kiss
from kiss import Slides, Slide

# run with "python testsuite.py"

class SlidesTest (TestCase):
   def setUp (self):
      self.slides = Slides("example.mdwn", template=kiss.get_template("template.html"), 
                           opt={'title_h1':True})
   def tearDown (self):  pass
        
   def test_init (self):

      """ Test Slides initialization. """

      self.failUnless(self.slides.template != None)

      unloaded_slides = Slides(template=kiss.get_template("template.html"), opt={'test':True})
      self.failUnless(unloaded_slides.slides == [])
      self.failUnless(unloaded_slides.opt['test'])
      

   def test_load (self):

      """ Test loading of example file. """

      self.failUnless(self.slides.fname == "example.mdwn")
      self.failUnless(self.slides.count == 14, "There are 9 slides in the example deck (and one universal slide).")
      self.failUnless(len(self.slides.slides) == 15, "There are 9 slides in the example deck (and one universal slide).")

   def test_load_defaults(self):
      """ Test loading of defaults from example file.

      For demonstration to the end user, the example file explicitly
      sets values that match the defaults.  This is convenient because
      we can test the loaded values against the defaults.  If they don't 
      match, either the load went wrong or the example file deviates (as
      it does by design for bg_image, for example.)
      """

      u = self.slides.slides[0].fields
      d = kiss.defaults
      self.failUnless(u['bg_color'] == d['bg_color'])
      self.failUnless(u['text_color'] == d['text_color'])
      self.failUnless(u['font_family'] == d['font_family'])
      self.failUnless(u['font_size'] == d['font_size'])
      self.failUnless(u['font_style'] == d['font_style'])
      self.failUnless(u['font_weight'] == d['font_weight'])
      self.failUnless(u['opacity'] == d['opacity'])
      self.failUnless(u['text_bg'] == d['text_bg'])
      self.failUnless(u['hpos'] == d['hpos'])
      self.failUnless(u['vpos'] == d['vpos'])
      self.failUnless(u['halign'] == d['halign'])
      self.failUnless(u['duration'] == d['duration'])
      self.failUnless(u['bg_image'] == 'images/example.png')
      self.failUnless(u['bg_height'] == d['bg_height'])
      self.failUnless(u['bg_width'] == d['bg_width'])
      self.failUnless(u['bg_x'] == d['bg_x'])
      self.failUnless(u['bg_y'] == d['bg_y'])
      self.failUnless(u['title'] == "KISS Demo")

   def test_unicode(self):
      """ Test that we load unicode input file properly. """

      ## Unicode strings inherit from basestring but not str
      f = self.slides.slides[1].fields
      self.failUnless(isinstance(f['content'], basestring))
      self.failIf(isinstance(f['content'], str), "Content isn't a str (Unicode strings don't inherit from str).")

   def test_comments(self):
      """ Test handling of comment lines (they start with ;) in input file. """

      for s in self.slides.slides:
         for line in s.fields['content'].split("\n"):
            self.failIf(line.startswith(';'), "No comments made it in to content.")

   def test_render (self):
      """ Test rendering of Slides. """
      self.slides.render()
      pass

 
def suite():

   suite1= unittest.TestLoader().loadTestsFromTestCase(SlidesTest)
   suite = unittest.TestSuite([suite1])
   return suite

def main():
   runner = unittest.TextTestRunner()
   test_suite = suite()
   runner.run (test_suite)

if __name__ == '__main__':
   main()
