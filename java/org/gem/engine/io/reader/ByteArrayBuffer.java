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

import java.io.IOException;
import java.io.InputStream;

class ByteArrayBuffer
{

    private static final int CACHE_SIZE_IN_BYTES = 1024 * 1024;

    private byte[] buffer;
    private boolean isEmpty;

    public ByteArrayBuffer()
    {
        this.isEmpty = true;
        this.buffer = new byte[CACHE_SIZE_IN_BYTES];
    }

    public double doubleAt(int index)
    {
        return fromMSBToLSB(index);
    }

    public int size()
    {
        return CACHE_SIZE_IN_BYTES;
    }

    public void fillBuffer(InputStream inputStream)
    {
        try
        {
            isEmpty = false;
            inputStream.read(buffer, 0, CACHE_SIZE_IN_BYTES);
        }
        catch (IOException e)
        {
            throw new RuntimeException(e);
        }
    }

    public boolean isEmpty()
    {
        return isEmpty;
    }

    private float fromMSBToLSB(int index)
    {
        int accum = 0;

        for (int shiftBy = 0, k = index; shiftBy < 32; shiftBy += 8, k++)
        {
            accum |= (buffer[k] & 0xff) << shiftBy;
        }

        return Float.intBitsToFloat(accum);
    }

}
