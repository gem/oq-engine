package org.opensha.gem.GEM1.util;


public enum SourceType {
	
	/** Area source. */
	AREA_SOURCE("Area Source"),
	
	/** Grid source. */
	GRID_SOURCE("Grid Source"),
	
	/** Fault source. */
	FAULT_SOURCE("Fault Source"),
	
	/** Subduction fault source. */
	SUBDUCTION_FAULT_SOURCE("Subduction Fault Source");
	
	private String name;
	
	private SourceType(String name) {
		this.name = name;
	}
	
	/**
	 * This gets the GemSourceType associated with the given string
	 * @param name
	 * @return
	 */
	public static SourceType getTypeForName(String name) {
		if (name == null) throw new NullPointerException();
		for (SourceType trt:SourceType.values()) {
			if (trt.name.equals(name)) return trt;
		}
		throw new IllegalArgumentException("GEM source name does not exist");
	}
	
	/**
	 * This check whether given string is a valid Gem source type
	 * @param name
	 * @return
	 */
	public static boolean isValidType(String name) {
		boolean answer = false;
		for (SourceType trt:SourceType.values()) {
			if (trt.name.equals(name)) answer = true;
		}
		return answer;
	}

	
	@Override
	public String toString() {
		return name;
	}

}
