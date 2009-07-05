#!/bin/bash
# cobbled together from history

mkdir tmp
chmod 777 tmp
mkdir books
mkdir cache
sudo chgrp www-data books
sudo chgrp www-data cache
sudo chmod 775 books cache
sudo chmod g+s books cache
