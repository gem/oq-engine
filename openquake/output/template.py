# -*- coding: utf-8 -*-
"""HTML template to embed geotiffs of GMF maps."""

HTML_TEMPLATE_GREENRED = """<!DOCTYPE html PUBLIC 
    "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html lang="en-US" xml:lang="en-US" xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>GMF</title>
</head>
<body>
<center>
<img width="PLACEHOLDER_WIDTH" height="PLACEHOLDER_HEIGHT" 
    src="PLACEHOLDER_IMAGE_NAME" type="image/tiff" negative="yes"/>
<br/>
<table cellspacing="0" border="1" width="20%">
<tr>
<th width="10%">Color</th>
<th width="10%">PGA/g</th>
</tr>
<tr>
<td bgcolor="#00FF00">&nbsp;</td>
<td>0.0</td>
</tr>
<tr>
<td bgcolor="#0FF00">&nbsp;</td>
<td>0.125</td>
</tr>
<tr>
<td bgcolor="#1FE000">&nbsp;</td>
<td>0.25</td>
</tr>
<tr>
<td bgcolor="#2FD000">&nbsp;</td>
<td>0.375</td>
</tr>
<tr>
<td bgcolor="#3FC000">&nbsp;</td>
<td>0.5</td>
</tr>
<tr>
<td bgcolor="#4FB000">&nbsp;</td>
<td>0.625</td>
</tr>
<tr>
<td bgcolor="#5FA000">&nbsp;</td>
<td>0.75</td>
</tr>
<tr>
<td bgcolor="#6F9000">&nbsp;</td>
<td>0.875</td>
</tr>
<tr>
<td bgcolor="#7F8000">&nbsp;</td>
<td>1.0</td>
</tr>
<tr>
<td bgcolor="#8F7000">&nbsp;</td>
<td>1.125</td>
</tr>
<tr>
<td bgcolor="#9F6000">&nbsp;</td>
<td>1.25</td>
</tr>
<tr>
<td bgcolor="#AF5000">&nbsp;</td>
<td>1.375</td>
</tr>
<tr>
<td bgcolor="#BF4000">&nbsp;</td>
<td>1.5</td>
</tr>
<tr>
<td bgcolor="#CF3000">&nbsp;</td>
<td>1.625</td>
</tr>
<tr>
<td bgcolor="#DF2000">&nbsp;</td>
<td>1.75</td>
</tr>
<tr>
<td bgcolor="#EF1000">&nbsp;</td>
<td>1.875</td>
</tr>
<tr>
<td bgcolor="#FF0000">&nbsp;</td>
<td>2.0</td>
</tr>
</table>
<br/>
</center>
</body>
</html>
"""

def generate_html(path, width="", height=""):
    curr_html = HTML_TEMPLATE_GREENRED
    for (token, new_value) in (
        ('PLACEHOLDER_IMAGE_NAME', path), ('PLACEHOLDER_WIDTH', width),
        ('PLACEHOLDER_HEIGHT', height)):
        curr_html = curr_html.replace(token, new_value)
    return curr_html
    