#!/bin/sh
HERE=`dirname $0`
THERE='cloudy.halo.gen.nz:objavi2'
#THERE='www.booki.cc:objavi2'

rsync $@ -v -a \
    --include='tests/*.py' \
    --exclude='htdocs/books' \
    --exclude='htdocs/booki-books' \
    --exclude='htdocs/tmp' \
    --exclude='booki' \
    --exclude='pdf' \
    --exclude='log' \
    --exclude='perl' \
    --exclude='misc' \
    --exclude='cache' \
    --exclude='examples' \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='tests/' \
    --exclude='rsync.sh' \
    $HERE $THERE

echo $HERE

#rsync -r $HERE/../booki/lib/booki/ cloudy.halo.gen.nz:objavi2/booki/
#rsync $HERE/../booki/lib/booki/ cloudy.halo.gen.nz:objavi2/booki/
#echo booki