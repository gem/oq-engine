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

import java.io.BufferedReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
/**
 * <p>Title: RunScript</p>
 * <p>Description : Accepts the command and runs the shell script
 * @author: Nitin Gupta and Vipin Gupta
 * @created:Dec 27, 2002
 * @version 1.0
 */

public class RunScript {


	/**
	 * accepts the command and executes on java runtime environment
	 *
	 * @param command : command to execute
	 */
	public static int runScript(String[] command, String outFile, String errFile) {
		int i=0;
		try {
			// wait for the shell script to end
			System.out.println("Command to execute: " +command[2]);
			Process p=Runtime.getRuntime().exec(command);
			i=displayProcessStatus(p, outFile, errFile);
		} catch(Exception e) {
			// if there is some other exception, print the detailed explanation
			System.out.println("Exception in Executing Shell Script:"+e);
			e.printStackTrace();
		}
		return i;
	}

	/**
	 * accepts the command and executes on java runtime environment
	 *
	 * @param command : command to execute
	 */
	public static int runScript(String[] command) {
		return runScript(command, "", "");
	}

	/**
	 * display the input stream
	 * @param is inputstream
	 * @throws Exception
	 */
	public static void displayOutput(InputStream is) throws Exception {
		String s;
		try {
			BufferedReader br = new BufferedReader(new InputStreamReader(is));
			while ((s = br.readLine()) != null)
				System.out.println(s);
		} catch (Exception e) {
			System.out.println("Exception in RunCoreCode:displayOutput:"+e);
			e.printStackTrace();
		}
	}

	/**
	 * Display the process status while it is executing
	 *
	 * @param pr
	 * @return
	 * @throws IOException 
	 */
	public static int displayProcessStatus(Process pr, String outFile, String errFile) throws IOException {
		InputStream is = pr.getErrorStream();
		InputStreamReader isr = new InputStreamReader(is);
		BufferedReader br = new BufferedReader(isr);
		InputStream es = pr.getInputStream();
		InputStreamReader esr = new InputStreamReader(es);
		BufferedReader ebr = new BufferedReader(esr);
		String processStr=null, errStr=null;
		
		FileWriter outWrite = null;
		if (outFile != null && outFile.length() > 0)
			outWrite = new FileWriter(outFile);
		FileWriter errWrite = null;
		if (errFile != null && errFile.length() > 0)
			errWrite = new FileWriter(errFile);
		try {
			// get the error and process output strings
			while ( ( (errStr = ebr.readLine()) != null) ||
					( (processStr = br.readLine()) != null)) {
				if (processStr != null) {
					System.out.println(processStr);
					if (outWrite != null)
						outWrite.write(processStr + "\n");
				}
				if (errStr != null) {
					System.out.println(errStr);
					if (errWrite != null)
						errWrite.write(errStr + "\n");
				}
				if ( (processStr == null) && (errStr == null)) {
					break;
				}
			}
			if (outWrite != null)
				outWrite.close();
			if (errWrite != null)
				errWrite.close();
			int exit = pr.waitFor();
			return exit;
		}catch(Exception e) { e.printStackTrace(); }
		if (outWrite != null)
			outWrite.close();
		if (errWrite != null)
			errWrite.close();
		return -1;
	}
}
