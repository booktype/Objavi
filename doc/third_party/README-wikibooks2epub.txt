USAGE:
    wikibook2epub -i http://en.wikibooks.org/wiki/Latin -o /var/www/Latin.epub

INSTALLATION:
    to use wikibook2epub you need python-oxlib
        bzr branch http://code.0xdb.org/python-oxlib
        cd python-oxlib && sudo python setup.py install

    you also need python modules simplejson and elementtree
    and
        apt-get install zip

    after that install it:
        sudo python setup.py install
    
    wikibook2epub uses oxlibs web cache, if you can not write to $HOME/.ox
    you can overwrite the location of the cache by setting oxCACHE 
    export oxCACHE=/tmp/ox

Open Questions:
    - Math formulas, how to deal with them
    - Images, how to download/embed them
    - Images should be replaced with highest possible version for print

TODO:
    - make this a WikiBook class
    - create TOC / index. what about sorting / subversion
    - what about print vs. other views (i.e. Basic Physics of Nuclear Medicine)




