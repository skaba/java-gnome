<?php
#
# render.php
# Render a text document marked up with Markdown syntax as an HTML page. Based
# on view.php from web/local/markdown/
#
# Copyright (c) 2004-2007 Operational Dynamics Consulting Pty Ltd 
# 
# The code in this file, and the library it is a part of, are made available to
# you by the authors under the terms of the "GNU General Public Licence,
# version 2". See the LICENCE file for the terms governing usage and
# redistribution.
#


#
# parse the inbound URI. We have to go to some effort to get the translated
# path that we're working from.
#

	$filepath = substr($_SERVER["SCRIPT_FILENAME"], 0, -11);
	$filepath .= $_SERVER["REQUEST_URI"];


	if (substr($filepath, -5) == ".html") {
		$filepath = substr_replace($filepath, ".txt" ,-5);

		if (!file_exists($filepath)) {
			$filepath = substr($filepath, 0, -4);

			if (!file_exists($filepath)) {
				header("HTTP/1.1 404 Not Found");
				echo "<h1>404 Tried looking for your file, but no joy<h1>";
				exit;
			}
		}

		$title = substr_replace($_SERVER["REQUEST_URI"], "" ,-5);
		$title = substr($title, 1);

	} else {
		header("HTTP/1.1 404 Not Found");
		echo "<h1>404 for real</h1>";
		exit;
	}

#
# WARNING This is a workaround; we used to send HTTP/1.1 of course, but doing
# that here now causes SourceForge's web server to prepend garbage. Putting
# HTTP/1.0 here makes it work. Strangely, even with this, their web server
# actually sends HTTP/1.1. Morons.
#

	header("HTTP/1.0 200 OK");

#
# now, with the filename in hand, shlurp its contents and parse out the first
# line as title.
#

	$text = file_get_contents($filepath);

#
# and with that done, proceed with the site template
#

	require "template.inc";
?>
<html>
<head>
<?
	template_header();
?>
<title><?=$title?></title>
<meta name="author" content="Andrew Cowie">
</head>
<body>
<?
	template_begin();
?>
<h1 class="title"><?=$title?></h1>
<div class="bluepanel"></div>

<?
	include_once "markdown.php";
	include_once "smartypants.php";

	$text = preg_replace('/(FIXME|TODO)/', '<span class="highlight">${1}</span>', $text);

#
# And at last call Markdown, and post-process that result with SmartyPants
#

	echo SmartyPants(Markdown($text));


	$bottom_message = "This page was generated from a text document! We use
	John Gruber's Markdown syntax as ported to PHP by Michel Fortin. See <a
	class=\"black\" href=\"/doc/style/MARKUP.html\">MARKUP</a> for
	details";

	template_end();
?>
</body>
</html>
