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

package org.gem.engine.risk.io.reader;

/**
 * A simple decorator that takes into account files with header lines to skip.
 * 
 * @author Andrea Cerisara
 * @version $Id: HeaderLineReader.java 537 2010-06-16 18:29:36Z acerisara $
 */
public class HeaderLineReader implements LineReader
{

    private final LineReader reader;
    private final int headerLinesToSkip;

    /**
     * @param headerLinesToSkip the number of header lines to skip
     * @param reader the decorated reader
     */
    public HeaderLineReader(int headerLinesToSkip, LineReader reader)
    {
        this.reader = reader;
        this.headerLinesToSkip = headerLinesToSkip;
    }

    @Override
    public String[] readAndSplit(int row, String delimiter)
    {
        return reader.readAndSplit(row + headerLinesToSkip, delimiter);
    }

}
