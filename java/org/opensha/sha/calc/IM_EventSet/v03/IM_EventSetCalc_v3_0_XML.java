/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.sha.calc.IM_EventSet.v03;

import java.util.List;

import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.GnuParser;
import org.apache.commons.cli.HelpFormatter;
import org.apache.commons.cli.MissingOptionException;
import org.apache.commons.cli.Option;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;

public class IM_EventSetCalc_v3_0_XML {
	
//	public IM_EventSetCalc_v3_0(EqkRupForecastBaseAPI erf, ArrayList) {
//		
//	}
	
	
	/**
	 * This creates the command line options for use by apache commons cli
	 * 
	 * @return
	 */
	private static Options createOptions() {
		Options ops = new Options();
		
		// the 3rd argument (boolean) to all of these Option constructors is 'hasarg'
		
		// ERF
		Option erf = new Option("e", "erf", true, "ERF XML File");
		erf.setArgName("erf.xml");
		erf.setRequired(true);
		ops.addOption(erf);
		
		// Atten Rel(s)
		Option atten = new Option("a", "atten-rel", true, "Attenuation Relationship XML File(s)");
		atten.setArgName("atten1.xml[,atten2.xml,...]");
		atten.setRequired(true);
		ops.addOption(atten);
		
		// IMT(s)
		Option imt = new Option("i", "imt", true, "Intensity Measure Type(s)");
		imt.setArgName("IMT1[,IMT2,...]");
		imt.setRequired(true);
		ops.addOption(imt);
		
		// IMT(s)
		Option sites = new Option("s", "sites", true, "Sites to perform calculation");
		sites.setArgName("sites.txt");
		sites.setRequired(true);
		ops.addOption(sites);
		
		return ops;
	}
	
	public static void printHelp(Options options) {
		HelpFormatter formatter = new HelpFormatter();
		formatter.printHelp( "IM_EventSetCalc_v3_0", options, true );
		System.exit(2);
	}

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		Options options = createOptions();
		
		CommandLineParser parser = new GnuParser();
		
		try {
			CommandLine cmd = parser.parse( options, args);
		} catch (MissingOptionException e) {
			List<String> missings = e.getMissingOptions();
			String missStr = null;
			for (String missing : missings) {
				if (missStr == null)
					missStr = "";
				else
					missStr += ", ";
				missStr += missing;
			}
			e.printStackTrace();
			System.err.println("Missing " + missings.size() + " missing options: " + missStr);
			printHelp(options);
		} catch (ParseException e) {
			e.printStackTrace();
			System.err.println("Error parsing command line options! (see above stack trace)");
			System.exit(2);
		}
	}

}
