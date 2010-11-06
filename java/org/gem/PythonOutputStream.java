package org.gem;

import java.io.IOException;
import java.io.OutputStream;

public class PythonOutputStream extends OutputStream {
    private IPythonPipe thispipe;

    public void setPythonStdout(IPythonPipe mypipe) {
        thispipe = mypipe;
    }

    @Override
    public void write(int arg0) throws IOException {
        // TODO Auto-generated method stub
        thispipe.write((char) arg0);

    }

}
