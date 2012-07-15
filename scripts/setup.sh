#!/bin/bash

mkdir -m 775 data
mkdir -m 775 data/booki-books
mkdir -m 775 data/books
mkdir -m 775 data/shared
mkdir -m 775 data/tmp
mkdir -m 775 cache
mkdir -m 775 logs

sudo chgrp www-data data
sudo chgrp www-data data/booki-books
sudo chgrp www-data data/books
sudo chgrp www-data data/shared
sudo chgrp www-data data/tmp
sudo chgrp www-data cache
sudo chgrp www-data logs
