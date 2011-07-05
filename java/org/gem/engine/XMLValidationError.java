package org.gem.engine;

import org.dom4j.DocumentException;

/**
 * Trivial Exception subclass with additional information for
 * error reporting.
 */
public class XMLValidationError extends RuntimeException {
    private String fileName;

    public XMLValidationError(String fileName, DocumentException cause) {
        super(cause);

        this.fileName = fileName;
    }

    /** The full path of the invalid file */
    public String getFileName() {
        return fileName;
    }
}
