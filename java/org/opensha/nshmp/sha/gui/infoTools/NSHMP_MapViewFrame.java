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

package org.opensha.nshmp.sha.gui.infoTools;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.awt.event.MouseListener;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JList;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JSplitPane;
import javax.swing.ListSelectionModel;

import edu.stanford.ejalbert.BrowserLauncher;

/**
 * <p>Title: NSHMP_MapViewFrame</p>
 *
 * <p>Description: This class shows the listing of the maps that user can view and
 * print.</p>
 * @author Ned Field, Nitin Gupta and E.V.Leyendecker
 * @version 1.0
 */
public class NSHMP_MapViewFrame
    extends JFrame {

  JSplitPane mapButtonsSplitPane = new JSplitPane();
  JPanel mapListPanel = new JPanel();
  JList mapList = new JList();
  JPanel buttonPanel = new JPanel();
  JButton viewMapButton = new JButton();
  GridBagLayout gridBagLayout1 = new GridBagLayout();
  GridBagLayout gridBagLayout2 = new GridBagLayout();
  BorderLayout borderLayout1 = new BorderLayout();
  JScrollPane dataScrollPane = new JScrollPane();

  //Pdf map files
  private String[] mapFiles;

  /**
   * Constructor for the PDF Map Viewing Window.
   * It shows the list of maps for the user to choose from, then launches the Acrobat
   * Reader to view the selected map.
   * @param availableMapsList String[] : Info about the Maps, user selects one of the provided
   * choice and clicks on the "View Map" button. For the selected choice it then launches
   * the Acrobat PDF Viewer to view the map.
   * @param mapFiles String[] : URLs to the PDF map files corresponding to the
   * available map list.
   */
  public NSHMP_MapViewFrame(String[] availableMapsList, String[] mapFiles) {
    try {
      jbInit();
    }
    catch (Exception exception) {
      exception.printStackTrace();
    }
    createListofAvailableMaps(availableMapsList,mapFiles);
  }

  private void jbInit() throws Exception {
    getContentPane().setLayout(borderLayout1);
    mapButtonsSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);
    mapListPanel.setLayout(gridBagLayout2);
    mapList.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
    buttonPanel.setLayout(gridBagLayout1);
    viewMapButton.setText("View Map");
    buttonPanel.setMinimumSize(new Dimension(1, 1));
    mapButtonsSplitPane.add(buttonPanel, JSplitPane.BOTTOM);
    mapButtonsSplitPane.add(mapListPanel, JSplitPane.TOP);
    buttonPanel.add(viewMapButton, new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
        , GridBagConstraints.CENTER, GridBagConstraints.NONE,
        new Insets(4, 4, 4, 4), 0, 0));
    mapListPanel.add(dataScrollPane, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
        , GridBagConstraints.CENTER, GridBagConstraints.BOTH,
        new Insets(0, 0, 0,0), 0, 0));
    dataScrollPane.getViewport().add(mapList, null);
    this.getContentPane().add(mapButtonsSplitPane, java.awt.BorderLayout.CENTER);
    mapButtonsSplitPane.setDividerLocation(400);
    buttonPanel.setMinimumSize(new Dimension(4,4));
    mapListPanel.setMinimumSize(new Dimension(4,4));
    viewMapButton.addActionListener(new ActionListener() {
      public void actionPerformed(ActionEvent actionEvent) {
        viewMapButton_actionPerformed(actionEvent);
      }
    });

    MouseListener mouseListener = new MouseAdapter() {
      public void mouseClicked(MouseEvent e) {
        if (e.getClickCount() == 2) {
          viewMaps();
        }
      }
    };
    mapList.addMouseListener(mouseListener);
    mapList.setForeground(Color.BLUE);
    mapList.setFont(new Font("Arial",Font.BOLD,14));
    this.setTitle("PGA and SA Maps");
    this.setLocation( 150,40);
    this.setSize(600,500);
  }

  /**
   * This function displays the list of the maps that user can view
   */
  private void viewMaps(){
    int selectedIndex = mapList.getSelectedIndex();
    String fileToRead = mapFiles[selectedIndex];
    try {
        BrowserLauncher bl = new BrowserLauncher();
        bl.openURLinBrowser(fileToRead);
    }
    catch (Exception ex) {
      ex.printStackTrace();
    }
  }

  /*
   *
   * @param actionEvent ActionEvent
   */
  private void viewMapButton_actionPerformed(ActionEvent actionEvent) {
    viewMaps();
  }

  /*
   * Create the List to be shown to the user for the available pdf maps
   * @param availableMapsList String[]
   * @param mapFiles String[]
   */
  public void createListofAvailableMaps(String[] availableMapsList,
                                         String[] mapFiles
      ) {
    this.mapFiles = mapFiles;
    mapList.setListData(availableMapsList);
  }
}

