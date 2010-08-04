package org.opensha.gem.GEM1.util;

public enum AreaSourceParams {
	
	/** Area discretization grid spacing */
	AREA_GRID_SPACING("Area discretization grid spacing (in degree)"),
	
    /** Rake angle*/
	RAKE("Rake angle (in degree)"),
	
	/** Dip angle */
	DIP("Dip angle (in degree)");
	
	private String name;
	
	private AreaSourceParams(String name) {
		this.name = name;
	}
	
	/**
	 * This gets the GemSourceType associated with the given string
	 * @param name
	 * @return
	 */
	public static AreaSourceParams getTypeForName(String name) {
		if (name == null) throw new NullPointerException();
		for (AreaSourceParams trt:AreaSourceParams.values()) {
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
		for (AreaSourceParams trt:AreaSourceParams.values()) {
			if (trt.name.equals(name)) answer = true;
		}
		return answer;
	}

	
	@Override
	public String toString() {
		return name;
	}

}
