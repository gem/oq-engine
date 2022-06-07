#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (c) 2022, GEM Foundation.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.
# If not, see <https://www.gnu.org/licenses/agpl.html>.
#
import fileinput
import re


def process(line):
    # Search for lines like " .2ex " and extract section header
    m = re.search(r'(.* \.\dex) (.*)$', line)
    if(m is None):
        print(line)
    else:
        codes = m.group(1)
        section = m.group(2)
        if(codes == '-3ex -0.1ex -.4ex 0.5ex .2ex'):
            uline_char = '~'
        elif(codes == '-4ex -1ex -.4ex 1ex .2ex'):
            uline_char = '^'
        elif(codes == '-2ex -.2ex .2ex .1ex'):
            uline_char = ':'
        else:
            uline_char = '_'
        print(section)
        print(''.join([uline_char] * len(section)))


def main():
    for line in fileinput.input():
        process(line.rstrip())


if __name__ == "__main__":
    main()
