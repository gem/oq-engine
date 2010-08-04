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

package org.opensha.sha.calc.hazardMap.old.servlet;

import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.net.URLConnection;

import org.opensha.commons.mapping.gmt.GMT_Map;

public class PlotServletAccessor extends ServletAccessor {
	
	public static final String SERVLET_URL = "http://opensha.usc.edu:8080/HazardMaps/HazardMapPlotter";
	
	public PlotServletAccessor() {
		super(SERVLET_URL);
	}
	
	public String getMap(String datasetID, GMT_Map map, boolean isProbAt_IML, double level, String overwriteMode)
				throws IOException, ClassNotFoundException {
		URLConnection servletConnection = this.openServletConnection(false);
		
		ObjectOutputStream outputToServlet = new
		ObjectOutputStream(servletConnection.getOutputStream());

		System.out.println("Sending ID...");
		outputToServlet.writeObject(datasetID);
		
		// send the operation to servlet
		System.out.println("Sending Operation...");
		outputToServlet.writeObject(PlotServlet.OP_PLOT);
		
		System.out.println("Sending isProbAt_IML...");
		outputToServlet.writeObject(new Boolean(isProbAt_IML));
		
		System.out.println("Sending level...");
		outputToServlet.writeObject(new Double(level));
		
		System.out.println("Sending overwrite...");
		outputToServlet.writeObject(overwriteMode);
		
		System.out.println("Sending GMT_Map...");
		outputToServlet.writeObject(map);
		
		ObjectInputStream inputFromServlet = new
		ObjectInputStream(servletConnection.getInputStream());
		
		System.out.println("Getting map url...");
		Object mapObj = inputFromServlet.readObject();
		
		checkHandleError("Plot request failed: ", mapObj, inputFromServlet);
		
		String mapURL = (String)mapObj;
		
		inputFromServlet.close();
		
		return mapURL;
	}

}
