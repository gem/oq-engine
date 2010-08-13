package org.opensha.gem.GEM1.util;

public enum ResultTypeParams {

	HAZARD_MAP("Hazard map"),

	HAZARD_CURVE("Hazard curve"),
	
	DISAGGREGATION_MAP("Disaggregation map");
	
	private String name;
	
	private ResultTypeParams(String name) {
		this.name = name;
	}
	
	/**
	 * This gets the GemSourceType associated with the given string
	 * @param name
	 * @return
	 */
	public static ResultTypeParams getTypeForName(String name) {
		if (name == null) throw new NullPointerException();
		for (ResultTypeParams trt:ResultTypeParams.values()) {
			if (trt.name.equals(name)) return trt;
		}
		throw new IllegalArgumentException("Area source parameter name does not exist");
	}
	
	/**
	 * This check whether given string is a valid return type
	 * @param name
	 * @return
	 */
	public static boolean isValidType(String name) {
		boolean answer = false;
		for (ResultTypeParams trt:ResultTypeParams.values()) {
			if (trt.name.equals(name)) answer = true;
		}
		return answer;
	}

	
	@Override
	public String toString() {
		return name;
	}

}
