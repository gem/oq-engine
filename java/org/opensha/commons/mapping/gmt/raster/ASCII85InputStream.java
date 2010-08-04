/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.commons.mapping.gmt.raster;

//modified from: Copyright 2001, FreeHEP.

import java.io.IOException;
import java.io.InputStream;

/**
 * The ASCII85InputStream decodes ASCII base-85 encoded data.
 * The exact definition of ASCII base-85 encoding can be found
 * in the PostScript Language Reference (3rd ed.) chapter 3.13.3.
 *
 * IMPORTANT: inherits from InputStream rather than FilterInputStream
 * so that the correct read(byte[], int, int) method is used.
 *
 * @author Mark Donszelmann
 * @version $Id: ASCII85InputStream.java 5941 2009-10-12 20:38:15Z pmpowers $
 */
public class ASCII85InputStream extends InputStream {
	
    public final static int MAX_CHARS_PER_LINE = 80;
    
    public static long a85p1 = 85;
    public static long a85p2 = a85p1*a85p1;
    public static long a85p3 = a85p2*a85p1;
    public static long a85p4 = a85p3*a85p1;

    private boolean endReached;
    private int b[] = new int[4];
    private int bIndex;
    private int bLength;
    private int c[] = new int[5];
    private int lineNo;
    private int prev;
    private InputStream in;

    public ASCII85InputStream(InputStream input) {
        super();
        in = input;
        bIndex = 0;
        bLength = 0;
        endReached = false;
        prev = -1;
        lineNo = 1;
    }

    public int read() throws IOException {

        if (bIndex >= bLength) {
            if (endReached) return -1;
            bLength = readTuple();
            if (bLength < 0) return -1;
            bIndex = 0;
        }
        int a = b[bIndex];
        bIndex++;

        return a;
    }
    
    public boolean isEndReached() {
    	return endReached;
    }

    public int getLineNo() {
        return lineNo;
    }

    private int readTuple() throws IOException,  RuntimeException {
        int cIndex = 0;
        int ch = -1;
        while ((!endReached) && (cIndex<5)) {
            prev = ch;
            ch = in.read();
            switch (ch) {
                case -1:
                    throw new RuntimeException("missing '~>' at end of ASCII85 stream");
                case 'z':
                    b[0] = b[1] = b[2] = b[3] = '!';
                    return 4;
                case '~':
                    if (in.read() != '>') throw new RuntimeException("Invalid ASCII85 EOD");
                    endReached = true;
                    break;
                case '\r':
                    lineNo++;
                    break;
                case '\n':
                    if (prev != '\r') {
                        lineNo++;
                    }
                    break;
                case ' ':
                case '\t':
                case '\f':
                case 0:
                    // ignored
                    break;
                default:
                    c[cIndex] = ch;
                    cIndex++;
                    break;
            }
        }

        if (cIndex > 0) {
            // fill the rest
            for (int i=0; i<c.length; i++) {
                if (i >= cIndex) {
                    c[i] = '!';
                } else {
                    c[i] -= '!';
                }
            }

            // convert
            long d = ((c[0] * a85p4) + (c[1] * a85p3) + (c[2] * a85p2) + (c[3] * a85p1) + c[4]) & 0x00000000FFFFFFFFL;

            b[0] = (int)((d >> 24) & 0x00FF);
            b[1] = (int)((d >> 16) & 0x00FF);
            b[2] = (int)((d >> 8)  & 0x00FF);
            b[3] = (int)( d        & 0x00FF);
        }
        return cIndex-1;
    }
}
