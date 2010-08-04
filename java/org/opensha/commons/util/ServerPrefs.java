/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.commons.util;

import java.util.NoSuchElementException;

public enum ServerPrefs {
	
	/**
	 * Preferences for development (trunk)
	 */
	DEV_PREFS(ServerPrefUtils.OPENSHA_SERVLET_DEV_URL,
			ServerPrefUtils.BUILD_TYPE_NIGHTLY),
	/**
	 * Preferences for stable production releases
	 */
	PRODUCTION_PREFS(ServerPrefUtils.OPENSHA_SERVLET_PRODUCTION_URL,
			ServerPrefUtils.BUILD_TYPE_PRODUCTION);
	
	private String servletURL;
	private String buildType;
	
	private ServerPrefs(String servletURL, String buildType) {
		this.servletURL = servletURL;
		this.buildType = buildType;
	}

	public String getServletBaseURL() {
		return servletURL;
	}

	public String getBuildType() {
		return buildType;
	}
	
	/**
	 * Returns the server type with the given build type string
	 * 
	 * @param buildType
	 * @return
	 */
	public static ServerPrefs fromBuildType(String buildType) {
		for (ServerPrefs prefs : ServerPrefs.values()) {
			if (prefs.getBuildType().equals(buildType))
				return prefs;
		}
		throw new NoSuchElementException("No ServerPrefs instance exists with build type '" + buildType + "'");
	}
	
}
