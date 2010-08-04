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

import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Rectangle;

import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JProgressBar;

/**
 * <p>Title: CalcProgressBar</p>
 * <p>Description:Shows the Progrss Bar for the calculations</p>
 * @author: Nitin Gupta & Vipin Gupta
 * @created: March 10, 2003
 * @version 1.0
 */

public class CalcProgressBar extends JFrame {


  private JLabel label;
  // frame height and width
  private int FRAME_WIDTH = 320;
  private int FRAME_HEIGHT = 80;

  // start x and y for frame
  private int FRAME_STARTX = 400;
  private int FRAME_STARTY = 200;

  private JProgressBar progress;

  private String frameMessage=  new String();
  /**
   * class constructor
   */
  public CalcProgressBar(String frameMsg,String labelMsg){
    progress= new JProgressBar(0,100);
    //progress frame title
    frameMessage=frameMsg;
    label = new JLabel(labelMsg);
     // initiliaze the progress bar frame in which to show progress bar

    initProgressFrame();
  }

  /**
   * initialize the progress bar
   * Display "Updating forecast" initially
   */
  private void initProgressFrame() {
    this.setTitle(frameMessage);
    this.setLocation(this.FRAME_STARTX, this.FRAME_STARTY);
    this.setSize(this.FRAME_WIDTH, this.FRAME_HEIGHT);
    // make the progress bar
    progress.setStringPainted(true); // display the percentage completed also
    progress.setSize(FRAME_WIDTH-10, FRAME_HEIGHT-10);
    this.getContentPane().setLayout(new GridBagLayout());
    this.getContentPane().add(label, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
        ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(1, 2, 1, 2), 110, 10));
    this.setVisible(true);
    label.paintImmediately(label.getBounds());
  }


  /**
   * Updates the Progress Bar message
   * @param progressMsg
   */
  public void setProgressMessage(String progressMsg){
    label.setText(progressMsg);
    //this.setVisible(true);
    label.paintImmediately(label.getBounds());
  }

  /**
   * remove the "Updating forecast Label" and display the progress bar
   */
  public void displayProgressBar() {
    // now add the  progress bar
    label.setVisible(false);
    this.getContentPane().remove(label);
    this.getContentPane().add(this.progress, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
        ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(1, 2, 1, 2), 110, 10));
    this.getContentPane().remove(label);
    this.getContentPane().validate();
    this.getContentPane().repaint();
    //this.setVisible(true);
  }

  /**
   * update the progress bar with this new value and string
   *
   * @param val : Value of progress bar
   * @param str  : string to be displayed in progress bar
   */
  private  void updateProgressBar(int val, String str) {
    progress.setString(str);
    progress.setValue(val);
    Rectangle rect = progress.getBounds();
    //progress.paintImmediately(rect);
  }


  /**
   * update the calculation progress
   * @param num:    the current number
   * @param totNum: the total number
   */
  public void updateProgress(int num, int totNum) {

    //int val=0;
   // boolean update = false;

    // find if we're at a point to update
   /* if(num == (int) (totNum*0.9)) { // 90% complete
      val = 90;
      update = true;
    } else if(num == (int) (totNum*0.8)) { // 80% complete
      val = 80;
      update = true;
    } else if(num == (int) (totNum*0.7)) { // 70% complete
      val = 70;
      update = true;
    } else if(num == (int) (totNum*0.6)) { // 60% complete
      val = 60;
      update = true;
    } else if(num == (int) (totNum*0.5)) { // 50% complete
      val = 50;
      update = true;
    } else if(num == (int) (totNum*0.4)) { // 40% complete
      val = 40;
      update = true;
    } else if(num == (int) (totNum*0.3)) { // 30% complete
      val = 30;
      update = true;
    } else if(num == (int) (totNum*0.2)) { // 20% complete
      val = 20;
      update = true;
    } else if(num == (int) (totNum*0.1)) { // 10% complete
      val = 10;
      update = true;
    }*/
    // update the progress bar
    //if(update == true)
	if(totNum!=0)
		updateProgressBar((num*100)/totNum, num + "  of  " + Integer.toString(totNum) + "  Done");
    //this.setVisible(true);
  }

  public void showProgress(boolean flag){
    this.setVisible(flag);
    if(flag==false)
      this.dispose();
  }
}
