/*
    Copyright (c) 2010-2012, GEM Foundation.

    OpenQuake is free software: you can redistribute it and/or modify it
    under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    OpenQuake is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
*/

package org.gem;

import java.io.IOException;
import java.io.OutputStream;

public class PythonOutputStream extends OutputStream {
    private IPythonPipe thispipe;
    private StringBuilder buffer;

    public void setPythonStdout(IPythonPipe mypipe) {
        thispipe = mypipe;
        buffer = new StringBuilder();
    }

    @Override
    public void write(int arg0) throws IOException {
        buffer.append((char) arg0);
        if (arg0 == '\n') {
            thispipe.write(buffer.toString());
            buffer = new StringBuilder();
        }
    }
}
