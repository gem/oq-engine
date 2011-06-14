package org.gem.engine;

import org.dom4j.DocumentException;

/**
 * Unexpected document type during parsing
 */
public class XMLMismatchError extends RuntimeException {
    private String fileName, actualTag, expectedTag;

    public XMLMismatchError(String file, String actual_tag,
                            String expected_tag) {
        fileName = file;
        actualTag = actual_tag;
        expectedTag = expected_tag;
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
