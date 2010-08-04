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

package org.opensha.sha.gui.infoTools;

import java.awt.BorderLayout;
import java.awt.Component;

import javax.swing.JFrame;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;

/**
 * <p>Title: DisplayDataWindow</p>
 *
 * <p>Description: Allows the users to display the data in a window.</p>
 *
 * @author Nitin Gupta
 * @version 1.0
 */
public class DisplayDataWindow
    extends JFrame {

  private JScrollPane dataScrollPane = new JScrollPane();
  private JTextArea dataText = new JTextArea();
  private BorderLayout borderLayout1 = new BorderLayout();

  public DisplayDataWindow(Component parent, String data, String title) {
    try {
      jbInit();
      // show the window at center of the parent component
      this.setLocation(parent.getX()+parent.getWidth()/2,
                       parent.getY()+parent.getHeight()/2);
      this.setTitle(title);

    }
    catch (Exception exception) {
      exception.printStackTrace();
    }
    setDataInWindow(data);
  }

  private void jbInit() throws Exception {
    getContentPane().setLayout(borderLayout1);
    dataScrollPane.getViewport().add(dataText, null);
    this.getContentPane().add(dataScrollPane, java.awt.BorderLayout.CENTER);
    dataText.setEditable(false);
    this.setSize(400,300);
  }


  public void setDataInWindow(String data){
    dataText.setText(data);
    dataText.setCaretPosition(0);
  }

}
