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


import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.opensha.commons.util.MailUtil;

/**
 * <p>Title: EmailServlet </p>
 * <p>Description: This servlet sends email to the system maintainer if application
 * crashes and user submits the bug report using the Bug reporting window that
 * pops up. </p>
 * @author : Nitin Gupta & Vipin Gupta
 * @version 1.0
 */

public class EmailServlet extends HttpServlet {

	//static Strings to send the mails
	private static final String TO = "vgupta@usc.edu, kmilner@usc.edu";
	private static final String HOST = "email.usc.edu";

	//Process the HTTP Get request
	public void doGet(HttpServletRequest request, HttpServletResponse response) throws
	ServletException, IOException {
		
		System.out.println("EmailServlet: Handling GET");

		try {

			// get an input stream from the applet
			ObjectInputStream inputFromApplet = new ObjectInputStream(request.
					getInputStream());


			//get the email address from the applet
			String email = (String) inputFromApplet.readObject();

			//getting the email content from the aplication
			String emailMessage = (String) inputFromApplet.readObject();
			MailUtil.sendMail(HOST,email,TO,"Exception in Application",emailMessage);
			// report to the user whether the operation was successful or not
			// get an ouput stream from the applet
			ObjectOutputStream outputToApplet = new ObjectOutputStream(response.
					getOutputStream());
			outputToApplet.writeObject("Email Sent");
			outputToApplet.close();

		}
		catch (Exception e) {
			// report to the user whether the operation was successful or not
			e.printStackTrace();
		}
	}



	//Process the HTTP Post request
	public void doPost(HttpServletRequest request, HttpServletResponse response) throws
	ServletException, IOException {
		// call the doPost method
		doGet(request, response);
	}

}
