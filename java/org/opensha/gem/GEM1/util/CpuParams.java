package org.opensha.gem.GEM1.util;

public enum CpuParams {

	/**  number of cpus used for calculation */
	CPU_NUMBER("Number of cpus used for calculation");
	
	private String name;
	
	private CpuParams(String name) {
		this.name = name;
	}
	
	/**
	 * This gets the GemSourceType associated with the given string
	 * @param name
	 * @return
	 */
	public static CpuParams getTypeForName(String name) {
		if (name == null) throw new NullPointerException();
		for (CpuParams trt:CpuParams.values()) {
			if (trt.name.equals(name)) return trt;
		}
		throw new IllegalArgumentException("Cpu parameter name does not exist");
	}
	
	/**
	 * This check whether given string is a valid Gem source type
	 * @param name
	 * @return
	 */
	public static boolean isValidType(String name) {
		boolean answer = false;
		for (CpuParams trt:CpuParams.values()) {
			if (trt.name.equals(name)) answer = true;
		}
		return answer;
	}

	
	@Override
	public String toString() {
		return name;
	}
	
}
