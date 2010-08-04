package org.opensha.gem.GEM1.calc.gemModelParsers.gscFrisk.canada;

import java.util.ArrayList;

public class GscFriskInputSourceSet {

	private ArrayList<GscFriskInputSource> srcLst; 
	
	public GscFriskInputSourceSet(){
		this.srcLst = new ArrayList<GscFriskInputSource>();
	}
	
	public void addSource(GscFriskInputSource src){
		this.srcLst.add(src);
	}
	public GscFriskInputSource getSource(int idx){
		return this.srcLst.get(idx);
	}
	public int getNumberOfSources(){
		return this.srcLst.size();
	}
	public void deleteSource(int idx){
		this.srcLst.remove(idx);
	}
}
