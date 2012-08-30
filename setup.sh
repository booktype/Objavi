#!/bin/bash

mkdir -m 775 htdocs/books
mkdir -m 775 htdocs/booki-books
mkdir -m 775 htdocs/tmp
mkdir -m 775 cache
mkdir -m 775 log

sudo chgrp -R www-data htdocs/books
sudo chgrp -R www-data htdocs/booki-books
sudo chgrp -R www-data htdocs/tmp
sudo chgrp -R www-data cache
sudo chgrp -R www-data log

chmod 775 htdocs/*.cgi htdocs/font-list.cgi.pdf
sudo chgrp www-data htdocs/*.cgi htdocs/font-list.cgi.pdf
