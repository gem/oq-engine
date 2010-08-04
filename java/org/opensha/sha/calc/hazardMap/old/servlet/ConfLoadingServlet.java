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
import java.io.ObjectOutputStream;
import java.text.DateFormat;
import java.util.Date;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.opensha.sha.calc.hazardMap.old.ConfLoader;
import org.opensha.sha.calc.hazardMap.old.HazardMapJobCreator;

public abstract class ConfLoadingServlet extends HttpServlet {
	
	DateFormat df = HazardMapJobCreator.LINUX_DATE_FORMAT;

	public static final String CONF_FILE = "/home/aftershock/opensha/hazmaps/conf/conf.xml";

	protected ConfLoader confLoader = null;
	
	String debugName;

	public ConfLoadingServlet(String debugName) {
		super();
		
		this.debugName = debugName;

		try {
			confLoader = new ConfLoader(CONF_FILE);
		} catch (Exception e) {
			confLoader = null;
		}
	}

	protected void fail(ObjectOutputStream out, String message) throws IOException {
		debug("Failing: " + message);
		out.writeObject(new Boolean(false));
		out.writeObject(message);
		out.flush();
		out.close();
	}
	
	protected void fail(ObjectOutputStream out, Exception e) throws IOException {
		debug("Failing: " + e.getMessage());
		out.writeObject(new Boolean(false));
		out.writeObject(e);
		out.flush();
		out.close();
	}

	//Process the HTTP Post request
	public void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		// call the doGet method
		doGet(request,response);
	}

	@Override
	// Process the HTTP Get request
	abstract public void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException;
	
	protected void debug(String message) {
		String date = "[" + df.format(new Date()) + "]";
		System.out.println(debugName + " " + date + ": " + message);
	}

}
