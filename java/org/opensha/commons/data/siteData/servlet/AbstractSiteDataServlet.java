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

package org.opensha.commons.data.siteData.servlet;

import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.opensha.commons.data.siteData.SiteDataAPI;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.util.ServerPrefUtils;

public abstract class AbstractSiteDataServlet<Element> extends HttpServlet {
	
//	public static DateFormat df = new SimpleDateFormat("EEE MMM dd HH:mm:ss z yyyy");
	
	public static String OP_GET_CLOSEST = "Get Closest Location";
	
	private SiteDataAPI<Element> data;
	
	private String debugName;
	
	public AbstractSiteDataServlet(SiteDataAPI<Element> data) {
		super();
		
		this.data = data;
		this.debugName = data.getShortName() + " servlet";
	}
	
	public AbstractSiteDataServlet() {
		// if you use this, you better set the data!
	}
	
	public void setData(SiteDataAPI<Element> data) {
		this.data = data;
		this.debugName = data.getShortName() + " servlet";
	}
	
	//Process the HTTP Post request
	public void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		// call the doGet method
		doGet(request,response);
	}
	
	private Location getLocation(double pt[]) {
		if (pt.length == 2) {
			return new Location(pt[0], pt[1]);
		} else if (pt.length == 3) {
			return new Location(pt[0], pt[1], pt[2]);
		} else {
			return null;
		}
	}
	
	// Process the HTTP Get request
	public void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		debug("Handling GET");
		
		// get an input stream from the applet
		ObjectInputStream in = new ObjectInputStream(request.getInputStream());
		ObjectOutputStream out = new ObjectOutputStream(response.getOutputStream());
		
		// get the location or location list object
		try {
			Object obj = in.readObject();
			
			if (obj instanceof Location) {
				// this is a single location request
				Location loc = (Location)obj;
				Element e = data.getValue(loc);
				out.writeObject(e);
			} else if (obj instanceof LocationList) {
				// this is a multiple location request
				LocationList locs = (LocationList)obj;
				ArrayList<Element> e = data.getValues(locs);
				out.writeObject(e);
			} else if (obj instanceof double[]) {
				// this is a single location request
				Location loc = getLocation((double[])obj);
				if (loc == null)
					fail(out, "Invalid location!");
				Element e = data.getValue(loc);
				out.writeObject(e);
			} else if (obj instanceof ArrayList) {
				// this is a multiple location request
				ArrayList<double[]> pts = (ArrayList<double[]>)obj;
				LocationList locs = new LocationList();
				for (double[] pt : pts) {
					Location loc = getLocation(pt);
					if (loc == null)
						fail(out, "Invalid location!");
					locs.add(loc);
				}
				ArrayList<Element> e = data.getValues(locs);
				out.writeObject(e);
			} else if (obj instanceof String) {
				String op = (String)obj;
				if (op.equals(OP_GET_CLOSEST)) {
					obj = in.readObject();
					if (!(obj instanceof Location)) {
						fail(out, "A location must be given for closest location operation");
						return;
					}
					Location loc = (Location)obj;
					Location close = data.getClosestDataLocation(loc);
					out.writeObject(loc);
				} else {
					fail(out, "Unknown operation: " + op);
					return;
				}
			} else {
				fail(out, "You must give either a Location or a LocationList!");
				return;
			}
			
			out.flush();
			out.close();
		} catch (Exception e) {
			e.printStackTrace(System.out);
			fail(out, "Servlet Exception: " + e.getMessage());
		}
	}
	
	protected void fail(ObjectOutputStream out, String message) throws IOException {
		ServerPrefUtils.fail(out, debugName, message);
	}
	
	protected void debug(String message) {
		ServerPrefUtils.debug(debugName, message);
	}
}
