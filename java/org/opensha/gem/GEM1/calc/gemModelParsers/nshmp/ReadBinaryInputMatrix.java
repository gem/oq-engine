package org.opensha.gem.GEM1.calc.gemModelParsers.nshmp;


import java.io.BufferedReader;
import java.io.DataInputStream;
import java.io.EOFException;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.URL;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;

import org.opensha.gem.GEM1.calc.gemHazardCalculator.GemComputeHazardLogicTree;


/**
 * 
 * @author damianomonelli
 *
 * This class reads input matrix file (for weights, b value, maximum magnitude)
 *
 */

public class ReadBinaryInputMatrix {
	
	private final static boolean D = false;	// for debugging
	
    ArrayList<Double> val;
	
	// constructor
	public ReadBinaryInputMatrix(String filename, boolean bigEndian2LittleEndian) throws IOException{

        val = new ArrayList<Double>();
		
//        // Get a handle to the input file
//	    URL data = GemComputeHazardLogicTree.class.getResource(filename);
//	    File file = new File(data.getFile());
//        FileInputStream oFIS = null;
//		try {
//			//oFIS = new FileInputStream(filename);
//			oFIS = new FileInputStream(file.getPath());
//		} catch (FileNotFoundException e) {
//			e.printStackTrace();
//		}
//		
//	      DataInputStream data_in    = new DataInputStream (oFIS);
		
//		String myClass = '/'+getClass().getName().replace('.', '/')+".class";
//		URL myClassURL = getClass().getResource(myClass);
//		if ("jar" == myClassURL.getProtocol())
//		{
//			filename = filename.substring(filename.lastIndexOf("./")+1);
//		}
        //BufferedReader oReader = new BufferedReader(new InputStreamReader(GemComputeHazardLogicTree.class.getResourceAsStream(filename)));
        
		DataInputStream data_in    = new DataInputStream (GemComputeHazardLogicTree.class.getResourceAsStream(filename));


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
	          if (D) System.out.println ("End of File");
	          break;
	        }
	      }
	      data_in.close();
        
	}
	
	public ArrayList<Double> getVal(){
		return val;
	}

}
