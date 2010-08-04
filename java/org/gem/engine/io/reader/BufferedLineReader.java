/*
 * [COPYRIGHT]
 *
 * [NAME] is free software; you can redistribute it and/or modify it
 * under the terms of the GNU Lesser General Public License as
 * published by the Free Software Foundation; either version 2.1 of
 * the License, or (at your option) any later version.
 *
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this software; if not, write to the Free
 * Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
 * 02110-1301 USA, or see the FSF site: http://www.fsf.org.
 */

package org.gem.engine.io.reader;

import java.util.ArrayList;
import java.util.List;

/**
 * A simple decorator that adds buffering logic.
 * 
 * @author Andrea Cerisara
 * @version $Id: BufferedLineReader.java 537 2010-06-16 18:29:36Z acerisara $
 */
public class BufferedLineReader implements LineReader
{

    private int offSet;
    private boolean bufferEmpty;
    private final int linesToCache;

    private List<String[]> lines;
    private final LineReader reader;

    /**
     * @param reader the decorated reader
     * @param linesToCache the number of lines to read and cache
     */
    public BufferedLineReader(LineReader reader, int linesToCache)
    {
        this.reader = reader;
        this.bufferEmpty = true;
        this.linesToCache = linesToCache;
    }

    @Override
    public String[] readAndSplit(int row, String delimiter)
    {
        if (bufferNeedsUpdate(row))
        {
            updateBuffer(row, delimiter);
        }

        return lines.get(row - 1 - offSet);
    }

    private boolean bufferNeedsUpdate(int row)
    {
        return row < offSet || row > (offSet + (bufferEmpty ? 0 : linesToCache));
    }

    private void updateBuffer(int row, String delimiter)
    {
        offSet = row - 1;
        bufferEmpty = false;
        readLines(row, delimiter);
    }

    private void readLines(int row, String delimiter)
    {
        lines = new ArrayList<String[]>();

        for (int i = 0; i < linesToCache; i++)
        {
            String[] line = reader.readAndSplit(row++, delimiter);

            if (line != null)
            {
                lines.add(line);
            }
        }
    }

}
