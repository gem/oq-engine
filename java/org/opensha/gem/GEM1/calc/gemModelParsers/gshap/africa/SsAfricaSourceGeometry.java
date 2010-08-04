package org.opensha.gem.GEM1.calc.gemModelParsers.gshap.africa;

import java.util.ArrayList;

import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;

public class SsAfricaSourceGeometry {
	
	LocationList vertexes;
	int id;

	public SsAfricaSourceGeometry (){
	}
	
	public SsAfricaSourceGeometry (LocationList vertexes, int id){
		this.vertexes = vertexes;
		this.id = id; 
	}
	
	public void setId(int id){
		this.id = id;
	}
	
	public void setVertexes(LocationList vertexes){
		this.vertexes = vertexes;
	}
	
	public LocationList getVertexes(){
		return this.vertexes;
	}

	public int getId(){
		return this.id;
	}
	
}
