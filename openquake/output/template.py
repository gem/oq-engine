# -*- coding: utf-8 -*-
"""HTML template to embed geotiffs of GMF/Loss Ratio maps."""

HTML_TEMPLATE_LOSSRATIO = """<!DOCTYPE html PUBLIC 
    "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html lang="en-US" xml:lang="en-US" xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>Loss Ratio</title>
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

HTML_TEMPLATE_HEADER = """<!DOCTYPE html PUBLIC
    "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html lang="en-US" xml:lang="en-US" xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>PLACEHOLDER_TITLE</title>
</head>
<body>
<center>
"""

HTML_TEMPLATE_IMAGE = """
<img width="PLACEHOLDER_WIDTH" height="PLACEHOLDER_HEIGHT" 
    src="PLACEHOLDER_IMAGE_NAME" type="image/tiff" negative="yes"/>
"""

HTML_TEMPLATE_TABLE_START = """
<br/>
<table cellspacing="0" border="1" width="20%">
<tr>
<th width="10%">Color</th>
<th width="10%">PLACEHOLDER_IMT</th>
</tr>
"""

HTML_TEMPLATE_FOOTER = """
</table>
<br/>
</center>
</body>
</html>
"""

HTML_TEMPLATE_TABLE_ROW = """
<tr>
<td bgcolor="PLACEHOLDER_COLOR_HEX_CODE">&nbsp;</td>
<td>PLACEHOLDER_IML_VALUE</td>
</tr>
"""

def generate_html(path, width="", height="", # pylint: disable=R0913,R0914
                  colorscale=None, imt='PGA/g',
                  title="", template=None):
    """This function creates an HTML page with a Geotiff image linked, and a 
    colorscale as HTML table. The HTML can be created from an explicitly 
    given template, or automatically based on color scale values."""

    if template is None:
        curr_html = HTML_TEMPLATE_HEADER
        header_html = curr_html.replace('PLACEHOLDER_TITLE', title)

        curr_html = HTML_TEMPLATE_IMAGE
        curr_html = curr_html.replace('PLACEHOLDER_IMAGE_NAME', path)
        curr_html = curr_html.replace('PLACEHOLDER_WIDTH', width)
        curr_html = curr_html.replace('PLACEHOLDER_HEIGHT', height)
        image_html = curr_html

        curr_html = HTML_TEMPLATE_TABLE_START 
        table_start_html = curr_html.replace('PLACEHOLDER_IMT', imt)

        table_body_html = '' 
        for curr_color in colorscale:
            curr_row_html = HTML_TEMPLATE_TABLE_ROW
            curr_row_html = curr_row_html.replace('PLACEHOLDER_COLOR_HEX_CODE', 
                                                curr_color[0])
            curr_row_html = curr_row_html.replace('PLACEHOLDER_IML_VALUE', 
                                                curr_color[1])
            table_body_html += curr_row_html

        return ''.join((header_html, image_html, table_start_html, 
                        table_body_html, HTML_TEMPLATE_FOOTER))
    else:
        curr_html = template
        for (token, new_value) in (
            ('PLACEHOLDER_IMAGE_NAME', path), ('PLACEHOLDER_WIDTH', width),
            ('PLACEHOLDER_HEIGHT', height)):
            curr_html = curr_html.replace(token, new_value)
        return curr_html
