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

import java.io.PrintStream;

import sun.net.smtp.SmtpClient;

/**
 * <p>Title: MailUtil.java </p>
 * <p>Description: Utility to send mail throough the program </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author Nitin Gupta, Vipin Gupta
 * @date May 4, 2004
 * @version 1.0
 */

public final class MailUtil {

  /**
   *
   * @param host SMTP server from which mail needs to be sent
   * @param from Email prefix of sender
   * @param emailAddr email address of receiver
   * @param mailSubject Email subject
   * @param mailMessage Email body
   */
 public static void sendMail(String host, String from,
                      String emailAddr,
                      String mailSubject,
                      String mailMessage) {
   try {

     // Create a new instance of SmtpClient.
     SmtpClient smtp = new SmtpClient(host);
     // Sets the originating e-mail address
     smtp.from(from);
     // Sets the recipients' e-mail address
     smtp.to(emailAddr);
     // Create an output stream to the connection
     PrintStream msg = smtp.startMessage();
     msg.println("To: " + emailAddr); // so mailers will display the recipient's e-mail address
     msg.println("From: " + from); // so that mailers will display the sender's e-mail address
     msg.println("Subject: " + mailSubject + "\n");
     msg.println(mailMessage);

     // Close the connection to the SMTP server and send the message out to the recipient
     smtp.closeServer();
   }
   catch (Exception e) {
     e.printStackTrace();
   }
 }

}
