# -*- coding: utf-8 -*-
"""HTML template to embed geotiffs of GMF maps."""

HTML_TEMPLATE_LOSSRATIO = """<!DOCTYPE html PUBLIC 
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
<th width="10%">Percentage</th>
</tr>
<tr>
<td bgcolor="#000000">&nbsp;</td><td>0-6</td>
</tr>
<tr>
<td bgcolor="#0f0000">&nbsp;</td><td>7-12</td>
</tr>
<tr>
<td bgcolor="#1f0000">&nbsp;</td><td>13-18</td>
</tr>
<tr>
<td bgcolor="#2f0000">&nbsp;</td><td>19-25</td>
</tr>
<tr>
<td bgcolor="#3f0000">&nbsp;</td><td>26-31</td>
</tr>
<tr>
<td bgcolor="#4f0000">&nbsp;</td><td>32-37</td>
</tr>
<tr>
<td bgcolor="#5f0000">&nbsp;</td><td>38-43</td>
</tr>
<tr>
<td bgcolor="#6f0000">&nbsp;</td><td>44-50</td>
</tr>
<tr>
<td bgcolor="#7f0000">&nbsp;</td><td>51-56</td>
</tr>
<tr>
<td bgcolor="#8f0000">&nbsp;</td><td>57-62</td>
</tr>
<tr>
<td bgcolor="#9f0000">&nbsp;</td><td>63-69</td>
</tr>
<tr>
<td bgcolor="#af0000">&nbsp;</td><td>70-75</td>
</tr>
<tr>
<td bgcolor="#bf0000">&nbsp;</td><td>76-81</td>
</tr>
<tr>
<td bgcolor="#cf0000">&nbsp;</td><td>82-87</td>
</tr>
<tr>
<td bgcolor="#df0000">&nbsp;</td><td>88-94</td>
</tr>
<tr>
<td bgcolor="#ef0000">&nbsp;</td><td>95-100</td>
</tr>
"""

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

def generate_html(path, width="", height="", template=HTML_TEMPLATE_GREENRED):
    """ Method takes an HTML template and returns the HTML with a GEOTIFF 
    linked """
    curr_html = template
    for (token, new_value) in (
        ('PLACEHOLDER_IMAGE_NAME', path), ('PLACEHOLDER_WIDTH', width),
        ('PLACEHOLDER_HEIGHT', height)):
        curr_html = curr_html.replace(token, new_value)
    return curr_html
    
