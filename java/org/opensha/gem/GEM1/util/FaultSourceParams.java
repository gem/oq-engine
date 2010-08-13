package org.opensha.gem.GEM1.util;

public enum FaultSourceParams {
	
	/** Fault discretization grid spacing. */
	FAULT_GRID_SPACING("Fault discretization grid spacing (in km)"),
	
	/** Rupture aspect ratio. */
	RUP_ASPECT_RATIO("Rupture aspect ratio"),
	
	/** Rupture offset. */
	RUP_OFFSET("Rupture offset"),
	
	/** Magnitude area relationship. */
	MAG_AREA_REL("Magnitude area relationship");
	
	private String name;
	
	private FaultSourceParams(String name) {
		this.name = name;
	}
	
	/**
	 * This gets the GemSourceType associated with the given string
	 * @param name
	 * @return
	 */
	public static FaultSourceParams getTypeForName(String name) {
		if (name == null) throw new NullPointerException();
		for (FaultSourceParams trt:FaultSourceParams.values()) {
			if (trt.name.equals(name)) return trt;
		}
		throw new IllegalArgumentException("Fault source parameter does not exist");
	}
	
	/**
	 * This check whether given string is a valid Gem source type
	 * @param name
	 * @return
	 */
	public static boolean isValidType(String name) {
		boolean answer = false;
		for (FaultSourceParams trt:FaultSourceParams.values()) {
			if (trt.name.equals(name)) answer = true;
		}
		return answer;
	}

	
	@Override
	public String toString() {
		return name;
	}

}
