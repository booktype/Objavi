#!/bin/sh
HERE=`dirname $0`

rsync $@ -a \
    --include='tests/*.py' \
    --exclude='books' \
    --exclude='booki-books' \
    --exclude='epub' \
    --exclude='booki' \
    --exclude='pdf' \
    --exclude='perl' \
    --exclude='tmp' \
    --exclude='misc' \
    --exclude='cache' \
    --exclude='examples' \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='tests/' \
    --exclude='rsync.sh' \
    $HERE 'cloudy.halo.gen.nz:objavi2'

echo $HERE

rsync -r $HERE/../booki/lib/booki/ cloudy.halo.gen.nz:objavi2/booki/
#rsync $HERE/../booki/lib/booki/ cloudy.halo.gen.nz:objavi2/booki/
echo booki