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

package org.opensha.sha.gui.beans;


import java.awt.Color;
import java.awt.Font;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.io.BufferedReader;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.StringTokenizer;

import javax.swing.BorderFactory;
import javax.swing.JCheckBox;
import javax.swing.JDialog;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.border.Border;
import javax.swing.border.TitledBorder;

import junk.nga.EqkRuptureFromNGA;

import org.opensha.commons.geo.Location;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.sha.earthquake.EqkRupture;


/**
 * <p>Title: ObservedRuptureSelectorGuiBean</p>
 * <p>Description: This class allows user to select from the list of
 *  observed earthquakes.</p>
 * @author : Nitin Gupta and Vipin Gupta
 * @version 1.0
 */

public class ObservedRuptureSelectorGuiBean extends JPanel implements ParameterChangeListener
{

  /**
   * Name of the class
   */
  protected final static String C = "ObservedRuptureSelectorGuiBean";
  // for debug purpose
  protected final static boolean D = false;

  private final static String EQK_RUP_SELECTOR_TITLE = "Set Observed Rupture";


  // Rupture Param Name
  public final static String RUPTURE_PARAM_NAME = "Rupture Index";


  //Object of ProbEqkRupture
  private EqkRuptureFromNGA rupture;


  private JScrollPane sourceRupInfoScroll = new JScrollPane();
  private JTextArea sourceRupInfoText = new JTextArea();

  //parameterList
  private ParameterList paramList;

  //ListEditor
  private ParameterListEditor listEditor;



  //Instance of the JDialog to show all the adjuatble params for the forecast model
  JDialog frame;
  private JCheckBox hypoCentreCheck = new JCheckBox();
  private GridBagLayout gridBagLayout1 = new GridBagLayout();

  private ArrayList eqkRuptureNames;

  private ArrayList ruptureList;


  //It is a file provided by the NGA , but have been modified
  public static final String NGA_SITES_DATA_FILE_NAME = "/Users/nitingupta/PEER_NGA_Data/nga_sites_data.txt";
  public static final double DEFAULT_RAKE = 90;
  public static final double DEFAULT_Vs30 = 180;


  /**
   * Class constructor takes in the observed earthquake list
   * @param ruptureList
   */
  public ObservedRuptureSelectorGuiBean(ArrayList ruptureList) {
    eqkRuptureNames = new ArrayList();
    this.ruptureList = ruptureList;
    int size = ruptureList.size();

    for(int i=0;i<size;++i)
      eqkRuptureNames.add(((EqkRuptureFromNGA)ruptureList.get(i)).getEqkName());

    try {
      jbInit();
    }
    catch(Exception e) {
      e.printStackTrace();
    }

    this.setSelectedRupture();
    this.getSelectedRuptureInfo();
    readSiteInfoFromFile();
  }





  /**
   * Reads the rupture info from the each site that rupture was observed
   */
  public void readSiteInfoFromFile(){

    String eqkId = rupture.getEqkId();
    boolean readSitesFlag = true;

    try{

    //reading all the sites data for the earthquake id
    //reading the file that provides the site specific about the rupture
    FileReader fr_sites = new FileReader(NGA_SITES_DATA_FILE_NAME);
    BufferedReader br_sites = new BufferedReader(fr_sites);
    String lineFromSiteFile = br_sites.readLine();
    //reading each line of the file to get all the sites info.
    //corresponding to the earthquake.
    while(lineFromSiteFile !=null && readSitesFlag){
      if(lineFromSiteFile.startsWith("#") || lineFromSiteFile.equals("\n") || lineFromSiteFile.equals("")){
        lineFromSiteFile = br_sites.readLine();
        continue;
      }
      StringTokenizer st_sites = new StringTokenizer(lineFromSiteFile,",");
      String id = st_sites.nextToken().trim();
      //Id is the first thing in the line that we read from the site info file.
      if(id.equals(eqkId)){//if both id matches then create get the sites info for that quake
        ArrayList rakeList = new ArrayList();
        ArrayList vs30List = new ArrayList();
        ArrayList locationList = new ArrayList();
        while(id.equals(eqkId)){

          String rakeString =st_sites.nextToken().trim();
          //getting the rake as observed by different sites, but if not provide then give it a default value of 90.
          if(rakeString !=null && !rakeString.equals(""))
            rakeList.add(new Double(Double.parseDouble(rakeString)));
          else
            rakeList.add(new Double(this.DEFAULT_RAKE));

          //getting the preffered NEHRP based vs30, currently discarding it because it is integer format
          st_sites.nextToken().trim();

          //getting the preffered Vs30 from the file
          String vs30String =st_sites.nextToken().trim();

          //getting the Vs30 as observed by different sites, but if not provide then give it a default value of 180.
          if(vs30String !=null && !vs30String.equals(""))
            //adding the vs30 value to he ruoture sites, if not provided then giving it a default it
            vs30List.add(new Double(Double.parseDouble(vs30String)));
          else
            vs30List.add(new Double(this.DEFAULT_Vs30));

          //getting the site Location
          double siteLat = Double.parseDouble(st_sites.nextToken().trim());
          double siteLon = Double.parseDouble(st_sites.nextToken().trim());
          Location siteLoc = new Location(siteLat,siteLon);
          //adding the site to the observed rupture site list.
          locationList.add(siteLoc);
          lineFromSiteFile = br_sites.readLine();
          st_sites = new StringTokenizer(lineFromSiteFile,",");
          id = st_sites.nextToken().trim();
        }
        readSitesFlag = false;
        rupture.addSite(locationList);
        rupture.addSiteVs30(vs30List);
        rupture.addSiteRake(rakeList);
      }
      else{ //if id doesn't match the read the next line.
        lineFromSiteFile = br_sites.readLine();
        continue;
      }
    }
    br_sites.close();
    fr_sites.close();
    }catch(Exception e){
      e.printStackTrace();
    }
  }





 /**
  *  This is the main function of this interface. Any time a control
  *  paramater or independent paramater is changed by the user in a GUI this
  *  function is called, and a paramater change event is passed in. This
  *  function then determines what to do with the information ie. show some
  *  paramaters, set some as invisible, basically control the paramater
  *  lists.
  *
  * @param  event
  */
 public void parameterChange( ParameterChangeEvent event ) {

   String S = C + ": parameterChange(): ";
   if ( D )
     System.out.println( "\n" + S + "starting: " );

   String name1 = event.getParameterName();

   // if ERF selected by the user  changes

   // if source selected by the user  changes
   if( name1.equals(this.RUPTURE_PARAM_NAME) ){
     this.setSelectedRupture();
     getSelectedRuptureInfo();
     readSiteInfoFromFile();
   }
 }

   private void jbInit() throws Exception {

     StringParameter ruptureParam = new StringParameter(this.RUPTURE_PARAM_NAME,this.eqkRuptureNames,
         (String)eqkRuptureNames.get(0));
     paramList = new ParameterList();
    paramList.addParameter(ruptureParam);
    ruptureParam.addParameterChangeListener(this);
    this.setLayout(gridBagLayout1);
    sourceRupInfoText.setLineWrap(true);
    sourceRupInfoText.setForeground(Color.blue);
    sourceRupInfoText.setSelectedTextColor(new Color(80, 80, 133));
    sourceRupInfoText.setSelectionColor(Color.blue);
    sourceRupInfoText.setEditable(false);

    listEditor = new ParameterListEditor(paramList);
    this.add(listEditor,  new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
        ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(4, 4, 4, 4), 0, 0));
    this.add(sourceRupInfoScroll,  new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0
        ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(4, 4, 4, 4), 0, 0));
    sourceRupInfoScroll.getViewport().add(sourceRupInfoText, null);

    // get the panel for increasing the font and border
    // this is hard coding for increasing the IMR font
    // the colors used here are from ParameterEditor
    JPanel panel = listEditor.getParameterEditor(RUPTURE_PARAM_NAME).getOuterPanel();
    TitledBorder titledBorder1 = new TitledBorder(BorderFactory.createLineBorder(new Color( 80, 80, 140 ),3),"");
    titledBorder1.setTitleColor(new Color( 80, 80, 140 ));
    Font DEFAULT_LABEL_FONT = new Font( "SansSerif", Font.BOLD, 13 );
    titledBorder1.setTitleFont(DEFAULT_LABEL_FONT);
    titledBorder1.setTitle(RUPTURE_PARAM_NAME);
    Border border1 = BorderFactory.createCompoundBorder(titledBorder1,BorderFactory.createEmptyBorder(0,0,3,0));
    panel.setBorder(border1);
    this.add(listEditor,  new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
        ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(4, 4, 4, 4), 0,0));
    this.validate();
    this.repaint();
  }


  public void getSelectedRuptureInfo(){
    //writing the ruptures info. for each selected source in the text Area below the rupture
    String rupturesInfo = "Rupture info ";
    rupturesInfo += ":\n";
    rupturesInfo += ""+((EqkRuptureFromNGA)rupture).getInfo();
    sourceRupInfoText.setText(rupturesInfo);
  }


  /**
   * From the list of the selected rupture name sets the on selected
   */
  private void setSelectedRupture(){
    String eqkRuptureName = (String)paramList.getParameter(this.RUPTURE_PARAM_NAME).getValue();
    int size = this.eqkRuptureNames.size();

    int i=0;
    for(;i<size;++i){
      if(((String)eqkRuptureNames.get(i)).equals(eqkRuptureName))
        break;
    }
    rupture = (EqkRuptureFromNGA)ruptureList.get(i);
  }

  /**
   *
   * @returns the selected Rupture
   */
  public EqkRupture getSelectedRupture(){
    return rupture;
  }


  /**
   *
   * @returns the Metadata String of parameters that constitute the making of this
   * ERF_RupSelectorGUI  bean.
   */
  public String getParameterListMetadataString(){
    return null;
  }


  /**
   *
   * @param : Name of the Parameter
   * @returns the parameter with the name param
   */
  public ParameterAPI getParameter(String param){
    return listEditor.getParameterList().getParameter(param);
  }


  /**
   *
   * @returns the EqkRupture
   */
  public EqkRupture getRupture(){
    return rupture;
  }


  //returns the parameterListEditor
  public ParameterListEditor getParameterListEditor(){
    return listEditor;
  }

}
