package org.opensha.gem.GEM1.calc.gemCommandLineCalculator;

import java.io.IOException;
import java.lang.reflect.InvocationTargetException;

public class CommandLineCalculatorMain {

	/**
	 * @param args
	 * @throws IOException 
	 * @throws InvocationTargetException 
	 * @throws NoSuchMethodException 
	 * @throws IllegalAccessException 
	 * @throws InstantiationException 
	 * @throws ClassNotFoundException 
	 * @throws IllegalArgumentException 
	 * @throws SecurityException 
	 */
	public static void main(String[] args) throws IOException, SecurityException, IllegalArgumentException, ClassNotFoundException, InstantiationException, IllegalAccessException, NoSuchMethodException, InvocationTargetException {
		

		// define the command line calculator
		// at the moment the configuration file is assumed to be in the Data folder
		CommandLineCalculator clc = new CommandLineCalculator("CalculatorConfig.inp");
		
		// do the calculation
		clc.doCalculation();
		
		// exit
		System.exit(0);

	}

}
