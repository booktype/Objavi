#!/usr/bin/perl -wT
#
# Copyright (C) 2008 Aleksandar Erkalovic, aerkalov@gmail.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version. For
# more details read LICENSE in the root of this distribution.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# As per the GPL, removal of this notice is prohibited.

BEGIN {
    # Set default current working directory (needed for mod_perl)
    if( $ENV{"SCRIPT_FILENAME"} && $ENV{"SCRIPT_FILENAME"} =~ /^(.+)\/[^\/]+$/ ) {
        chdir $1;
    }
    # Set library paths in @INC, at compile time
    unshift @INC, '.';
    require 'setlib.cfg';
}


use strict;
use CGI::Carp qw( fatalsToBrowser );
use CGI;
use File::Temp qw(:POSIX);
use TWiki;
use TWiki::Render;
use TWiki::Meta;
use TWiki::Func;

my $log="";

my $query = new CGI;

my $thePathInfo   = $query->path_info();
my $theRemoteUser = $query->remote_user();
my $theTopic      = $query->param( 'topic' );
my $theUrl        = $query->url;

my( $topic, $webName, $scriptUrlPath, $userName ) =
  TWiki::initialize( $thePathInfo, $theRemoteUser,
                     $theTopic, $theUrl, $query );



use TWiki::Contrib::ObjaviContrib;

if($query->request_method() eq "GET") {
    TWiki::Contrib::ObjaviContrib::handleRequest($webName, $userName, $thePathInfo, $query);
} else {
    TWiki::Contrib::ObjaviContrib::handlePublish($webName, $userName, $thePathInfo, $query);
}
