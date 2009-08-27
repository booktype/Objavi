#!/usr/bin/python
from __future__ import with_statement
import sys, os, subprocess, time

import uno
from com.sun.star.beans import PropertyValue

def file_url(path):
    if path.startswith('file:///'):
        return path
    return "file://" + os.path.abspath(path)

class Oo(object):
    def __init__(self):
        self.connect()

    def connect(self):
        accept_string = "socket,host=localhost,port=2002;urp;StarOffice.ComponentContext"

        self.ooffice = subprocess.Popen(["ooffice", "-nologo", "-nodefault",
                                         "-norestore",
                                         "-headless", # "-invisible",
                                         "-accept=%s" % accept_string])

        time.sleep(3)

        local = uno.getComponentContext()
        self.resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
        self.context = self.resolver.resolve("uno:" + accept_string)
        self.desktop = self.unobject("com.sun.star.frame.Desktop", self.context)

    def unobject(self, klass, context=None):
        if context is None:
            return self.context.ServiceManager.createInstance(klass)
        return self.context.ServiceManager.createInstanceWithContext(klass, context)

    def convert(self, src, dest):
        src = file_url(src)
        dest = file_url(dest)

        doc = self.desktop.loadComponentFromURL(src, "_blank", 0,
                                                (PropertyValue("Hidden" , 0 , True, 0),))

        gp = self.unobject("com.sun.star.graphic.GraphicProvider")


        if True:
            for a in  dir(doc.GraphicObjects):
                try:
                    print "%25s %s" % (a, getattr(doc.GraphicObjects, a))
                except:
                    print "%s DOES NOT WORK!" % a

    
        #there are probably simpleer ways to iterate, but this works.
        #Reset each graphic object to an embedded copy of itself. 
        for gn in doc.GraphicObjects.ElementNames:            
            g = doc.GraphicObjects.getByName(gn)
            props = (PropertyValue("URL", 0, g.GraphicURL, 0),)
            g.setPropertyValue("Graphic", gp.queryGraphic(props))

        doc.storeToURL(dest, (PropertyValue("FilterName", 0, 'writer8', 0),
                              PropertyValue("Overwrite", 0, True, 0 )))
        doc.dispose()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.desktop.dispose()
        self.context.dispose()
        #self.resolver.dispose()
        self.ooffice.kill()



if __name__ == '__main__':
    src, dest = sys.argv[1:3]
    with Oo() as oo:
        oo.convert(src, dest)


