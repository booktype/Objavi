#/bin/bash -e

# Unpack all the test epub files into
# tests/epub-examples/unzipped/<epub-name>

TESTDIR=`dirname $0`

cd $TESTDIR/epub-examples

[[ -d unzipped ]] || mkdir unzipped

for f in *.epub; do
    #echo $f
    d=unzipped/${f/.epub/}
    [[ -d "$d" ]] && continue
    mkdir "$d"
    unzip "$f" -d "$d"
done
