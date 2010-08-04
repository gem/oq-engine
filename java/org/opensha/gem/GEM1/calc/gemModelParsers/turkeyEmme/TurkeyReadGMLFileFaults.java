package org.opensha.gem.GEM1.calc.gemModelParsers.turkeyEmme;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;

public class TurkeyReadGMLFileFaults {
	
	private ArrayList<String> code;
	private ArrayList<String> name;
	private ArrayList<LocationList> coords;
	
	/**
	 * Constructor
	 */
	public TurkeyReadGMLFileFaults(BufferedReader input) {
		int i;
		String sCurrentLine;
		String stringa;
		Matcher match;
		String[] strarr;	
		Double coo[][];
		double tmpLo, tmpLa;
		LocationList lol; 
		boolean info = false;
		
		// Define patterns
		Pattern NAMEPATT    = Pattern.compile("^<fme:NAME>(.+)</fme:NAME>");
		Pattern FAULTPATT   = Pattern.compile("^<fme:FAULT_NAME>(.+)</fme:FAULT_NAME>");
		Pattern COORTPATT   = Pattern.compile("^<gml:posList>(.+)</gml:posList>");
		
		// Initialize
		this.setCode(new ArrayList<String>());
		this.setName(new ArrayList<String>());
		this.setCoords(new ArrayList<LocationList>());
		
		// Reading the file
	    try {
	    	// Instantiate a BufferedReader
//	    	BufferedReader input =  new BufferedReader(new FileReader(fleName));
	    	// Try to read file
	    	try {	
	    	
	    		// Cycle over lines
	    		while ((sCurrentLine = input.readLine()) != null) {
	    			
	    			// Search codes
	    			match = NAMEPATT.matcher(sCurrentLine);
		    		if (match.find()) {
		    			this.getCode().add(match.group(1));
		    			if (info) System.out.println(match.group(1));
		    		}
		    		
		    		// Search names
		    		match = FAULTPATT.matcher(sCurrentLine);
		    		if (match.find()) {
		    			this.getName().add(match.group(1));
		    			if (info) System.out.println("  "+match.group(1));
		    		}
		  
		    		// Coordinates
		    		match = COORTPATT.matcher(sCurrentLine);
		    		if (match.find()) {
		    			stringa = match.group(1); stringa = stringa.trim(); strarr = stringa.split("\\s+");
		    			// Find the number of rows 
		    			int nrow = Math.round(strarr.length/2);
		    			coo = new Double[nrow][2];
		    			// Reading coordinates
		    			int cli = 0;
		    			lol = new LocationList();
		    			for (i=0; i < strarr.length; i = i + 2){
		    				if (info) System.out.printf("%s %s\n",strarr[i],strarr[i+1]);
		    				// Add a location <lat,lon>
		    				tmpLa = Double.valueOf(strarr[i]).doubleValue();
		    				tmpLo = Double.valueOf(strarr[i+1]).doubleValue();
		    				Location loc = new Location(tmpLa,tmpLo);
		    				lol.add(loc);
		    			}
		    			this.getCoords().add(lol);
		    		}	
	    		}
	    		
	    	} finally {
		    	input.close();
	    	}
    	} catch (FileNotFoundException e) {
    	      e.printStackTrace();
    	} catch (IOException e) {
    	      e.printStackTrace();
    	} 
	}
	
	/**
	 * Constructor
	 */
	public TurkeyReadGMLFileFaults(String filename) {
		int i;
		String sCurrentLine;
		String stringa;
		Matcher match;
		String[] strarr;	
		Double coo[][];
		double tmpLo, tmpLa;
		LocationList lol; 
		boolean info = false;
		
		// Define patterns
		Pattern NAMEPATT    = Pattern.compile("^<fme:NAME>(.+)</fme:NAME>");
		Pattern FAULTPATT   = Pattern.compile("^<fme:FAULT_NAME>(.+)</fme:FAULT_NAME>");
		Pattern COORTPATT   = Pattern.compile("^<gml:posList>(.+)</gml:posList>");
		
		// Initialize
		this.setCode(new ArrayList<String>());
		this.setName(new ArrayList<String>());
		this.setCoords(new ArrayList<LocationList>());
		
		// Reading the file
	    try {
	    	// Instantiate a BufferedReader
	    	BufferedReader input =  new BufferedReader(new FileReader(filename));
	    	// Try to read file
	    	try {	
	    	
	    		// Cycle over lines
	    		while ((sCurrentLine = input.readLine()) != null) {
	    			
	    			// Search codes
	    			match = NAMEPATT.matcher(sCurrentLine);
		    		if (match.find()) {
		    			this.getCode().add(match.group(1));
		    			if (info) System.out.println(match.group(1));
		    		}
		    		
		    		// Search names
		    		match = FAULTPATT.matcher(sCurrentLine);
		    		if (match.find()) {
		    			this.getName().add(match.group(1));
		    			if (info) System.out.println("  "+match.group(1));
		    		}
		  
		    		// Coordinates
		    		match = COORTPATT.matcher(sCurrentLine);
		    		if (match.find()) {
		    			stringa = match.group(1); stringa = stringa.trim(); strarr = stringa.split("\\s+");
		    			// Find the number of rows 
		    			int nrow = Math.round(strarr.length/2);
		    			coo = new Double[nrow][2];
		    			// Reading coordinates
		    			int cli = 0;
		    			lol = new LocationList();
		    			for (i=0; i < strarr.length; i = i + 2){
		    				if (info) System.out.printf("%s %s\n",strarr[i],strarr[i+1]);
		    				// Add a location <lat,lon>
		    				tmpLa = Double.valueOf(strarr[i]).doubleValue();
		    				tmpLo = Double.valueOf(strarr[i+1]).doubleValue();
		    				Location loc = new Location(tmpLa,tmpLo);
		    				lol.add(loc);
		    			}
		    			this.getCoords().add(lol);
		    		}	
	    		}

	    		
	    		
	    	} finally {
		    	input.close();
	    	}
    	} catch (FileNotFoundException e) {
    	      e.printStackTrace();
    	} catch (IOException e) {
    	      e.printStackTrace();
    	} 
	}

	public void setCoords(ArrayList<LocationList> coords) {
		this.coords = coords;
	}

	public ArrayList<LocationList> getCoords() {
		return coords;
	}

	public void setCode(ArrayList<String> code) {
		this.code = code;
	}

	public ArrayList<String> getCode() {
		return code;
	}

	public void setName(ArrayList<String> name) {
		this.name = name;
	}

	public ArrayList<String> getName() {
		return name;
	}
	
	
	/**
	 * The gml file created from the original shapefile for each fault
	 * contains many segments. This method remove multiple segments 
	 * of a single fault structure and groups them into a single 
	 * fault.
	 * @throws CloneNotSupportedException 
	 */
	public void removeFaultSegments() throws CloneNotSupportedException {
		// TODO 

		// Create a hashmap to identify the elements with the same code. 
		// This hashmap associates a String (source code) to a number 
		// that's the id in the ArrayList
		HashMap<String,Integer> codeMap = new HashMap<String,Integer>(); 
		Iterator<String> iter = this.code.iterator();
		int cnt = 0;
		while (iter.hasNext()){
			codeMap.put(iter.next(),cnt);
			cnt++;
		}
		// 
		
		// List of source codes
		Set<String> codeSet = codeMap.keySet();
		// Merge the fault segments
		Iterator<String> iterCode = codeSet.iterator();
		while(iterCode.hasNext()){
			
		}
		
		
	}
}
