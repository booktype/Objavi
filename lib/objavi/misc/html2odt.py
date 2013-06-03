#!/usr/bin/python
"""Convert html files to ODF.

html2odt source.html destination.odt
"""

from __future__ import with_statement
import sys, os, subprocess, multiprocessing, time

import uno
from com.sun.star.beans import PropertyValue
from com.sun.star.connection import NoConnectException

def _inspect_obj(o):
    print >> sys.stderr, 'inspecting %r' % o
    for a in  dir(o):
        try:
            print >> sys.stderr, "%25s %s" % (a, getattr(o, a))
        except Exception, e:
            print >> sys.stderr, "%s DOES NOT WORK! (%s)" % (a, e)

def file_url(path):
    if path.startswith('file:///'):
        return path
    return "file://" + os.path.abspath(path)

class Oo(object):
    def __init__(self):
        """Start up an open office and connect to it."""
        accept_string = "socket,host=localhost,port=2002;urp;StarOffice.ComponentContext"

        self.soffice = subprocess.Popen(["soffice", "-nologo", "-nodefault",
                                         "-norestore", "-nofirststartwizard",
                                         "-headless", "-invisible", "-nolockcheck",
                                         "-accept=%s" % accept_string], 
                                        env=dict(HOME=os.environ['HOME'], 
                                                 PATH=os.environ['PATH']), 
                                        close_fds=True)

        for i in range(20):
            time.sleep(0.5)
            try:
                local = uno.getComponentContext()
                self.resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
                self.context = self.resolver.resolve("uno:" + accept_string)
                self.desktop = self.unobject("com.sun.star.frame.Desktop", self.context)
                break
            except NoConnectException:
                print >> sys.stderr, '.',
        else:
            print >> sys.stderr, "Failed to connect soffice"
            self.resolver = None
            self.context = None
            self.desktop = None


    def unobject(self, klass, context=None):
        """get an instance of the class named by <klass>.  It will
        probably be a string that looks like
        'com.sun.something.SomeThing'."""
        if context is None:
            return self.context.ServiceManager.createInstance(klass)
        return self.context.ServiceManager.createInstanceWithContext(klass, context)

    def load(self, src):
        """Attempt to load as TextDocument format, but fall back to
        WebDocument if that doesn't work.  (WebDocument is called
        writer/web in the gui and is less exportable."""
        # import property values:
        # http://api.openoffice.org/docs/common/ref/com/sun/star/document/MediaDescriptor.html
        try:
            return self.desktop.loadComponentFromURL(src, "_blank", 0,
                                                     (PropertyValue("Hidden" , 0 , True, 0),
                                                      PropertyValue("FilterName" , 0 , 'HTML (StarWriter)', 0),
                                                      ))
        except Exception, e:
            print >> sys.stderr, e
        #fall back on default WebDocument format
        return self.desktop.loadComponentFromURL(src, "_blank", 0,
                                                 (PropertyValue("Hidden" , 0 , True, 0),
                                                  ))

    def embed_graphics(self, doc):
        """Reset each graphic object to an embedded copy of itself."""
        gp = self.unobject("com.sun.star.graphic.GraphicProvider")
        for i in range(doc.GraphicObjects.Count):
            g = doc.GraphicObjects.getByIndex(i)
            props = (PropertyValue("URL", 0, g.GraphicURL, 0),)
            g.setPropertyValue("Graphic", gp.queryGraphic(props))

    def convert(self, src, dest):
        """Use the connected open office instance to convert the file
        named by <src> into odf and save it as <dest>.

        The main trick here is forcing the images to be stored inline."""
        src = file_url(src)
        dest = file_url(dest)
        print >> sys.stderr, src
        print >> sys.stderr, dest

        doc = self.load(src)
        self.embed_graphics(doc)
        doc.storeToURL(dest, (PropertyValue("FilterName", 0, 'writer8', 0),
                              PropertyValue("Overwrite", 0, True, 0 )))
        doc.dispose()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.desktop:
            self.desktop.dispose()
        if self.context:
            self.context.dispose()
        if self.soffice.poll() is not None:
            print >> sys.stderr, "soffice exit with return code %s" % self.soffice.returncode
        else:
            print >> sys.stderr, "sending SIGTERM to soffice"
            for x in range(10):
                os.kill(self.soffice.pid, 15)
                time.sleep(0.25)
                if self.soffice.poll() is not None:
                    print >> sys.stderr, "soffice exit with return code %s" % self.soffice.returncode
                    break
                print >> sys.stderr, '*',
            else:
                print >> sys.stderr, "sending SIGKILL to soffice"
                os.kill(self.soffice.pid, 9)


def set_env(workdir):
    workdir = os.path.abspath(workdir)
    os.environ['HOME'] = workdir
    os.chdir(workdir)
    print >> sys.stderr, os.environ


def run(workdir, src, dest):
    """Runs the conversion."""
    set_env(workdir)
    with Oo() as oo:
        oo.convert(src, dest)


def run_subprocess(workdir, src, dest):
    """Runs the conversion in a subprocess."""
    p = multiprocessing.Process(target = run, args = (workdir, src, dest))
    p.start()
    p.join()


if __name__ == '__main__':
    workdir, src, dest = sys.argv[1:4]
    run(workdir, src, dest)

