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


import java.awt.Font;
import java.awt.FontMetrics;
import java.awt.Graphics;
import java.awt.PrintGraphics;
import java.awt.PrintJob;
import java.io.EOFException;
import java.io.FileWriter;
import java.io.IOException;
import java.io.LineNumberReader;
import java.io.StringReader;


/**
 * <p>Title: PrintData</p>
 *
 * <p>Description: This class sends the text for printing to the printer.</p>
 * @author Ned Field, Nitin Gupta and E.V.Leyendecker
 * @version 1.0
 */
public class DataUtil {


  private String textToPrint ;
  private final static int margin = 60;


  /**
   * Saves the text to a file on the users machine.
   * File is saved with extension ".txt".
   * @param panel Component
   * @param dataToSave String
   */
  public static void save(String fileName, String dataToSave) {

      try {
        FileWriter fw = new FileWriter(fileName);
        fw.write(dataToSave);
        fw.close();
      }
      catch (IOException e) {
        //JOptionPane.showMessageDialog(panel, "Error creating file", "Error",
          //                            JOptionPane.ERROR_MESSAGE);
          e.printStackTrace();
      }
  }


  /**
   * Prints a Text file
   * @param pjob PrintJob  created using getToolkit().getPrintJob(JFrame,String,Properties);
   * @param pg Graphics
   * @param textToPrint String
   */
  public static void print(PrintJob pjob, Graphics pg, String textToPrint) {

     int pageNum = 1;
     int linesForThisPage = 0;
     int linesForThisJob = 0;
     // Note: String is immutable so won't change while printing.
     if (!(pg instanceof PrintGraphics)) {
       throw new IllegalArgumentException ("Graphics context not PrintGraphics");
     }
     StringReader sr = new StringReader (textToPrint);
     LineNumberReader lnr = new LineNumberReader (sr);
     String nextLine;
     int pageHeight = pjob.getPageDimension().height - margin;
     Font helv = new Font("Monaco", Font.PLAIN, 12);
     //have to set the font to get any output
     pg.setFont (helv);
     FontMetrics fm = pg.getFontMetrics(helv);
     int fontHeight = fm.getHeight();
     int fontDescent = fm.getDescent();
     int curHeight = margin;
     try {
       do {
         nextLine = lnr.readLine();
         if (nextLine != null) {
           if ((curHeight + fontHeight) > pageHeight) {
             // New Page
             if (linesForThisPage == 0)
                break;

             pageNum++;
             linesForThisPage = 0;
             pg.dispose();
             pg = pjob.getGraphics();
             if (pg != null) {
               pg.setFont (helv);
             }
             curHeight = 0;
           }
           curHeight += fontHeight;
           if (pg != null) {
             pg.drawString (nextLine, margin, curHeight - fontDescent);
             linesForThisPage++;

             linesForThisJob++;
           }
         }
       } while (nextLine != null);
     } catch (EOFException eof) {
       // Fine, ignore
     } catch (Throwable t) { // Anything else
       t.printStackTrace();
     }
  }
}
