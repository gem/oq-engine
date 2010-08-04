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
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.net.URL;
import java.util.ArrayList;

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
import javax.swing.JTabbedPane;
import javax.swing.JTextPane;
import javax.swing.JToolBar;
import javax.swing.event.HyperlinkEvent;
import javax.swing.event.HyperlinkListener;

import org.jpedal.PdfDecoder;
import org.opensha.commons.util.FileUtils;

import com.lowagie.text.Document;
import com.lowagie.text.DocumentException;
import com.lowagie.text.Paragraph;
import com.lowagie.text.pdf.PRAcroForm;
import com.lowagie.text.pdf.PdfCopy;
import com.lowagie.text.pdf.PdfImportedPage;
import com.lowagie.text.pdf.PdfReader;
import com.lowagie.text.pdf.PdfWriter;
import com.lowagie.text.pdf.SimpleBookmark;


/**
 * <p>Title: DisaggregationPlotViewerWindow</p>
 * <p>Description: this Class thye displays the image of the GMT Map in the
 * Frame window</p>
 * @author: Nitin Gupta & Vipin Gupta
 * @version 1.0
 */

public class DisaggregationPlotViewerWindow extends JFrame implements HyperlinkListener{
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


  private BorderLayout borderLayout1 = new BorderLayout();
  private JPanel mapPanel = new JPanel();
  private GridBagLayout layout = new GridBagLayout();
  //private JTextPane mapText = new JTextPane();
  //private final static String HTML_START = "<html><body>";
  //private final static String HTML_END = "</body></html>";

  //gets the image file name as URL to save as PDF
  private String imgFileName;

  //creates the tab panes for the user to view different information for the
  //disaggregation plot
  private JTabbedPane infoTabPane = new JTabbedPane();
  //If disaggregation info needs to be scrolled
  private JScrollPane meanModeScrollPane = new JScrollPane();
  private JScrollPane metadataScrollPane = new JScrollPane();
  private JScrollPane sourceListDataScrollPane;
  private JScrollPane binnedDataScrollPane;

  //TextPane to show different disaggregation information
  private JTextPane meanModePane = new JTextPane();
  private JTextPane metadataPane = new JTextPane();
  private JTextPane sourceListDataPane;
  private JTextPane binnedDataPane;

  //Strings for getting the different disaggregation info.
  private String meanModeText,metadataText,binDataText,sourceDataText;


  /**
   * Class constructor
   * @param imageFileName : Name of the image file to be shown
   * @param mapInfo : Metadata about the Map
   * @param gmtFromServer : boolean to check if map to be generated using the Server GMT
   * @throws RuntimeException
   */
  public DisaggregationPlotViewerWindow(String imageFileName,
                                        boolean gmtFromServer,
                                        String meanModeString, String metadataString,
                                        String binDataString, String sourceDataString)
      throws RuntimeException{

    meanModeText = meanModeString;
    metadataText = metadataString;
    binDataText = binDataString;
    sourceDataText = sourceDataString;
    this.gmtFromServer = gmtFromServer;
    imgFileName = imageFileName;
    try {
      jbInit();

      //show the bin data only if it is not  null
      if(binDataString !=null && !binDataString.trim().equals("")){
        binnedDataScrollPane = new JScrollPane();
        binnedDataPane = new JTextPane();
        //adding the text pane for the bin data
        infoTabPane.addTab("Bin Data", binnedDataScrollPane);
        binnedDataScrollPane.getViewport().add(binnedDataPane, null);
        binnedDataPane.setForeground(Color.blue);
        binnedDataPane.setText(binDataText);
        binnedDataPane.setEditable(false);
      }

      //show the source list metadata only if it not null
      if(sourceDataString !=null && !sourceDataString.trim().equals("")){
        sourceListDataScrollPane = new JScrollPane();
        sourceListDataPane = new JTextPane();
        //adding the text pane for the source list data
        infoTabPane.addTab("Source List Data", sourceListDataScrollPane);
        sourceListDataScrollPane.getViewport().add(sourceListDataPane, null);
        sourceListDataPane.setForeground(Color.blue);
        sourceListDataPane.setText(sourceDataText);
        sourceListDataPane.setEditable(false);
      }

    }catch(RuntimeException e) {
      e.printStackTrace();
      throw new RuntimeException(e.getMessage());
    }
    //addImageToWindow(imageFileName);
    addPdfImageToWindow(imageFileName);
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
    //adding the mean/mode and metadata info tabs to the window
    infoTabPane.addTab("Mean/Mode", meanModeScrollPane);
    infoTabPane.addTab("Metadata", metadataScrollPane);
    meanModeScrollPane.getViewport().add(meanModePane,null);
    metadataScrollPane.getViewport().add(metadataPane,null);

    //adding the metadata text to the metatada info window
    metadataPane.setContentType("text/html");
    metadataPane.setForeground(Color.blue);
    metadataPane.setText(metadataText);
    metadataPane.setEditable(false);
    metadataPane.addHyperlinkListener(this);

    //adding the meanMode text to the meanMode info window
    meanModePane.setForeground(Color.blue);
    meanModePane.setText(meanModeText);
    meanModePane.setEditable(false);

    this.getContentPane().add(mapSplitPane, BorderLayout.CENTER);
    mapSplitPane.add(mapScrollPane, JSplitPane.TOP);
    mapSplitPane.add(infoTabPane, JSplitPane.BOTTOM);
    infoTabPane.setTabPlacement(JTabbedPane.BOTTOM);
    mapPanel.setLayout(layout);
    mapScrollPane.getViewport().add(mapPanel, null);
    mapSplitPane.setDividerLocation(480);
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
   * Displays the PDF file to the user in the window
   * @param fileName String URL to the PDF filename
   */
  private void addPdfImageToWindow(String fileName){
    int currentPage = 1;
    PdfDecoder pdfDecoder = new PdfDecoder();

    try {
      //this opens the PDF and reads its internal details
      pdfDecoder.openPdfFileFromURL(fileName);

      //these 2 lines opens page 1 at 100% scaling
      pdfDecoder.decodePage(currentPage);
      pdfDecoder.setPageParameters(1, 1); //values scaling (1=100%). page number
    }
    catch (Exception e) {
      e.printStackTrace();
    }

    //setup our GUI display
    mapScrollPane.setViewportView(pdfDecoder);
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
    //document for temporary storing the metadata as pdf-file
    Document document_temp = new Document();
    //String array to store the 2 pdfs
    String[] pdfFiles = new String[2];
    try {

      String disaggregationInfoString = "Mean/Mode Metadata :\n"+meanModeText+
          "\n\n"+"Disaggregation Plot Parameters Info :\n"+
          metadataText+"\n\n"+"Disaggregation Bin Data :\n"+binDataText+"\n\n"+
          "Disaggregation Source List Info:\n"+sourceDataText;

      pdfFiles[0] = imgFileName;
      pdfFiles[1] = fileName+".tmp";
      //creating the temp data pdf for the Metadata
      PdfWriter.getInstance(document_temp,
                                               new FileOutputStream(pdfFiles[1]));
      document_temp.open();
      document_temp.add(new Paragraph(disaggregationInfoString));
      document_temp.close();

      //concating the PDF files, one is the temporary pdf file that was created
      //for storing the metadata, other is the Disaggregation plot image pdf file
      //which is read as URL.
      int pageOffset = 0;
      ArrayList master = new ArrayList();
      int f = 0;

      PdfCopy writer = null;
      while (f < pdfFiles.length) {
        // we create a reader for a certain document
        PdfReader reader = null;
        if(f ==0)
          reader = new PdfReader(new URL(pdfFiles[f]));
        else
          reader = new PdfReader(pdfFiles[f]);

        reader.consolidateNamedDestinations();
        // we retrieve the total number of pages
        int n = reader.getNumberOfPages();
        java.util.List bookmarks = SimpleBookmark.getBookmark(reader);
        if (bookmarks != null) {
          if (pageOffset != 0)
            SimpleBookmark.shiftPageNumbers(bookmarks, pageOffset, null);
          master.addAll(bookmarks);
        }
        pageOffset += n;

        if (f == 0) {
          // step 1: creation of a document-object
          document = new Document(reader.getPageSizeWithRotation(1));
          // step 2: we create a writer that listens to the document
          writer = new PdfCopy(document, new FileOutputStream(fileName));
          // step 3: we open the document
          document.open();
        }
        // step 4: we add content
        PdfImportedPage page;
        for (int i = 0; i < n; ) {
          ++i;
          page = writer.getImportedPage(reader, i);
          writer.addPage(page);
        }
        PRAcroForm form = reader.getAcroForm();
        if (form != null)
          writer.copyAcroForm(reader);
        f++;
      }
      if (master.size() > 0)
        writer.setOutlines(master);
      // step 5: we close the document
      document.close();

    }
    catch (DocumentException de) {
      System.err.println(de.getMessage());
    }
    catch (IOException ioe) {
      System.err.println(ioe.getMessage());
    }

    //deleting the temporary PDF file that was created for storing the metadata
    File f = new File(pdfFiles[1]);
    f.delete();
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
    catch (Exception e) {
      e.printStackTrace();
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
//       org.opensha.util.BrowserLauncher.openURL(e.getURL().toString());
       edu.stanford.ejalbert.BrowserLauncher.openURL(e.getURL().toString());
      }catch(Exception ex) { ex.printStackTrace(); }

      //displayPage(e.getURL());   // Follow the link; display new page
    }
  }

}


