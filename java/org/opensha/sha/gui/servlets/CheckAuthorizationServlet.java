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

package org.opensha.sha.gui.servlets;

import java.io.ObjectOutputStream;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.opensha.sha.gui.servlets.user_auth_db.OpenSHA_UsersDBDAO;
import org.opensha.sha.gui.servlets.user_auth_db.OpenSHA_UsersVO;


/**
 *
 * <p>Title: CheckAuthorizationServlet.java </p>
 * <p>Description: It will check the database to see whether user is authorized to
 * use the system</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author Vipin Gupta, Nitin Gupta
 * @date Nov 18, 2004
 * @version 1.0
 */

public class CheckAuthorizationServlet extends HttpServlet {
	private OpenSHA_UsersDBDAO dao = new OpenSHA_UsersDBDAO();
	public final static String USERNAME = "username";
	public final static String PASSWORD = "password";

	/**Handles the HTTP <code>GET</code> method.
	 * @param request servlet request
	 * @param response servlet response
	 */
	public void doGet(HttpServletRequest request, HttpServletResponse response)
	throws ServletException, java.io.IOException {
		System.out.println("CheckAuthorizationServlet: Handling GET");
		String uname = request.getParameter(USERNAME);
		String password = request.getParameter(PASSWORD);
		OpenSHA_UsersVO userInfo  = dao.getUserInfo(uname, password);
		// get an ouput stream from the applet
		ObjectOutputStream outputToApplet = new ObjectOutputStream(response.getOutputStream());
		if(userInfo==null)
			//name of the image file as the URL
			outputToApplet.writeObject(Boolean.FALSE);
		else outputToApplet.writeObject(new Boolean(dao.isUserAuthorized(userInfo)));
		outputToApplet.close();
	}

	/** Handles the HTTP <code>POST</code> method.
	 * @param request servlet request
	 * @param response servlet response
	 */
	public void doPost(HttpServletRequest request, HttpServletResponse response)
	throws ServletException, java.io.IOException {
		doGet(request, response);
	}

}
