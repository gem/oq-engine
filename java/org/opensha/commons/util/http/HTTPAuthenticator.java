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

package org.opensha.commons.util.http;

import java.net.Authenticator;
import java.net.PasswordAuthentication;

import org.opensha.commons.gui.UserAuthDialog;


public class HTTPAuthenticator extends Authenticator {
	
	UserAuthDialog auth;
	
	public HTTPAuthenticator() {
		super();
		
		auth = new UserAuthDialog(null, false);
	}
	
	public UserAuthDialog getDialog() {
		return auth;
	}

    public PasswordAuthentication getPasswordAuthentication () {
    	auth.setVisible(true);
    	if (auth.isCanceled())
    		return null;
        return new PasswordAuthentication (auth.getUsername(), auth.getPassword());
    }
}
