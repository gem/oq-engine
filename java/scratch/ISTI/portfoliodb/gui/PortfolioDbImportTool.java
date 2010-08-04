package scratch.ISTI.portfoliodb.gui;

import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseEvent;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.Reader;
import java.io.Writer;
import java.sql.Connection;

import javax.swing.JButton;
import javax.swing.JFileChooser;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTable;
import javax.swing.SwingUtilities;
import javax.swing.event.TableModelEvent;
import javax.swing.table.JTableHeader;

import scratch.ISTI.portfoliodb.PortfolioDatabase;

import com.isti.util.DelimiterSeparatedValues;
import com.isti.util.DelimiterSeparatedValuesTable;
import com.isti.util.IstiFileFilter;
import com.isti.util.ValueTableModel;
import com.isti.util.gui.GuiUtilFns;
import com.isti.util.gui.ValueJTableModel;

public class PortfolioDbImportTool
{
  /** Default frame size. */
  private static final int DEF_FRAME_WIDTH = 1100;
  private static final int DEF_FRAME_HEIGHT = 780;

  private PortfolioDbConnectionInfoDialog _connectionInfoDialog = null;
  private final JFileChooser chooser;
  private final JFrame frameObj;
  private final PortfolioDatabase pdit;
  private final ValueTableModel svt;
  private final ValueJTableModel vgtm;
  private final JButton editButton;
  private final JButton cancelButton;
  private final JButton clearButton;
  private final JButton importButton;
  private final JButton exportButton;
  private final JButton readDbButton;
  private final JButton writeDbButton;
  private final JButton validateButton;

  public PortfolioDbImportTool()
  {
    chooser = new JFileChooser();
    chooser.setFileSelectionMode(JFileChooser.FILES_ONLY);
    final IstiFileFilter filter = new IstiFileFilter(
        new String[]
        {"*.csv"}, "CSV");
    chooser.addChoosableFileFilter(filter);
    chooser.setCurrentDirectory(new File(".").getAbsoluteFile());
    pdit = new PortfolioDatabase();
    svt = pdit.getValueTableModel();
    vgtm = new ValueJTableModel(svt);

    //add main content panel to frame:
    final JTable tableObj = new JTable(vgtm);
    tableObj.setTableHeader(new JTableHeader(tableObj.getTableHeader().
                                             getColumnModel())
    {
      public String getToolTipText(MouseEvent e)
      {
        String tip = super.getToolTipText(e);
        final int index = columnModel.getColumnIndexAtX(e.getPoint().x);
        if (index >= 0)
        {
          final int realIndex =
              columnModel.getColumn(index).getModelIndex();
          tip = svt.getColumnName(realIndex);
        }
        return tip;
      }
    });
    tableObj.putClientProperty("terminateEditOnFocusLost", Boolean.TRUE);
    final JScrollPane scrollPaneObj =
        new JScrollPane(tableObj);
    //create and set up the frame
    frameObj = new JFrame("PortfolioDbImportTool");
    final JPanel panelObj = new JPanel(new BorderLayout());
    final Dimension frameDimension =
        new Dimension(DEF_FRAME_WIDTH, DEF_FRAME_HEIGHT);
    frameObj.setPreferredSize(frameDimension);
    panelObj.add(scrollPaneObj, BorderLayout.CENTER);
    final JPanel bottomPanelObj = new JPanel();

    editButton = new JButton("Edit");
    editButton.setEnabled(false);
    editButton.setToolTipText("Edit data");
    editButton.addActionListener(new ActionListener()
    {
      public void actionPerformed(ActionEvent evt)
      {
        setEditable(true);
      }
    });
    bottomPanelObj.add(editButton);

    cancelButton = new JButton("Cancel");
    cancelButton.setEnabled(false);
    cancelButton.setToolTipText("Cancel editing and clears the loaded data");
    cancelButton.addActionListener(new ActionListener()
    {
      public void actionPerformed(ActionEvent evt)
      {
        clearData(true, evt);
      }
    });
    bottomPanelObj.add(cancelButton);

    clearButton = new JButton("Clear Data");
    clearButton.setEnabled(false);
    clearButton.setToolTipText("Clears the loaded data");
    clearButton.addActionListener(new ActionListener()
    {
      public void actionPerformed(ActionEvent evt)
      {
        clearData(true, evt);
      }
    });
    bottomPanelObj.add(clearButton);

    importButton = new JButton("Import");
    importButton.setToolTipText("Import data from a CSV file");
    importButton.addActionListener(new ActionListener()
    {
      public void actionPerformed(ActionEvent evt)
      {
        clearData(false, evt);
        importData(evt);
      }
    });
    bottomPanelObj.add(importButton);

    exportButton = new JButton("Export");
    exportButton.setEnabled(false);
    exportButton.setToolTipText("Export data to a CSV file");
    exportButton.addActionListener(new ActionListener()
    {
      public void actionPerformed(ActionEvent evt)
      {
        exportData(evt);
      }
    });
    bottomPanelObj.add(exportButton);

    readDbButton = new JButton("Read DB");
    readDbButton.setToolTipText("Read data from the database");
    readDbButton.addActionListener(new ActionListener()
    {
      public void actionPerformed(ActionEvent evt)
      {
        clearData(false, evt);
        readDatabase(evt);
      }
    });
    bottomPanelObj.add(readDbButton);

    writeDbButton = new JButton("Write DB");
    writeDbButton.setEnabled(false);
    writeDbButton.setToolTipText("Write data to the database");
    writeDbButton.addActionListener(new ActionListener()
    {
      public void actionPerformed(ActionEvent evt)
      {
        writeDatabase(evt);
      }
    });
    bottomPanelObj.add(writeDbButton);

    validateButton = new JButton("Validate");
    validateButton.setEnabled(false);
    validateButton.setToolTipText("Validate data - to be implemented");
    validateButton.addActionListener(new ActionListener()
    {
      public void actionPerformed(ActionEvent evt)
      {
        //TODO add validation
      }
    });
    bottomPanelObj.add(validateButton);

    panelObj.add(bottomPanelObj, BorderLayout.SOUTH);
    frameObj.getContentPane().add(panelObj);
    frameObj.setDefaultCloseOperation(JFrame.DO_NOTHING_ON_CLOSE);
    SwingUtilities.invokeLater(new Runnable()
    {
      public void run()
      {
        frameObj.pack();
        frameObj.setVisible(true); //make frame visible
        GuiUtilFns.initColumnSizes(tableObj);
      }
    });

    final Object windowCloseObj = new Object();
    frameObj.addWindowListener(new WindowAdapter()
    {
      public void windowClosing(WindowEvent e)
      {
        synchronized (windowCloseObj)
        {
          windowCloseObj.notifyAll();
        }
      }
    });

    try
    {
      synchronized (windowCloseObj)
      {
        windowCloseObj.wait();
      }
    }
    catch (Exception ex)
    {
      System.err.println(ex);
      ex.printStackTrace();
    }

    frameObj.dispose();
  }

  /**
   * Clears all data.
   * @param fireTableDataChangedFlag true to fire table data changed, false otherwise.
   * @param evt the action event or null if none.
   */
  protected void clearData(boolean fireTableDataChangedFlag, ActionEvent evt)
  {
    pdit.clearData();
    setEditable(false);
    if (fireTableDataChangedFlag)
    {
      fireTableDataChanged();
    }
  }

  /**
   * Export data to a CSV file.
   * @param evt the action event or null if none.
   */
  protected void exportData(ActionEvent evt)
  {
    final String titleText = "Export";
    chooser.setDialogTitle(titleText);
    final int returnVal = chooser.showDialog(frameObj, titleText);
    if (returnVal == JFileChooser.APPROVE_OPTION)
    {
      final File outputFile = chooser.getSelectedFile();
//      System.out.println("You chose to export to this file: " +
//                         outputFile.getName());
      final DelimiterSeparatedValuesTable dsvt =
          new DelimiterSeparatedValuesTable();
      dsvt.importValues(svt);
      Writer w = null;
      try
      {
        w = new FileWriter(outputFile);
        final DelimiterSeparatedValues output =
            new DelimiterSeparatedValues();
        dsvt.writeAll(output, w, true);
        w.close();
      }
      catch (Exception ex)
      {
        System.err.println(ex);
        ex.printStackTrace();
      }
      if (w != null)
      {
        try
        {
          w.close();
        }
        catch (Exception ex)
        {
          System.err.println("Error closing output file: " + ex);
        }
      }
    }
  }

  /**
   * Sends a {@link TableModelEvent} to all registered listeners to inform
   * them that the table data has changed.
   */
  protected void fireTableDataChanged()
  {
    vgtm.fireTableDataChanged();
    updateButtons();
  }

  /**
   * Gets the connection information dialog.
   * @return the connection information dialog.
   */
  protected PortfolioDbConnectionInfoDialog getConnectionInfoDialog()
  {
    if (_connectionInfoDialog == null)
    {
      _connectionInfoDialog = new PortfolioDbConnectionInfoDialog(frameObj);
    }
    return _connectionInfoDialog;
  }

  /**
   * Import data from a CSV file.
   * @param evt the action event or null if none.
   */
  protected void importData(ActionEvent evt)
  {
    final String titleText = "Import";
    chooser.setDialogTitle(titleText);
    final int returnVal = chooser.showDialog(frameObj, titleText);
    if (returnVal == JFileChooser.APPROVE_OPTION)
    {
      final File inputFile = chooser.getSelectedFile();
      if (!inputFile.exists())
      {
        System.err.println("Import file does not exist: " + inputFile);
        return;
      }
//      System.out.println("You chose to import from this file: " +
//                         inputFile.getName());
      final DelimiterSeparatedValuesTable dsvt =
          new DelimiterSeparatedValuesTable();
      BufferedReader br = null;
      try
      {
        final Reader reader = new FileReader(inputFile);
        br = new BufferedReader(reader);
        final DelimiterSeparatedValues input = new DelimiterSeparatedValues(
            DelimiterSeparatedValues.STANDARD_COMMENT_TEXT);
        String errorMessage;
        int count = dsvt.readAll(input, br, true);
        if (count == 0)
        {
          errorMessage = dsvt.getErrorMessageString();
          if (errorMessage != null && errorMessage.length() > 0)
          {
            dsvt.clearErrorMessageString();
            System.err.println("Error reading input:\n" + errorMessage);
          }
        }
        else
        {
          svt.importValues(dsvt);
        }
      }
      catch (Exception ex)
      {
        System.err.println(ex);
        ex.printStackTrace();
      }
      if (br != null)
      {
        try
        {
          br.close();
        }
        catch (Exception ex)
        {
          System.err.println("Error closing input file: " + ex);
        }
      }
    }
    fireTableDataChanged();
  }

  /**
   * Returns <code>true</code> if the model is editable by default, and
   * <code>false</code> if it is not.
   * @return true if the model is editable, false otherwise.
   */
  protected final boolean isEditable()
  {
    return pdit.isEditable();
  }

  /**
   * Read data from the database.
   * @param evt the action event or null if none.
   */
  protected void readDatabase(ActionEvent evt)
  {
    final PortfolioDbConnectionInfoDialog connectionInfoDialog =
        getConnectionInfoDialog();
    final Connection dbConnection = connectionInfoDialog.getConnection();
    try
    {
      if (dbConnection != null)
      {
        pdit.readDatabase(dbConnection);
      }
    }
    catch (Exception ex)
    {
      connectionInfoDialog.showErrorMessage(ex.toString());
      connectionInfoDialog.setConnection(null);
//      System.err.println(ex);
//      ex.printStackTrace();
    }
    fireTableDataChanged();
  }

  /**
   * Determines whether the model is editable by default.
   * @param flag true if the model is editable, false otherwise.
   */
  protected void setEditable(boolean flag)
  {
    pdit.setEditable(flag);
    updateButtons();
  }

  /**
   * Updates the buttons.
   */
  protected void updateButtons()
  {
    final boolean editableFlag = isEditable();
    final boolean emptyFlag = vgtm.getRowCount() == 0;
    editButton.setEnabled(!emptyFlag && !editableFlag);
    cancelButton.setEnabled(editableFlag);
    clearButton.setEnabled(!emptyFlag);
    importButton.setEnabled(!editableFlag && emptyFlag);
    exportButton.setEnabled(!emptyFlag);
    readDbButton.setEnabled(!editableFlag && emptyFlag);
    writeDbButton.setEnabled(!emptyFlag);
  }

  /**
   * Write data to the database.
   * @param evt the action event or null if none.
   */
  protected void writeDatabase(ActionEvent evt)
  {
    final PortfolioDbConnectionInfoDialog connectionInfoDialog =
        getConnectionInfoDialog();
    final Connection dbConnection = connectionInfoDialog.getConnection();
    try
    {
      if (dbConnection != null)
      {
        pdit.writeDatabase(dbConnection);
        setEditable(false);
      }
    }
    catch (Exception ex)
    {
      connectionInfoDialog.showErrorMessage(ex.toString());
      connectionInfoDialog.setConnection(null);
//      System.err.println(ex);
//      ex.printStackTrace();
    }
  }

  public static void main(String[] args)
  {
    try
    {
      PortfolioDbImportTool gui = new PortfolioDbImportTool();
    }
    catch (Exception ex)
    {
      System.err.println(ex);
      ex.printStackTrace();
      return;
    }
  }
}
