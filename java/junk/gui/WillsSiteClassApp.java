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

package junk.gui;

import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.util.ArrayList;
import java.util.StringTokenizer;

import javax.swing.JApplet;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.UIManager;

import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.sha.gui.infoTools.ConnectToCVM;



/**
 * <p>Title: WillsSiteClassApp</p>
 * <p>Description: This window allows the user to enter List of Lat-Lons and this application will
 * retrieve Wills Site class for them and show it in a seperete window.</p>
 * @author Nitin Gupta
 * @version 1.0
 */

public class WillsSiteClassApp extends JApplet{
 

  private JScrollPane locListScrollPane = new JScrollPane();
  private JTextArea locsTextArea = new JTextArea();
  private JLabel enterLocs = new JLabel("Enter Locations: ");
  private JLabel exampleLocs = new JLabel();

  private JButton getWillsSiteClassButton = new JButton();
  private boolean isStandalone = false;

 
  //Start the applet
  public void start() {
  }

  //Stop the applet
  public void stop() {
  }

  //Destroy the applet
  public void destroy() {
  }
  
  
  public void init(){
	  try{
		 jbInit(); 
	  }catch(Exception e){
		  
	  }
  }
  private void jbInit() throws Exception {
 
    this.setLayout(new BorderLayout());
    this.getContentPane().setLayout(new GridBagLayout());
    
    getWillsSiteClassButton.setText("Get Wills Site Class");
    getWillsSiteClassButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
    	  getWillsSiteClassButton_actionPerformed(e);
      }
    });
    this.getContentPane().add(enterLocs,  new GridBagConstraints(0,0 , 1, 1, 1.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(0, 0, 0, 0), 0, 0));
    exampleLocs.setText("Enter Location Per Line Example:");
    exampleLocs.setToolTipText("Enter one Location per line \n"+
    		"and one can enter as many location as one wants");
    JLabel firstLocExample = new JLabel();
    firstLocExample.setText("34.00   -118.20");
    JLabel secLocExample = new  JLabel();
    secLocExample.setText("34.40   -119.00");
    
    this.getContentPane().add(exampleLocs,  new GridBagConstraints(0,1 , 1, 1, 1.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(0, 0, 0, 0), 0, 0));
    this.getContentPane().add(firstLocExample,  new GridBagConstraints(0,2 , 1, 1, 1.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 0, 0, 0), 0, 0));
    this.getContentPane().add(secLocExample,  new GridBagConstraints(0,3 , 1, 1, 1.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 0, 0, 0), 0, 0));
    this.getContentPane().add(locListScrollPane,  new GridBagConstraints(0,4 , 1, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(0, 0, 0, 0), 214, 15));
    
    this.getContentPane().add(getWillsSiteClassButton,  new GridBagConstraints(0, 5, 1, 1, 1.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 0, 0, 0), 0, 0));
    
    locListScrollPane.getViewport().add(locsTextArea, null);
    String info = new String("This uses both the CGS Preliminary Site "+
            "Conditions Map of CA (Wills et al., 2000) ");
    getWillsSiteClassButton.setToolTipText(info);
   }


  /**
   * Retrives the Wills Site class values for the list of locations entered by the user.
   * @param e
   */
  void getWillsSiteClassButton_actionPerformed(ActionEvent e) {
	  LocationList locs = getLocs();
	  if(locs.size() >0){
		  ArrayList willsSiteClassList = null;
		  try{
		      //getting the wills site class values from servlet
		      willsSiteClassList = ConnectToCVM.getWillsSiteTypeFromCVM(locs);
		    }catch(Exception ee){
		     	JOptionPane.showMessageDialog(this,"Error connecting to the SCEC WebServer","Network Problem",
		  				JOptionPane.INFORMATION_MESSAGE);
		     	return;
		    }
		    showWillsSiteClassValsInWindow(willsSiteClassList);
	  }
  }

  /**
   * Shows the Wills Site Class values retrieved from the webservice.
   *
   */
  private void showWillsSiteClassValsInWindow(ArrayList willsSiteClassList){
	  JFrame willSiteClassFrame = new JFrame();
	  willSiteClassFrame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
	  willSiteClassFrame.setTitle("Wills Class Values");
	  willSiteClassFrame.setLayout(new BorderLayout());
	  willSiteClassFrame.getContentPane().setLayout(new GridBagLayout());
	  JScrollPane willsSiteValsScroll =  new JScrollPane();
	  JTextArea willsSiteValsText = new JTextArea();
	  willsSiteValsText.setEditable(false);
	  String willSiteClassVals="";
	  int size = willsSiteClassList.size();
	  String locs = locsTextArea.getText();
	  StringTokenizer st = new StringTokenizer(locs,"\n");
	  for(int i=0;i<size;++i){
		  String willsVal = (String)willsSiteClassList.get(i);
		  if(willsVal.equals("NA"))
			  willsVal = "Not Available";
  		  willSiteClassVals +=st.nextToken()+"  "+willsVal+"\n";
	  }
	  
	  String infoText = "#Lat Lon WillsSiteClass-Value\n";
	  willsSiteValsText.setText(infoText+willSiteClassVals);
	  willSiteClassFrame.getContentPane().add(willsSiteValsScroll,  new GridBagConstraints(0,0 , 1, 1, 1.0, 1.0
	            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(0, 0, 0, 0), 214, 15));
	    
	  willsSiteValsScroll.getViewport().add(willsSiteValsText, null);
	  willSiteClassFrame.setSize(200,360);
	  // show the window at center of the parent component
	  willSiteClassFrame.setLocation(this.getX()+this.getWidth()/2,
                       this.getY()+this.getHeight()/2);
	  willSiteClassFrame.setVisible(true);
  }
  
/**
 * Creates the LocationList from the location entered by the user in the TextArea.
 * @return
 */
  private LocationList getLocs(){
	  LocationList locs = new LocationList();
	  String locsText = locsTextArea.getText();
	  if(locsText ==null || locsText.trim().equals("")){
		JOptionPane.showMessageDialog(this,"Please Enter valid Locations in text Area, see example","Input Error",
				JOptionPane.ERROR_MESSAGE);
		
		return locs;
	  }
	  //getting the locations entered by the user in the textArea and adding it the locList object.
	  	StringTokenizer st = new StringTokenizer(locsText,"\n");
	    while(st.hasMoreTokens()){
	
	      StringTokenizer st1 = new StringTokenizer(st.nextToken());
	      int numVals = st1.countTokens();
	      if(numVals !=2){
	    	  JOptionPane.showMessageDialog(this,"Each line should have just one Lat and "+
	                  "one Lon value.\nPlease see exmaple above and enter just one location per line","Input Error",
	  				JOptionPane.ERROR_MESSAGE);
	        return locs;
	      }
	      double lat=0;
	      double lon=0;
	      try{
	        lat = Double.parseDouble(st1.nextToken());
	        lon = Double.parseDouble(st1.nextToken());
	      }catch(NumberFormatException e){
	    	  JOptionPane.showMessageDialog(this,"Lat and Lon Values entered must be valid numbers","Input Error",
	  				JOptionPane.ERROR_MESSAGE);
	        return locs;
	      }
	      locs.add(new Location(lat,lon));
	    }
	    return locs;
  }

  /**
   * 
   * application main method
   * @param args
   */
  public static void main(String[] args) {
	  WillsSiteClassApp application = new WillsSiteClassApp();
	  application.isStandalone = true;
    JFrame frame = new JFrame();
    //EXIT_ON_CLOSE == 3
    frame.setDefaultCloseOperation(3);
    frame.setTitle("Wills Site Class Application");
    frame.getContentPane().add(application, BorderLayout.CENTER);
    application.init();
    frame.setSize(300, 400);
    Dimension d = Toolkit.getDefaultToolkit().getScreenSize();
    frame.setLocation((d.width - frame.getSize().width) / 2, (d.height - frame.getSize().height) / 2);
    frame.setVisible(true);
  }
 
  //static initializer for setting look & feel
  static {
    String osName = System.getProperty("os.name");
    try {
        UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
    }
    catch(Exception e) {
    }
  }

  
}
