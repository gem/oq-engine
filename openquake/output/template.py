# -*- coding: utf-8 -*-
"""HTML template to embed geotiffs of GMF maps."""

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

def generate_html(path, width="", height="", colorscale=None, imt='PGA/g',
                  title=""):

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
    