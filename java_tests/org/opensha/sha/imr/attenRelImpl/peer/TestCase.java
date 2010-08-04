package org.opensha.sha.imr.attenRelImpl.peer;

public enum TestCase {
	
	CASE_1("Case1"), 
	CASE_2("Case2"), 
	CASE_3("Case3"), 
	CASE_4("Case4"), 
	CASE_5("Case5"), 
	CASE_6("Case6"), 
	CASE_7("Case7"),
	CASE_8A("Case8a"), 
	CASE_8B("Case8b"), 
	CASE_8C("Case8c"),
	CASE_9A("Case9a"), 
	CASE_9B("Case9b"), 
	CASE_9C("Case9c"),
	CASE_10("Case10"), 
	CASE_11("Case11"), 
	CASE_12("Case12");
	
	private String id;
	
	private TestCase(String id) {
		this.id = id;
	}
	
	public String toString() {
		return id;
	}
}
