#!/bin/bash

if ! test -d htdocs; then
  echo "error: run this in Objavi's toplevel directory"
  exit -1
fi

mkdir -m 775 htdocs/data
mkdir -m 775 htdocs/data/booki-books
mkdir -m 775 htdocs/data/books
mkdir -m 775 htdocs/data/shared
mkdir -m 775 htdocs/data/tmp
mkdir -m 775 cache
mkdir -m 775 log

sudo chgrp www-data htdocs/data
sudo chgrp www-data htdocs/data/booki-books
sudo chgrp www-data htdocs/data/books
sudo chgrp www-data htdocs/data/shared
sudo chgrp www-data htdocs/data/tmp
sudo chgrp www-data cache
sudo chgrp www-data log

#sudo chmod g+s htdocs/data/books
#sudo chmod g+s cache
