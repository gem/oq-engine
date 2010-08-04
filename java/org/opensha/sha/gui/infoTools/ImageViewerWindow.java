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
import java.awt.Color;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.FileOutputStream;
import java.io.IOException;
import java.net.URL;

import javax.swing.ImageIcon;
import javax.swing.JButton;
import javax.swing.JFileChooser;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JMenu;
import javax.swing.JMenuBar;
import javax.swing.JMenuItem;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JSplitPane;
import javax.swing.JTextPane;
import javax.swing.JToolBar;
import javax.swing.event.HyperlinkEvent;
import javax.swing.event.HyperlinkListener;

import org.apache.commons.lang.SystemUtils;
import org.opensha.commons.util.FileUtils;

import com.lowagie.text.Document;
import com.lowagie.text.DocumentException;
import com.lowagie.text.Image;
import com.lowagie.text.Paragraph;
import com.lowagie.text.pdf.PdfWriter;


/**
 * <p>Title: ImageViewerWindow</p>
 * <p>Description: this Class thye displays the image of the GMT Map in the
 * Frame window</p>
 * @author: Nitin Gupta & Vipin Gupta
 * @version 1.0
 */

public class ImageViewerWindow extends JFrame implements HyperlinkListener{
  private final static int W=650;
  private final static int H=730;


  private final static String MAP_WINDOW = "Maps using GMT";
  private JSplitPane mapSplitPane = new JSplitPane();
  private JScrollPane mapScrollPane = new JScrollPane();


  private boolean gmtFromServer = true;
  JMenuBar menuBar = new JMenuBar();
  JMenu fileMenu = new JMenu();

  JMenuItem fileSaveMenu = new JMenuItem();
  JToolBar jToolBar = new JToolBar();

  JButton saveButton = new JButton();
  ImageIcon saveFileImage = new ImageIcon(FileUtils.loadImage("icons/saveFile.jpg"));

  private String mapInfoAsHTML,mapInfoAsString;
  private BorderLayout borderLayout1 = new BorderLayout();
  private JScrollPane mapInfoScrollPane = new JScrollPane();
  private JPanel mapPanel = new JPanel();
  private GridBagLayout layout = new GridBagLayout();
  private JTextPane mapText = new JTextPane();
  //private final static String HTML_START = "<html><body>";
  //private final static String HTML_END = "</body></html>";

  //gets the image file names as URL to save as PDF
  private String[] imgFileNames;

  /**
   * Class constructor
   * @param imageFileName : Name of the image file to be shown
   * @param mapInfo : Metadata about the Map
   * @param gmtFromServer : boolean to check if map to be generated using the Server GMT
   * @throws RuntimeException
   */
  public ImageViewerWindow(String imageFileName,String mapInfoAsHTML,boolean gmtFromServer)
      throws RuntimeException{
    this.mapInfoAsHTML = mapInfoAsHTML;
    String lf = SystemUtils.LINE_SEPARATOR;
    this.mapInfoAsString = mapInfoAsHTML.replaceAll("<br>",lf);
    mapInfoAsString = mapInfoAsString.replaceAll("</br>","");
    mapInfoAsString = mapInfoAsString.replaceAll("<p>",lf);
    mapInfoAsString = mapInfoAsString.replaceAll("</p>","");
    mapInfoAsString = mapInfoAsString.replaceAll("&nbsp;","  ");
    this.gmtFromServer = gmtFromServer;
    imgFileNames = new String[1];
    imgFileNames[0] = imageFileName;
    try {
      jbInit();
    }catch(RuntimeException e) {
      throw new RuntimeException(e.getMessage());
    }
    addImageToWindow(imageFileName);
    this.setVisible(true);
  }

  /**
   * Class constructor
   * @param imageFileName : String array containing names of the image files to be shown(if
   * more than one image is to be shown in the same window.
   * @param mapInfo : Metadata about the Map
   * @param gmtFromServer : boolean to check if map to be generated using the Server GMT
   * @throws RuntimeException
   */
  public ImageViewerWindow(String[] imageFileNames,String mapInfo,
                           boolean gmtFromServer)
      throws RuntimeException{
    this.mapInfoAsHTML = mapInfo;
    String lf = SystemUtils.LINE_SEPARATOR;
    this.mapInfoAsString = mapInfoAsHTML.replaceAll("<br>",lf);
    mapInfoAsString = mapInfoAsString.replaceAll("</br>","");
    mapInfoAsString = mapInfoAsString.replaceAll("<p>",lf);
    mapInfoAsString = mapInfoAsString.replaceAll("</p>","");
    mapInfoAsString = mapInfoAsString.replaceAll("&nbsp;","  ");
    this.gmtFromServer = gmtFromServer;
    imgFileNames = imageFileNames;
    try {
      jbInit();
    }catch(RuntimeException e) {
      throw new RuntimeException(e.getMessage());
    }
    addImagesToWindow(imageFileNames);
    this.setVisible(true);
  }


  protected void jbInit() throws RuntimeException {
    this.setDefaultCloseOperation(DISPOSE_ON_CLOSE);
    this.setSize(W,H);
    this.setTitle(MAP_WINDOW);
    this.getContentPane().setLayout(borderLayout1);

    saveButton.addActionListener(new ActionListener() {
      public void actionPerformed(ActionEvent actionEvent) {
        saveButton_actionPerformed(actionEvent);
      }
    });
    fileSaveMenu.addActionListener(new java.awt.event.ActionListener() {
          public void actionPerformed(ActionEvent e) {
            fileSaveMenu_actionPerformed(e);
          }
    });
    fileSaveMenu.setText("Save");
    fileMenu.setText("File");
    menuBar.add(fileMenu);
    fileMenu.add(fileSaveMenu);

    setJMenuBar(menuBar);

    Dimension d = saveButton.getSize();
    jToolBar.add(saveButton);
    saveButton.setIcon(saveFileImage);
    saveButton.setToolTipText("Save Graph as image");
    saveButton.setSize(d);
    jToolBar.add(saveButton);
    jToolBar.setFloatable(false);

    this.getContentPane().add(jToolBar, BorderLayout.NORTH);

    mapSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);

    mapInfoScrollPane.getViewport().add(mapText, null);

    mapText.setContentType("text/html");
    mapText.setText(mapInfoAsHTML);
    mapText.setEditable(false);
    mapText.setForeground(Color.blue);
    mapText.setEditable(false);
    mapText.setSelectedTextColor(new Color(80, 80, 133));
    mapText.setSelectionColor(Color.blue);
    mapText.addHyperlinkListener(this);
    this.getContentPane().add(mapSplitPane, BorderLayout.CENTER);
    mapSplitPane.add(mapScrollPane, JSplitPane.TOP);
    mapSplitPane.add(mapInfoScrollPane, JSplitPane.BOTTOM);
    mapPanel.setLayout(layout);
    mapScrollPane.getViewport().add(mapPanel, null);
    mapSplitPane.setDividerLocation(480);
  }

  /**
   * This function plots all the images for the dataset in a single map window
   * @param imageURLs : String array of all the images URL/Absolute Path.
   */
  private void addImagesToWindow(String[] imageURLs){
    int size  = imageURLs.length;
    JLabel[] mapLabel = new JLabel[size];
    for(int i=0; i<size;++i){
      mapLabel[i] = new JLabel();
      if(gmtFromServer){
        try{
          mapLabel[i].setIcon(new ImageIcon(new URL((String)imageURLs[i])));
        }catch(Exception e){
          throw new RuntimeException("No Internet connection available");
        }
      }
      else
        mapLabel[i].setIcon(new ImageIcon((String)imageURLs[i]));
      mapPanel.add(mapLabel[i],new GridBagConstraints(0, i, 1, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(4, 3, 5, 5), 0, 0));
    }
  }


  /**
   * This function plots the image for the dataset in a single map window
   * @param imageFile : Absolute Path/URL to the image.
   */
  private void addImageToWindow(String imageFile){
    JLabel mapLabel = new JLabel();
    //adding the image to the label
    if(!this.gmtFromServer)
      mapLabel.setIcon(new ImageIcon(imageFile));
    else
      try{
      mapLabel.setIcon(new ImageIcon(new URL(imageFile)));
    }catch(Exception e){
      throw new RuntimeException("No Internet connection available");
    }
    mapPanel.add(mapLabel,new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
        ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(4, 3, 5, 5), 0, 0));
  }


  /**
   * Opens a file chooser and gives the user an opportunity to save the Image and Metadata
   * in PDF format.
   *
   * @throws IOException if there is an I/O error.
   */
  protected void save() throws IOException {
    JFileChooser fileChooser = new JFileChooser();
    int option = fileChooser.showSaveDialog(this);
    String fileName = null;
    if (option == JFileChooser.APPROVE_OPTION) {
      fileName = fileChooser.getSelectedFile().getAbsolutePath();
      if (!fileName.endsWith(".pdf"))
        fileName = fileName + ".pdf";
    }
    else {
      return;
    }
    saveAsPDF(fileName);
  }

  /**
   * Allows the user to save the image and metadata as PDF.
   * This also allows to preserve the color coding of the metadata.
   * @throws IOException
   */
  protected void saveAsPDF(String fileName) throws IOException {
    // step 1: creation of a document-object
    Document document = new Document();

    try {
      // step 2:
      // we create a writer that listens to the document
      // and directs a PDF-stream to a file
      PdfWriter writer = PdfWriter.getInstance(document, new FileOutputStream(fileName));
      writer.setStrictImageSequence(true);
      // step 3: we open the document
      document.open();
      // step 4: add the images to the

      int numImages = imgFileNames.length;
      for(int i=0;i<numImages;++i){
        Image img = Image.getInstance(new URL(imgFileNames[i]));
        img.setAlignment(Image.RIGHT);
        //img.scalePercent(95);
        document.add(img);
      }
      document.add(new Paragraph(mapInfoAsString));
    }
    catch (DocumentException de) {
      System.err.println(de.getMessage());
    }
    catch (IOException ioe) {
      System.err.println(ioe.getMessage());
    }

    // step 5: we close the document
    document.close();

  }

  /**
   * File | Save action performed.
   *
   * @param actionEvent ActionEvent
   */
  private void saveButton_actionPerformed(ActionEvent actionEvent) {
    try {
      save();
    }
    catch (IOException e) {
      JOptionPane.showMessageDialog(this, e.getMessage(), "Save File Error",
                                    JOptionPane.OK_OPTION);
      return;
    }
  }

  /**
   * File | Save action performed.
   *
   * @param actionEvent ActionEvent
   */
  private void fileSaveMenu_actionPerformed(ActionEvent actionEvent) {
    try {
      save();
    }
    catch (IOException e) {
      JOptionPane.showMessageDialog(this, e.getMessage(), "Save File Error",
                                    JOptionPane.OK_OPTION);
      return;
    }
  }


  /** This method implements HyperlinkListener.  It is invoked when the user
   * clicks on a hyperlink, or move the mouse onto or off of a link
   **/
  public void hyperlinkUpdate(HyperlinkEvent e) {
    HyperlinkEvent.EventType type = e.getEventType();  // what happened?
    if (type == HyperlinkEvent.EventType.ACTIVATED) {     // Click!
      try{
    	  edu.stanford.ejalbert.BrowserLauncher.openURL(e.getURL().toString());
      }catch(Exception ex) { ex.printStackTrace(); }

      //displayPage(e.getURL());   // Follow the link; display new page
    }
  }

}


