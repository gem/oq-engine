package scratch.ISTI.portfoliodb;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

import com.isti.util.database.SQLValuesTable;

public class PortfolioAssetsTable
    extends SQLValuesTable
{
  //select limit text
  private final static String SELECT_LIMIT_TEXT = " LIMIT 1";
  private final PortfolioColumns portfolioColumns;

  public PortfolioAssetsTable()
  {
    portfolioColumns = new PortfolioColumns();
    portfolioColumns.addEntries();
    createLists(); //create new lists
    super.setColumnNames(portfolioColumns.getCsvColumnNames());
    setIdColumn(PortfolioColumns.IdColumn);
  }

  /**
   * Reads all of the rows.
   * This will attempt to load all of the rows into memory.
   * Any existing error messages are cleared.
   * To clear existing colums and rows the 'clearLists' method should be called.
   * To clear existing rows the 'clearRows' method should be called.
   * @param dbConnection the database connection.
   * @return the number of rows read or 0 if error.
   * @throws SQLException if error.
   * @see getErrorMessages
   */
  public int readAll(Connection dbConnection) throws SQLException
  {
    PortfolioColumns.TableInfo tableInfo;
    final StringBuffer from = new StringBuffer();
    final StringBuffer where = new StringBuffer();
    final Iterator dbTablesIt = portfolioColumns.getDbTables().iterator();
    while (dbTablesIt.hasNext())
    {
      tableInfo = (PortfolioColumns.TableInfo) dbTablesIt.next();
      if (from.length() > 0)
      {
        from.append(',');
      }
      from.append(tableInfo.TABLE_NAME);
      if (!tableInfo.equals(portfolioColumns.defaultTable))
      {
        if (where.length() > 0)
        {
          where.append(" AND ");
        }
        final String tableIdColumnName = tableInfo.TABLE_ID_COLUMN_NAME;
        where.append(
            PortfolioColumns.getFullColumnName(portfolioColumns.defaultTable,
                                               tableIdColumnName) + '=' +
            PortfolioColumns.getFullColumnName(tableInfo));
      }
    }
    final String sql = "SELECT * FROM " + from + " WHERE " + where;
    final ResultSet rs = executeQuery(dbConnection, sql);
    return readAll(rs);
  }

  /**
   * Gets the value.
   * @param rs the result set.
   * @param columnIndex the column index.
   * @return the value.
   * @throws SQLException if error.
   */
  protected Object getValue(ResultSet rs, int columnIndex) throws SQLException
  {
    final PortfolioColumns.Entry pcEntry =
        portfolioColumns.getPortfolioEntry(columnIndex);
    //skip if no entry
    if (pcEntry == null)
    {
      return null;
    }
    final String dbColumnName =
        pcEntry.DB_TABLE_INFO.TABLE_NAME + "." + pcEntry.DB_COLUMN_NAME;
    final Object valueObj = rs.getObject(dbColumnName);
    return valueObj;
  }

  /**
   * Sets the column names list.
   * The lists should be created (via the 'createLists' method) first.
   * @param l the column names list.
   * @return true if the column names list was set, false if error.
   * @see createLists
   */
  protected boolean setColumnNames(List l)
  {
    super.setColumnNames(l);
    return true;
  }

  /**
   * Writes all the rows.
   * @param dbConnection the database connection.
   * @throws SQLException if error.
   */
  public void writeAll(Connection dbConnection) throws SQLException
  {
    final int numRows = getRowCount();
    if (numRows <= 0) //exit if no rows
    {
      return;
    }

    //get the list of selected columns
    Object key;
    PortfolioColumns.Entry pcEntry;
    final int numColumns = getColumnCount();

    //make sure all subtables have entries
    for (int rowIndex = 0; rowIndex < numRows; rowIndex++)
    {
      //map with 'TableInfo' key and select 'StringBuffer' value
      final Map selectMap = new HashMap();

      for (int columnIndex = 0; columnIndex < numColumns; columnIndex++)
      {
        pcEntry = portfolioColumns.getPortfolioEntry(columnIndex);
        //skip if no entry or not a select column
        if (pcEntry == null || !pcEntry.isSelect())
        {
          continue;
        }
        key = pcEntry.DB_TABLE_INFO;
        StringBuffer select = (StringBuffer) selectMap.get(key);
        if (select == null)
        {
          select = new StringBuffer(
              " FROM " + pcEntry.DB_TABLE_INFO.TABLE_NAME + " WHERE");
          selectMap.put(key, select);
        }
        else
        {
          select.append(" AND");
        }
        final Object valueObj = getValueAt(rowIndex, columnIndex);
        select.append(" " + pcEntry.DB_COLUMN_NAME + "='" + valueObj + "'");
      }

      ResultSet defaultTableRs = null;
      boolean defaultTableInsertRowFlag = false;
      Iterator selectMapIt = selectMap.keySet().iterator();
      while (selectMapIt.hasNext())
      {
        final PortfolioColumns.TableInfo tableInfo = (PortfolioColumns.
            TableInfo) selectMapIt.next();
        final String sql =
            "SELECT *" + selectMap.get(tableInfo).toString() +
            SELECT_LIMIT_TEXT;
        final ResultSet rs = executeQuery(dbConnection, sql);
        final boolean insertRowFlag;
        if (!rs.next())
        {
          insertRowFlag = true;
          rs.moveToInsertRow();
        }
        else
        {
          insertRowFlag = false;
        }
        for (int columnIndex = 0; columnIndex < numColumns; columnIndex++)
        {
          pcEntry = portfolioColumns.getPortfolioEntry(columnIndex);
          //skip if no entry or not the current table
          if (pcEntry == null || !pcEntry.DB_TABLE_INFO.equals(tableInfo))
          {
            continue;
          }
          final String dbColumnName = pcEntry.DB_COLUMN_NAME;
          final Object valueObj = getValueAt(rowIndex, columnIndex);
//          System.out.println(
//              tableInfo.TABLE_NAME + "." + dbColumnName + "=" +
//              valueObj);
          updateValue(rs, valueObj, dbColumnName);
        }
        //if the default table
        if (tableInfo.equals(portfolioColumns.defaultTable))
        {
          defaultTableRs = rs;
          defaultTableInsertRowFlag = insertRowFlag;
        }
        else
        {
          updateRow(rs, insertRowFlag);
          rs.close();
        }
      }

      if (defaultTableRs == null)
      {
        System.err.println("No default table result set found");
        return;
      }

      //get the ID values
      selectMapIt = selectMap.keySet().iterator();
      while (selectMapIt.hasNext())
      {
        final PortfolioColumns.TableInfo tableInfo = (PortfolioColumns.
            TableInfo) selectMapIt.next();
        //skip the default table
        if (tableInfo.equals(portfolioColumns.defaultTable))
        {
          continue;
        }
        final String tableIdColumnName = tableInfo.TABLE_ID_COLUMN_NAME;
        final String sql =
            "SELECT " + tableIdColumnName +
            selectMap.get(tableInfo).toString() + SELECT_LIMIT_TEXT;
        final ResultSet rs = executeQuery(dbConnection, sql);
//        System.out.println("row " + rowIndex + ": " + sql);
        if (!rs.next()) //skip if no ID, should not happen
        {
          System.err.println("table ID not found: " + tableIdColumnName);
          continue;
        }

        //save db column name and value
        final Object valueObj = rs.getObject(tableIdColumnName);
//        System.out.println("table ID is: " + valueObj);
        updateValue(defaultTableRs, valueObj, tableIdColumnName);
      }
      updateRow(defaultTableRs, defaultTableInsertRowFlag);
      defaultTableRs.close();
    }
  }

  /**
   * Writes all the rows.
   * @param rs the result set.
   * @throws SQLException if error.
   * @deprecated replaced by <code>writeAll(Connection)</code>.
   */
  public void writeAll(ResultSet rs) throws SQLException
  {
    super.writeAll(rs);
  }

  /**
   * Executes the sql statement.
   * @param dbConnection the database connection.
   * @param sql the sql statement.
   * @return the ResultSet.
   * @throws SQLException if error.
   */
  protected ResultSet executeQuery(
      Connection dbConnection, String sql) throws SQLException
  {
    final ResultSet rs = dbConnection.createStatement(
        ResultSet.TYPE_SCROLL_INSENSITIVE,
        ResultSet.CONCUR_UPDATABLE).executeQuery(sql);
    return rs;
  }
}
