package org.opensha.gem.GEM1.util;

public enum DistanceParams {

	/** maximum distance to source */
	MAX_DIST_SOURCE("Maximum distance to source");
	
	private String name;
	
	private DistanceParams(String name) {
		this.name = name;
	}
	
	/**
	 * This gets the GemSourceType associated with the given string
	 * @param name
	 * @return
	 */
	public static DistanceParams getTypeForName(String name) {
		if (name == null) throw new NullPointerException();
		for (DistanceParams trt:DistanceParams.values()) {
			if (trt.name.equals(name)) return trt;
		}
		throw new IllegalArgumentException("Area source parameter name does not exist");
	}
	
	/**
	 * This check whether given string is a valid Gem source type
	 * @param name
	 * @return
	 */
	public static boolean isValidType(String name) {
		boolean answer = false;
		for (DistanceParams trt:DistanceParams.values()) {
			if (trt.name.equals(name)) answer = true;
		}
		return answer;
	}

	
	@Override
	public String toString() {
		return name;
	}
	
}
