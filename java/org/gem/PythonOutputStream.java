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
        if (arg0 == '\n') {
            thispipe.write(buffer.toString());
            buffer = new StringBuilder();
        } else {
            buffer.append((char) arg0);
        }
    }
}
