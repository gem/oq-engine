package org.opensha.gem.GEM1.calc.gemLogicTree;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.io.Serializable;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;

import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.gem.GEM1.calc.gemHazardCalculator.GemComputeHazardLogicTree;


public class GemLogicTree<Element> implements GemLogicTreeAPI<Element>, Serializable {

	private ArrayList<GemLogicTreeBranchingLevel> branLevLst;
	protected HashMap<String,Element> ebMap;
	private static String modelName;
	
	private Boolean D = false;
	
	public GemLogicTree(){
		this.branLevLst = new ArrayList<GemLogicTreeBranchingLevel>();
		this.ebMap = new HashMap<String,Element>();
		this.modelName = "";
	}
	
	public GemLogicTree(String fileName) throws IOException, ClassNotFoundException{
		
	    URL data = GemComputeHazardLogicTree.class.getResource(fileName);
	    File file = new File(data.getFile());
        FileInputStream f_in = null;
		try {
			//f_in = new FileInputStream(fileName);
			f_in = new FileInputStream(file.getPath());
		} catch (FileNotFoundException e) {
			System.out.println(file.getPath()+" not found!!");
			e.printStackTrace();
			System.exit(0);
		}
		
	    // Read object using ObjectInputStream.
	    ObjectInputStream obj_in = new ObjectInputStream (f_in);
	
	    // Read an object.
	    Object obj = obj_in.readObject ();
	
	    GemLogicTree<Element> gemLogicTree = (GemLogicTree<Element>) obj;
	    
	    this.branLevLst = gemLogicTree.getBranchingLevelsList();
	    this.ebMap = (HashMap<String, Element>) gemLogicTree.getEBMap();
	    this.modelName = gemLogicTree.getModelName();
		
	}

	/**
	 * 
	 */
	public void addBranchingLevel(GemLogicTreeBranchingLevel branLev){
		this.branLevLst.add(branLev);
	}
	
	/**
	 * 
	 */
	public void addEBMapping(String str, Element obj){
		this.ebMap.put(str,obj);
	}
	
	/**
	 * 
	 */
	public ArrayList<GemLogicTreeBranchingLevel> getBranchingLevelsList(){
		return this.branLevLst;
	}
	
	/**
	 * 
	 */
	public GemLogicTreeBranchingLevel getBranchingLevel(int idx){
		return this.branLevLst.get(idx);
	}	

	/**
	 * 
	 */
	public void setModelName(String str){
		this.modelName = str;
	}
	
	/**
	 * 
	 */
	public String getModelName(){
		return this.modelName;
	}
	
	/**
	 * 
	 */
	public double getWeight(String lab){
		String[] strarr = lab.split("_");
		GemLogicTreeBranchingLevel brl = this.branLevLst.get(strarr.length-1);
		return brl.getBranch(Integer.valueOf(strarr[strarr.length-1]).intValue()).getWeight();
	}
	
	/**
	 * 
	 */
	public double getTotWeight(String lab){
		double weight = 1.0;
		String[] strarr = lab.split("_");
		for (int i=0; i<strarr.length;i++){
			GemLogicTreeBranchingLevel brl = this.branLevLst.get(i);
			GemLogicTreeBranch br = brl.getBranch(Integer.valueOf(strarr[i]).intValue()-1);
			weight = weight * br.getWeight();
		}
		return weight;
	}

	public HashMap<String,Element> getEBMap() {
		return ebMap;
	}

	public Iterator<Element> iterator() {
		return ebMap.values().iterator();
	}

	public void saveGemLogicTreeModel(String fileName) throws Exception {
		
		// Use a FileOutputStream to send data to a file
		FileOutputStream f_out = new FileOutputStream (fileName);

		// Use an ObjectOutputStream to send object data to the
		// FileOutputStream for writing to disk.
		ObjectOutputStream obj_out = new ObjectOutputStream (f_out);

		// Pass our object to the ObjectOutputStream's
		// writeObject() method to cause it to be written out
		// to disk.
		obj_out.writeObject (this);
	}
	
	/**
	 * print logic tree structure on standard output
	 * 
	 */
	public void printGemLogicTreeStructure(){
		
		// total number of branching levels
	    int numBranchingLevels = this.branLevLst.size();

	    System.out.println("Total number of branching levels in the logic tree: "+numBranchingLevels+"\n");
	    // loop over branching levels
	    for(int i=0;i<numBranchingLevels;i++){
	    	
	    	GemLogicTreeBranchingLevel braLev = this.branLevLst.get(i);
	    	System.out.println("Branching level: "+braLev.getLevel()+", label: "+braLev.getBranchingLabel()+", appliesTo: "+braLev.getAppliesTo());
	    	
	    	// number of branches
	    	int numBranches = braLev.getTreeBranchList().size();
	        // loop over branches
	    	for(int j=0;j<numBranches;j++){
	    		
	    		GemLogicTreeBranch bra = braLev.getBranch(j);
	    		
	    		System.out.println("Branch number: "+bra.getRelativeID()+", label: "+bra.getBranchingValue()+", weight: "+bra.getWeight());
	    		if(bra.getNameInputFile()!=null) System.out.println("Associated file: "+bra.getNameInputFile());
	    		if(bra.getRule()!=null) {
	    			System.out.println("Associated rule: "+bra.getRule().getRuleName());
	    			System.out.println("Associated uncertainty value: "+bra.getRule().getVal());
	    		}
	    		
	    		
	    	}
	    	System.out.println("\n\n");
	    	
	    }
	}
	
	/**
	 * This method samples a branching level and return the index of a branch. 
	 * The sampling is done using the inverse transform method.
	 * (For the algorithm description see "Computational Statistics Handbook 
	 * with Matlab", Martinez & Martinez, Champman & all, pag.83)
	 */
	public int sampleBranchingLevel(int branchingLevelIndex){
		
		
		int sample = -Integer.MIN_VALUE;
		
		// get the corresponding branching level
		GemLogicTreeBranchingLevel bl = this.branLevLst.get(branchingLevelIndex);
		
		// x values
		int[] x = new int[bl.getTreeBranchList().size()];
		// p (probability values)
		double[] p = new double[bl.getTreeBranchList().size()];
		
		// loop over branches
		int i = 0;
		for(GemLogicTreeBranch b: bl.getTreeBranchList()){
			
			x[i] = b.getRelativeID();
			p[i] = b.getWeight();
			if(D) System.out.println("label, prob: "+x[i]+" "+p[i]);
			
			i = i+1;
			
		}
		
		// compute cumulative distribution
		double[] cdf = new double[p.length];
		// initialize to zero
		for(i=0;i<cdf.length;i++) cdf[i] = 0.0;
		for(i=0;i<cdf.length;i++){
			for(int j=0;j<=i;j++) cdf[i] = cdf[i] + p[j];
		}
		if(D) System.out.println("Cumulative distribution:");
		if(D) for(i=0;i<cdf.length;i++) System.out.println(cdf[i]);
		
		// generate uniform random number between 0 and 1
		double rand = Math.random();
		if(D) System.out.println("Random number: "+rand);
		
		// loop over probabilities
		for(int j=0;j<p.length;j++){
			
			if(rand<=cdf[j]){
				sample = x[j];
				break;
			}
						
		}// end loop over probabilities
		
		return sample;
	}
}
