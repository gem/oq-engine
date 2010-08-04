package org.opensha.sra.riskmaps;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;

public class BinaryHazardCurveReaderTest {
	
	public static final String DEFAULT_FILE_NAME = 
		"/Users/emartinez/Desktop/out.bin";
	
	public static void main(String [] args) throws Exception{
		String filename = null;
		if ( args.length > 0 ) { filename = args[0]; }
		else { filename = DEFAULT_FILE_NAME; }
		
		BinaryHazardCurveReader reader = new BinaryHazardCurveReader(filename);
		
		long start = System.currentTimeMillis();
		int i = 0;
		while ( reader.nextCurve() != null ) { i++; }
		long end = System.currentTimeMillis();
		
		//for ( int i = 0; i < 10; i++ ) {
			//ArbitrarilyDiscretizedFunc func = reader.nextCurve();
			//double [] loc = reader.currentLocation();
			
			//System.out.printf("Location: (%f, %f)\n", loc[0], loc[1]);
			//System.out.println(func);
		//}
		
		System.out.printf("Read %d curves in %d seconds.", i, (end - start) / 1000);
	}
}
