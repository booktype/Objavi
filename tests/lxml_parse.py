#!/usr/bin/python

html2 ="""
<html xmlns="http://www.w3.org/1999/xhtml"><head>
<title>Gimp: Help</title>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type">
</head>
<body>
<h1>More Help
</h1>
<p>For more help with GIMP you can try these avenues:
</p>
<h2>GIMP Documentation&#160;
</h2>
<p>should first look at the very good documentation at the developers site:
</p>
<p><!--
Copyright (c)  14 May 2006  AdamHyde
Permission is granted to copy, distribute and/or modify this document
under the terms of the GNU Free Documentation License, Version 1.2
or any later version published by the Free Software Foundation.
<p />
For a full text of the licence please see:
<a href="http://www.gnu.org/licenses/fdl.txt" target="_top">http://www.gnu.org/licenses/fdl.txt</a>
-->
</p>
<p> link
  <br>
</p>
<h2>GIMP Tutorials
</h2>
<p><a href="http://www.gimpguru.org/Tutorials/" target="_blank">http://www.gimpguru.org/Tutorials/&#160;</a>
</p>
<p><a href="http://gug.sunsite.dk/" target="_blank">http://gug.sunsite.dk/</a>
  <br>
</p>
<p><a href="http://www.gimp-tutorials.com/" target="_blank">http://www.gimp-tutorials.com/</a>
</p>
<p><a href="http://www.gimp-tutorials.com/" target="_blank"></a><a href="http://gimpology.com/" target="_blank">http://gimpology.com/</a>
</p>
<p><a href="http://gimpology.com/" target="_blank"></a><a href="http://gimp-savvy.com/" target="_blank">http://gimp-savvy.com/</a>
  <br>
</p>
<h2>Online Forums&#160;
</h2>
<p>You can also try searching through the forums for information. &#160;
</p>
<p>link
</p>
<p>The forums contain a lot of postings from users on many topics. You can use the search system to locate topics or just browse the categories. If you don't find what you want then try subscribing to the forums and posting your question to the relevant category. There are a few things to keep in mind when asking a question in a forum or to a mailing list. First, be as clear as you can with your question and provide any information that you might think would help some to try to help you. You might, for example, include information about the operating system you are using, or various specifics that relate to what you are trying to achieve. Additionally, it is always good practice to also post back to any forum or mailing list if you manage to solve your query and include clear information on how you solved the puzzle. This is so that someone else that may have the same issue can resolve it using what you have found out. If possible post back to the same thread (discussion topic) so that anyone searching through the forum can follow the discussion including the solution.
</p>
<h2><strong>Web Search</strong>
</h2>
<p>Searching the web is always useful. If you are looking for problems arising from errors reported by the software then try entering the error text into the search engine. Be sure to edit out any information that doesn't look generic when doing this. Some search engines also enable you to try searches of mailing lists, online groups etc, this can also provide good results.<strong>
  <br></strong>
</p>
<h2>Mailing Lists
</h2>
<p>Mailing lists are good places to look through for answers to questions. The archives are located here :
</p>
<p>link
</p>
<p>You can browse the archives (although this can take a while). You can also subscribe to the mailing lists and ask a question:
</p>
<p>link
</p>
<p>Please note the suggestions about posting to forums and mailing lists in the above section.
</p>
<h2><strong>IRC</strong>
</h2>
<p><strong>IRC</strong> is a type of online chat. it is not the easiest to use if you are not familiar with it but it is a very good system. There are a variety of softwares for all operating systems that enable you to use <strong>IRC</strong>. The <strong>IRC</strong> channel is where a number of the developers are online and some 'superusers'. So logging into this channel can be useful but it is very important that you know exactly what you are trying to find out before trying this route. The protocol for using the channel is jus tot log in, and ask the question immediately. Don't try and be too chatty as you are probably going to be ignored. It is also preferable if you have done some research using the other methods above before trying the channel. The details for the <strong>IRC</strong> channel are:
</p>
<p>
</p>
<ul>
  <li>IRC network: <code>detail</code> </li>
  <li>Channel: <code>#detail</code>
  <br> </li>
</ul>


</body></html>
"""


html ="""
<html><body>
<!-- a comment -->
</body></html>
"""

import lxml, lxml.html, lxml.html.clean
from lxml.html import html5parser
tree = lxml.html.document_fromstring(html)
tree = html5parser.document_fromstring(html)

cleaner = lxml.html.clean.Cleaner(scripts=True,
                                  javascript=True,
                                  comments=False,
                                  style=True,
                                  links=True,
                                  meta=True,
                                  page_structure=False,
                                  processing_instructions=True,
                                  embedded=True,
                                  frames=True,
                                  forms=True,
                                  annoying_tags=True,
                                  #allow_tags=OK_TAGS,
                                  remove_unknown_tags=True,
                                  safe_attrs_only=True,
                                  add_nofollow=False
                                  )

#cleaner = lxml.html.clean.Cleaner()

cleaner(tree)

