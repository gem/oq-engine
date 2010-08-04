package org.opensha.gem.GEM1.calc.gemModelParsers.gscFrisk.canada;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Iterator;

import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;

public class GscFriskInputFile {

	private GscFriskInputHeader head;
	private ArrayList<GscFriskInputAlternative> gloAlt;
	
	/**
	 * Constructor. Parses the content of the Crisis input file
	 * @param filename - Name of the Crisis input file (2007 format)
	 */
//	public GscFriskInputFile (FileReader file, boolean skipComm) {
	public GscFriskInputFile (BufferedReader input, boolean skipComm) {
		// 
		GscFriskInputSource src;
		GscFriskInputAlternative tmpalt;
		this.gloAlt = new ArrayList<GscFriskInputAlternative>();
		
		// Reading the file
	    try {
	    	// Instantiate a BufferedReader
//	    	BufferedReader input =  new BufferedReader(file);
	    	try {
	    		
	    		// Reading the header
	    		this.head = new GscFriskInputHeader(input);
	    		System.out.printf("This file contains %d global alternatives\n",head.nGloAlt);
	    		
	    		// Read the global alternatives
	    		for (int i=0; i<head.nGloAlt; i++ ) {
	    			System.out.printf("Reading Global Alternative %d\n",i);
	    			tmpalt = new GscFriskInputAlternative(input, head);
	    			
	    			// Reading the source sets contained in this Global Alternative
	    			GscFriskInputSourceSet srcgrp = new GscFriskInputSourceSet();
	    			for (int j=0; j<tmpalt.getNumberSourceSets(); j++) {
	    				System.out.printf("\n   ----> Reading source set %d\n",j);
	    				src = new GscFriskInputSource(input,tmpalt,skipComm);
	    				srcgrp.addSource(src);
	    			}
	    			tmpalt.addSourceSet(srcgrp);
	    			gloAlt.add(tmpalt);
	    		}
	    	}
	    	finally {
	    		input.close();
	    	}
	    }
	    catch (IOException ex){
	    	ex.printStackTrace();
	    }
	}
	/**
	 * Return the header of the CrisisInputFile object
	 * @return Returns the Crisis Input Header
	 */
	public GscFriskInputHeader getHeader() {
		return this.head; 
	}
	/**
	 * Return the List of Global Alternatives 
	 * @return Returns the Crisis Input Header
	 */
	public ArrayList<GscFriskInputAlternative> getGlobalAlternatives() {
		return this.gloAlt; 
	}
	
	/**
	 * 
	 */
	public void createGMTfile(String filename) {
		Iterator<GscFriskInputAlternative> iter = this.gloAlt.iterator();
		while(iter.hasNext()){
			GscFriskInputAlternative alter = iter.next();
			GscFriskInputSourceSet srcSet = alter.getSourceSet(0);
			for (int i = 0; i < srcSet.getNumberOfSources(); i++){
				//GscFriskInputSource src = srcSet.getSource(i);
				LocationList locLis = srcSet.getSource(i).coords.get(0);
				Iterator<Location> locIter = locLis.iterator();
				while (locIter.hasNext()){
					Location loc = locIter.next();
					System.out.printf("%f %f",loc.getLongitude(),loc.getLongitude());
				}
			}
		}
		
	}
}
