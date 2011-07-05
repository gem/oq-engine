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
