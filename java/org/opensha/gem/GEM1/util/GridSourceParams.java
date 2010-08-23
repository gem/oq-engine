package org.opensha.gem.GEM1.util;

public enum GridSourceParams {
		
		/** Magnitude area scaling relationship.
		 * It is used for non-vertical faults.
		 * Non-vertical faults are treated as 3D faults
		 * to take into account the hanging wall effect. */
		MAG_AREA_REL("Magnitude area scaling relationship"),
		
		/** Magnitude length scaling relationship. 
		 * It is used for vertical faults, because they are
		 * treated as 2D faults. */
		MAG_LENGTH_REL("Magnitude length scaling relationship"),
		
		/** Cut off magnitude. 
		 * Below this value the source is treated as 
		 * a point source. */
		MAG_CUT_OFF("Magnitude cut-off"),
		
		/** Rupture aspect ratio. */
		RUP_ASPECT_RATIO("Rupture aspect ratio"),
		
		/** Rupture center depth. */
		RUP_CENTER_DEPTH("Rupture center depth"),
		
		/** Cut off magnitude for depth to top of rupture distribution. */
		MAG_CUT_OFF_TOP_RUP_DEPTH("Cut-off magnitude for depth to top of rupture distribution."),
		
		/** Top of rupture depth for events with magnitude less than the cut-off magnitude. */
		TOP_RUP_DEPTH_LESS_MAG_CUT_OFF("Top of rupture depth for events with magnitude less than the cut-off magnitude."),
		
		/** Top of rupture depth for events with magnitude greater than the cut-off magnitude. */
		TOP_RUP_DEPTH_GREATER_MAG_CUT_OFF("Top of rupture depth for events with magnitude greater than the cut-off magnitude."),
		
		/** Rupture grid spacing. */
		RUP_GRID_SPACING("Rupture grid spacing"),
		
		/** Minimum strike angle. */
		MIN_STRIKE("Minimum strike angle"),
		
		/** Maximum strike angle. */
	    MAX_STRIKE("Maximum strike angle"),
	    
		/** Delta strike. */
		DELTA_STRIKE("Delta strike");
		
		private String name;
		
		private GridSourceParams(String name) {
			this.name = name;
		}
		
		/**
		 * This gets the GemSourceType associated with the given string
		 * @param name
		 * @return
		 */
		public static GridSourceParams getTypeForName(String name) {
			if (name == null) throw new NullPointerException();
			for (GridSourceParams trt:GridSourceParams.values()) {
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
			for (GridSourceParams trt:GridSourceParams.values()) {
				if (trt.name.equals(name)) answer = true;
			}
			return answer;
		}

		
		@Override
		public String toString() {
			return name;
		}

}
