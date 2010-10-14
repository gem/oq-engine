package org.gem.engine.hazard.parsers.nshmp;

import java.io.DataInputStream;
import java.io.EOFException;
import java.io.FileInputStream;
import java.io.IOException;
import java.net.URL;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

/**
 * 
 * @author damianomonelli
 * 
 *         This class reads input matrix file (for weights, b value, maximum
 *         magnitude)
 * 
 */

public class ReadBinaryInputMatrix {

    public static Map<String, ArrayList<Double>> oldVals;

    ArrayList<Double> val;

    // constructor
    public ReadBinaryInputMatrix(String filename, boolean bigEndian2LittleEndian)
            throws IOException {

        if (oldVals == null) {
            oldVals = new HashMap<String, ArrayList<Double>>();
        } else {
            ArrayList<Double> cachedVal = oldVals.get(filename);
            if (cachedVal != null) {
                val = cachedVal;
                System.out.println("Using cached binary file data...");
                return;
            }
        }

        val = new ArrayList<Double>();
        // filename MUST BE absolute path!!
        DataInputStream data_in =
                new DataInputStream(new FileInputStream(filename));

        int index = 0;
        while (true) {
            try {
                // the conversion from big endian to little endian
                // is done because the fortran code saves
                // values in a little-endian format but the java
                // VM works with big-endian format
                ByteBuffer buf = ByteBuffer.allocate(4);
                buf.order(ByteOrder.BIG_ENDIAN);
                buf.putFloat(0, data_in.readFloat());
                if (bigEndian2LittleEndian) {
                    buf.order(ByteOrder.LITTLE_ENDIAN);
                }
                val.add(index, (double) buf.getFloat(0));
                index = index + 1;
            } catch (EOFException eof) {
                System.out.println("End of File");
                break;
            }
        }
        data_in.close();
        oldVals.put(filename, val);
    }

    public ArrayList<Double> getVal() {
        return val;
    }

}
