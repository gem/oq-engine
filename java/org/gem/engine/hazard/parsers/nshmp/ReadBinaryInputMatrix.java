package org.gem.engine.hazard.parsers.nshmp;


import java.io.DataInputStream;
import java.io.EOFException;
import java.io.FileInputStream;
import java.io.IOException;
import java.net.URL;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;

/**
 * 
 * @author damianomonelli
 *
 * This class reads input matrix file (for weights, b value, maximum magnitude)
 *
 */

public class ReadBinaryInputMatrix {
	
    ArrayList<Double> val;
	
	// constructor
	public ReadBinaryInputMatrix(String filename, boolean bigEndian2LittleEndian) throws IOException{

        val = new ArrayList<Double>();
        
		DataInputStream data_in    = new DataInputStream (new FileInputStream(this.getClass().getClassLoader().getResource(filename).getPath()));


	      int index = 0;
	      while (true) {
	        try {
	        	// the conversion from big endian to little endian
	        	// is done because the fortran code saves
	        	// values in a little-endian format but the java
	        	// VM works with big-endian format
	            ByteBuffer buf = ByteBuffer.allocate(4);  
	            buf.order(ByteOrder.BIG_ENDIAN); 
	            buf.putFloat(0,data_in.readFloat());
	            if(bigEndian2LittleEndian){
		            buf.order(ByteOrder.LITTLE_ENDIAN);
	            }
	            val.add(index,(double)buf.getFloat(0));
	            index = index+1;
	        }
	        catch (EOFException eof) {
	          System.out.println ("End of File");
	          break;
	        }
	      }
	      data_in.close();
        
	}
	
	public ArrayList<Double> getVal(){
		return val;
	}

}
