package org.opensha.sha.imr.attenRelImpl.peer;

public enum TestSite {
	
	SITE_1("Site1"),
	SITE_2("Site2"),
	SITE_3("Site3"), 
	SITE_4("Site4"), 
	SITE_5("Site5"), 
	SITE_6("Site6"), 
	SITE_7("Site7");
	
	private String id;
	
	private TestSite(String id) {
		this.id = id;
	}
	
	public String toString() {
		return id;
	}
}
