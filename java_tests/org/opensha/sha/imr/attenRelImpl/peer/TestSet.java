package org.opensha.sha.imr.attenRelImpl.peer;

public enum TestSet {
	
	SET_1("Set1"), 
	SET_2("Set2");
	
	private String id;
	
	private TestSet(String id) {
		this.id = id;
	}
	
	public String toString() {
		return id;
	}
}
