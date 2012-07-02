#!/bin/bash

if ! test -d htdocs; then
  echo "error: run this in Objavi's toplevel directory"
  exit -1
fi

mkdir -m 775 htdocs/booki-books
mkdir -m 775 htdocs/books
mkdir -m 777 htdocs/tmp
mkdir -m 775 cache
mkdir -m 775 log

sudo chgrp www-data htdocs/booki-books
sudo chgrp www-data htdocs/books
sudo chgrp www-data cache
sudo chgrp www-data log

sudo chmod g+s htdocs/books
sudo chmod g+s cache
