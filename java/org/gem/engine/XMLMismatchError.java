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

package org.gem.engine;

import org.dom4j.DocumentException;

/**
 * Unexpected document type during parsing
 */
public class XMLMismatchError extends RuntimeException {
    private String fileName, actualTag, expectedTag;

    public XMLMismatchError(String fileName, String actualTag,
                            String expectedTag) {
        this.fileName = fileName;
        this.actualTag = actualTag;
        this.expectedTag = expectedTag;
    }

    /** The full path of the invalid file */
    public String getFileName() {
        return fileName;
    }

    /** Main tag of the document (first child of the NRML tag) */
    public String getActualTag() {
        return actualTag;
    }

    /** Expected main tag of the document (first child of the NRML tag) */
    public String getExpectedTag() {
        return expectedTag;
    }
}
