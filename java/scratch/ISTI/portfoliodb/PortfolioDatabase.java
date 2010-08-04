package scratch.ISTI.portfoliodb;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.Reader;
import java.io.Writer;
import java.sql.Connection;
import java.sql.SQLException;

import com.isti.util.DelimiterSeparatedValues;
import com.isti.util.DelimiterSeparatedValuesTable;
import com.isti.util.ValueTableModel;
import com.isti.util.database.MySQLConnectionJDBC;

public class PortfolioDatabase
{
  //portfolio assets table
  private final PortfolioAssetsTable assetsTable;

  /**
   * Creates the portfolio database.
   */
  public PortfolioDatabase()
  {
    assetsTable = new PortfolioAssetsTable();
  }

  /**
   * Clears all data.
   */
  public void clearData()
  {
    assetsTable.clearRows();
  }

  /**
   * Creates the MySQL connection.
   * @param hostName the host name.
   * @param failOverHostNames the fail over host names or null for none.
   * @param port the port or null for the default.
   * @param userName the user name.
   * @param password the password.
   * @exception ClassNotFoundException if the driver's class could not be found.
   * @exception InstantiationException if the driver could not be instantiated.
   * @exception IllegalAccessException if the driver's class or initializer is
   * not accessible.
   * @return the MySQL connection.
   * @exception SQLException if a database access error occurs.
   */
  public static MySQLConnectionJDBC
      createMySQLConnection(
          String hostName, String[] failOverHostNames, String port,
          String userName, String password) throws ClassNotFoundException,
      InstantiationException, IllegalAccessException, SQLException
  {
    MySQLConnectionJDBC.registerDriver();
    final String url = MySQLConnectionJDBC.getUrl(
        hostName, failOverHostNames, port, PortfolioColumns.DataBaseName);
    final java.util.Properties info = MySQLConnectionJDBC.saveUserPassword(
        null, userName, password);
    MySQLConnectionJDBC mySqlConn = new MySQLConnectionJDBC(url, info, null);
    mySqlConn.createConnection();
    return mySqlConn;
  }

  /**
   * Exports the data to a CSV file.
   * @param outputFile the output file.
   * @throws IOException if error.
   */
  public void exportData(File outputFile) throws IOException
  {
    final DelimiterSeparatedValuesTable dsvt =
        new DelimiterSeparatedValuesTable();
    dsvt.importValues(assetsTable);
    final Writer w = new FileWriter(outputFile);
    final DelimiterSeparatedValues output =
        new DelimiterSeparatedValues();
    dsvt.writeAll(output, w, true);
    w.close();
  }

  /**
   * Get the value table model.
   * @return the value table model.
   */
  public ValueTableModel getValueTableModel()
  {
    return assetsTable;
  }

  /**
   * Import the data from a CSV file.
   * @param inputFile the input file.
   * @throws IOException if error.
   */
  public void importData(File inputFile) throws IOException
  {
//    System.out.println("You chose to import from this file: " +
//                       inputFile.getName());
    final DelimiterSeparatedValuesTable dsvt =
        new DelimiterSeparatedValuesTable();
    final Reader reader = new FileReader(inputFile);
    final BufferedReader br = new BufferedReader(reader);
    final DelimiterSeparatedValues input = new DelimiterSeparatedValues(
        DelimiterSeparatedValues.STANDARD_COMMENT_TEXT);
    //if error reading rows
    if (dsvt.readAll(input, br, true) == 0)
    {
      final String errorMessage = dsvt.getErrorMessageString();
      if (errorMessage != null && errorMessage.length() > 0)
      {
        dsvt.clearErrorMessageString();
//        System.err.println("Error reading input:\n" + errorMessage);
      }
    }
    else
    {
      assetsTable.importValues(dsvt);
    }
    br.close();
  }

  /**
   * Returns <code>true</code> if the model is editable by default, and
   * <code>false</code> if it is not.
   * @return true if the model is editable, false otherwise.
   */
  public final boolean isEditable()
  {
    return assetsTable.isEditable();
  }

  /**
   * Reads the data from the database.
   * @param dbConnection the database connection.
   * @throws SQLException if error.
   */
  public void readDatabase(Connection dbConnection) throws SQLException
  {
    assetsTable.readAll(dbConnection);
  }

  /**
   * Determines whether the model is editable by default.
   * @param flag true if the model is editable, false otherwise.
   */
  public final void setEditable(boolean flag)
  {
    assetsTable.setEditable(flag);
  }

  /**
   * Writes the data to the database.
   * @param dbConnection the database connection.
   * @throws SQLException if error.
   */
  public void writeDatabase(Connection dbConnection) throws SQLException
  {
    assetsTable.writeAll(dbConnection);
  }

  public static void main(String[] args)
  {
    String s;
    String hostName = "localhost";
    String[] failOverHostNames = null;
    String port = null; //use the default port
    String userName = null;
    String password = null;
    File inputFile = null;
    File outputFile = null;

    if (args.length == 0)
    {
      System.out.println(
          "PortfolioDatabase username password input.csv output.csv");
      return;
    }

    for (int i = 0; i < args.length; i++)
    {
      s = args[i];
      switch (i)
      {
        case 0:
          userName = s;
          break;
        case 1:
          password = s;
          break;
        case 2:
          if (s.length() > 0)
          {
            inputFile = new File(s);
          }
          break;
        case 3:
          if (s.length() > 0)
          {
            outputFile = new File(s);
          }
          break;
      }
    }

    try
    {
      final Connection dbConnection = createMySQLConnection(
          hostName, failOverHostNames, port, userName, password).getConnection();
      final PortfolioDatabase pdit = new PortfolioDatabase();
      if (inputFile != null)
      {
        pdit.importData(inputFile);
        pdit.writeDatabase(dbConnection);
        pdit.clearData();
      }
      if (outputFile != null)
      {
        pdit.readDatabase(dbConnection);
        pdit.exportData(outputFile);
      }
    }
    catch (Exception ex)
    {
      System.err.println(ex);
      ex.printStackTrace();
      return;
    }
  }
}
