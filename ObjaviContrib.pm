# Plugin for TWiki Enterprise Collaboration Platform, http://TWiki.org/
#
# Copyright (C) 2000-2003 Andrea Sterbini, a.sterbini@flashnet.it
# Copyright (C) 2001-2006 Peter Thoeny, peter@thoeny.org
# and TWiki Contributors. All Rights Reserved. TWiki Contributors
# are listed in the AUTHORS file in the root of this distribution.
# NOTE: Please extend that file, not this notice.
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
# For licensing info read LICENSE file in the TWiki root.
# change the package name and $pluginName!!!

package TWiki::Contrib::ObjaviContrib;

# Always use strict to enforce variable scoping
use strict;

require TWiki::Func;    # The plugins API
require TWiki::Plugins; # For the API version

# $VERSION is referred to by TWiki, and is the only global variable that
# *must* exist in this package.
use vars qw( $VERSION $RELEASE $SHORTDESCRIPTION $debug $pluginName $NO_PREFS_IN_TOPIC );

use File::Temp qw/ tempfile  /;
use List::Compare::Functional qw( get_unique );

# This should always be $Rev$ so that TWiki can determine the checked-in
# status of the plugin. It is used by the build automation tools, so
# you should leave it alone.
$VERSION = '$Rev$';

# This is a free-form string you can use to "name" your own plugin version.
# It is *not* used by the build automation tools, but is reported as part
# of the version number in PLUGINDESCRIPTIONS.
$RELEASE = 'TWiki-4.2';

# Short description of this plugin
# One line description, is shown in the %TWIKIWEB%.TextFormattingRules topic:
$SHORTDESCRIPTION = 'Empty Plugin used as a template for new Plugins';

# You must set $NO_PREFS_IN_TOPIC to 0 if you want your plugin to use preferences
# stored in the plugin topic. This default is required for compatibility with
# older plugins, but imposes a significant performance penalty, and
# is not recommended. Instead, use $TWiki::cfg entries set in LocalSite.cfg, or
# if you want the users to be able to change settings, then use standard TWiki
# preferences that can be defined in your Main.TWikiPreferences and overridden
# at the web and topic level.
$NO_PREFS_IN_TOPIC = 1;

# Name of this Plugin, only used in this module
$pluginName = 'ObjaviContrib';


use Data::Dumper;

=pod

---++ initPlugin($topic, $web, $user, $installWeb) -> $boolean
   * =$topic= - the name of the topic in the current CGI query
   * =$web= - the name of the web in the current CGI query
   * =$user= - the login name of the user
   * =$installWeb= - the name of the web the plugin is installed in

REQUIRED

Called to initialise the plugin. If everything is OK, should return
a non-zero value. On non-fatal failure, should write a message
using TWiki::Func::writeWarning and return 0. In this case
%FAILEDPLUGINS% will indicate which plugins failed.

In the case of a catastrophic failure that will prevent the whole
installation from working safely, this handler may use 'die', which
will be trapped and reported in the browser.

You may also call =TWiki::Func::registerTagHandler= here to register
a function to handle variables that have standard TWiki syntax - for example,
=%MYTAG{"my param" myarg="My Arg"}%. You can also override internal
TWiki variable handling functions this way, though this practice is unsupported
and highly dangerous!

__Note:__ Please align variables names with the Plugin name, e.g. if 
your Plugin is called FooBarPlugin, name variables FOOBAR and/or 
FOOBARSOMETHING. This avoids namespace issues.


=cut

sub initPlugin {
    my( $topic, $web, $user, $installWeb ) = @_;

    # check for Plugins.pm versions
    if( $TWiki::Plugins::VERSION < 1.026 ) {
        TWiki::Func::writeWarning( "Version mismatch between $pluginName and Plugins.pm" );
        return 0;
    }

#    my $setting = $TWiki::cfg{Plugins}{EmptyPlugin}{ExampleSetting} || 0;
#    $debug = $TWiki::cfg{Plugins}{EmptyPlugin}{Debug} || 0;


##    TWiki::Func::registerRESTHandler('example', \&restExample);

    return 1;
}

=pod

---++ restExample($session) -> $text

This is an example of a sub to be called by the =rest= script. The parameter is:
   * =$session= - The TWiki object associated to this session.

Additional parameters can be recovered via de query object in the $session.

For more information, check TWiki:TWiki.TWikiScripts#rest

*Since:* TWiki::Plugins::VERSION 1.1

=cut

sub restExample {
   my ($session) = @_;
   return "This is an example of a REST invocation\n\n";
}


sub handleRequest {
    my ($webName, $userName, $thePathInfo, $query) = @_;

    my $htmlData = <<END;
<html>
        <head>
	<title>OBJAVI!</title>
	                <meta http-equiv="Content-Type" content="text/html; charset=en_GB" />
			                <meta  name="robots" content="noindex" /> 
					                <link rel="icon" href="http://www.flossmanuals.net/pub/TWiki//FlossSkin2/fl2.ico" type="image/x-icon" /> <link rel="shortcut icon" href="http://www.flossmanuals.net/pub/TWiki/FlossSkin2/fl2.ico" type="image/x-icon" />
							                <link rel=StyleSheet href="http://www.flossmanuals.net/pub/TWiki/FlossSkin2/typography_cover.css" type="text/css" media="screen"/>
<style type="text/css">
img {
        display:block;
}
* {margin:0}
</style>
<style>
body
{
margin:0;
padding:0
}
#header
{
position:absolute;
top:23px;
width:100%;
background-image:
url('http://www.flossmanuals.net/pub/TWiki/FlossSkin2/header_bg.gif');
background-position: 600px 0px; /* this places the orange background at
an offset, making sure it doesn't underlap the left side of the gif */
background-repeat: no-repeat;
    }
    #header_imagemap
    {
    margin-left: 352px;
    border: 0px
    }
h1 {
color:#ff7f00;
}
h2 {
color:#ff7f00;
}
h3 {
color:#000000;
}
</style>
</head><body background="http://www.flossmanuals.net/pub/TWiki/FlossSkin2/background.gif" style="margin:0;color:#000000;text-decoration:none;">
<div id="header"><img id="header_imagemap" width="465" height="95" alt="FlossManuals menu" src='http://www.flossmanuals.net/pub/TWiki/FlossSkin2/objavib_entireheader4.gif' border=0 usemap='#map'></div>
</div>
                <div style="position:absolute;left:270px;top:130px;">
<table  cellpadding="0" cellspacing="0" summary="" style="table-layout:fixed;width:730;border: 5px solid #666666;padding-right: 0px;padding-left: 0px;padding-bottom: 0px;padding-top: 0px;margin-left : 10px;margin-top:10;background:#FFF7F0;">
                        <tr>
                        <td width=100%>
                        <div class="ds-contentcontainer">
                        <div style="margin-left:1.2em;">
                        <br>
 <img src="http://www.flossmanuals.net/pub/TWiki/FlossSkin2/objavib.gif">
                        <p>
			This is the BETA publisher for FLOSS Manuals. Using OBJAVI you can export your manual to print ready source for upload and sale on Lulu.com
</p><p>
All design is managed by CSS. You can alter the CSS in the below text box and the PDF will be formatted accordingly. </p><p>This site is for testing only. 
</p>

<br>
<br>
Choose Manual : 
<form action="" method="POST">

<select name="webName">
END

my @websList = TWiki::Func::getListOfWebs("user, public");

  my @websExclude = split /,/, TWiki::Func::getPreferencesValue( "REMIXWEBEXCLUDE", "Main");

foreach my $web (get_unique([\@websList, \@websExclude ])) {
    $htmlData .= '<option value="'.$web.'">'.$web.'</option>';
}


    $htmlData .= <<END;
</select>
<br/>
<br/>
Text for Title page :<br>
<input type="text" name="title" />
<br>
<br>
Header Text :<br>
<input type="text" name="header" />
<br><br>
License :
<br>
<input type="text" name="license" value="GPL"/>
<br><br>
ISBN Number (optional) :
<br>
<input type="text" name="isbn" />
<br>
<br>
CSS
<br>
<textarea name="css" cols="60" rows="20">
END

open(DT, "</var/www/floss/pub/TWiki/Pisa/fm-book.css");
 while(<DT>) {
   $htmlData .= $_;
  }
close(DT);

$htmlData .= <<END;
</textarea><br/>
<button>OBJAVI!</button>
</form>
</div></td></tr></table>
</body>
</html>
END


    print "Content-Type: text/html\r\n\r\n";
    print $htmlData;

}

sub _showHeading {
 my ($web, $num_heading, @chapters) = @_;

 my $htmlData = "";

 $htmlData .= "</div></fmsection><p></p>\n";

 my $n = 0;
 foreach my $a (@chapters) {
    my $topicData = TWiki::Func::readTopicText($web, $a);

    $topicData = TWiki::Func::expandCommonVariables($topicData, "neki topic", $web);
    $topicData = TWiki::Func::renderText($topicData, $web);
    my $s = '';

    foreach my $line (split(/\n/,$topicData)) {
#	if($line =~ /<h1>(.+)<\/h1>/) {
	if($line =~ /<h1>(.+)/) {
	    $s .= '<h1><span class="fminitial">'.($num_heading+$n).'.</span> '.$1.'';
	    $s .= "<br><br>";
	    $s .= "\n";
	    $n += 1;
	} else {
	    $line =~ s/%META:\w+{.*?}%//gs;
	    $line =~ s/src=\"/src=\"\/var\/www/gs;
	    $s .= $line."\n";
	}
   }

   my $filename;
   my $filename2;

   (undef, $filename) = tempfile("/tmp/objaviXXXXX", UNLINK => 0);
   (undef, $filename2) = tempfile("/tmp/objaviXXXXX", UNLINK => 0);

   open(DT, ">$filename");
   print DT $s;
   close(DT);

   my @args = ('/usr/bin/tidy', "-q", "-f", "/dev/null", "-o", "$filename2", "$filename");
   system(@args);

   my $s2 = "";

   open(DT, "<$filename2");
   while(<DT>) {
      $s2 .= $_;
   }
   close(DT);

   unlink($filename);
   unlink($filename2);

 #  if($s2 =~ /.*\<body\>(.+)\<\/body\>.*/) {
 #    $htmlData .= $1;
 #  } else   {
 #    $htmlData .= $s2;
 #  }

   $htmlData .= $s;

#   $n += 1;
  }

  return $htmlData;
}

sub handlePublish {
    my ($webName, $userName, $thePathInfo, $query) = @_;

    my $htmlData = "";

    #print "Content-type: text/plain\r\n\r\n";
    print "Content-type: application/pdf\r\nContent-Disposition: attachment; filename=\"fm.pdf\"\r\n\r\n";

    my $web     = $query->param("webName");
    my $customCss =$query->param("css");
    my $customTitle =$query->param("title");
    my $customHeader =$query->param("header");
    my $customISBN =$query->param("isbn");
    my $customLicense =$query->param("license");

    my $tocData = TWiki::Func::readAttachment( $web, "_index", "TOC.txt");
    my $current_heading = 1;
    my $num_heading = 0;

    my @lines = split /\n/, $tocData;
    my @chapters;

    for(my $i = 0; $i < (@lines/3); $i++) {
	  my $topicName   = $lines[$i*3+1];
	  my $description = $lines[$i*3+2];
	  my $topicID     = $lines[$i*3];

  	  if($topicID eq "0") {

	      if($current_heading+$num_heading != 1) {
	        $htmlData .= _showHeading($web, $current_heading, @chapters);
	        @chapters = ();

	         $current_heading = $current_heading + $num_heading;
	      }    


#	      $current_heading = $current_heading + $num_heading;

	      $num_heading = 0;

	      $htmlData .= "<fmsection>\n";
	      $htmlData .= '<h0>'.$description."</h0>\n";
	      $htmlData .= '<div class="fmtoc">';
	      $htmlData .= "\n";
	    
          } elsif($topicID eq "1") {
	        push @chapters, $topicName;
	        $htmlData .= ($current_heading+$num_heading).'. '.$description.'<br/>';
	        $htmlData .= "\n";
	        $num_heading += 1;
          }
    }

    $htmlData .= _showHeading($web, $current_heading, @chapters);

   my $tmpl = TWiki::Func::readTemplate("basic", "pisa");

   $tmpl =~ s/%%BODY%%/$htmlData/gs;
   $tmpl =~ s/%%STYLE%%/$customCss/gs;
   $tmpl =~ s/%%CUSTOMHEADER%%/$customHeader/gs;
   $tmpl =~ s/%%CUSTOMTITLE%%/$customTitle/gs;
   $tmpl =~ s/%%CUSTOMISBN%%/$customISBN/gs;
   $tmpl =~ s/%%CUSTOMLICENSE%%/$customLicense/gs;


   $tmpl = TWiki::Func::expandCommonVariables($tmpl, "neki topic", $web);
   $tmpl = TWiki::Func::renderText($tmpl, $web);

#   my $willchange=$TWiki::cfg{"InstallDirectory"}"; 
   my $willchange = "/var/www/floss";
   my (undef, $filename) = tempfile("$willchange/pub/TWiki/Pisa/objaviXXXXX", UNLINK => 0);

   open(FH, ">$filename");

   print FH $tmpl;

   close(FH);

   my @args = ('/var/www/floss/pub/TWiki/Pisa/objavi.sh', $filename);
   #my @args = ('/usr/bin/python2.4', 'pisa/pisa.py', "-x", $filename, "-" );
   #chdir("$willchange/pub/TWiki/Pisa/");
   system(@args) or print STDERR "couldn't exec pisa: $!";
# disabled for debugging - lf
#   unlink($filename);

#00:43 < fileneed> cd /var/www/floss_clean/pub/TWiki/Pisa
#00:43 < fileneed>  python2.4 pisa-3.0.19-fm/pisa.py -x index.xhtml

}

1;
