package scratch.ISTI.portfoliodb;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import com.isti.util.VectorSet;

/**
 * Mapping of CSV columns to database table/columns.
 */
public class PortfolioColumns
{
  /** The database name. */
  public final static String DataBaseName = "openrisk";
  /** Id column. */
  public final static String IdColumn = "ID";
  /** Asset group name column. */
  public final static String AssetGroupNameColumn = "AssetGroupName";
  /** Asset ID column. */
  public final static String AssetIDColumn = "AssetID";
  /** AssetName column. */
  public final static String AssetNameColumn = "AssetName";
  /** BaseHt column. */
  public final static String BaseHtColumn = "BaseHt";
  /** Ded column. */
  public final static String DedColumn = "Ded";
  /** LimitLiab column. */
  public final static String LimitLiabColumn = "LimitLiab";
  /** Share column. */
  public final static String ShareColumn = "Share";
  /** SiteName column. */
  public final static String SiteNameColumn = "SiteName";
  /** Site elevation column. */
  public final static String SiteElevationColumn = "Elev";
  /** Site latitude column. */
  public final static String SiteLatitudeColumn = "Lat";
  /** Site longitude column. */
  public final static String SiteLongitudeColumn = "Lon";
  /** Soil column. */
  public final static String SoilColumn = "Soil";
  /** ValHi column. */
  public final static String ValHiColumn = "ValHi";
  /** ValLo column. */
  public final static String ValLoColumn = "ValLo";
  /** Value column. */
  public final static String ValueColumn = "Value";
  /** ValYr column. */
  public final static String ValYrColumn = "ValYr";
  /** Vs30 column. */
  public final static String Vs30Column = "Vs30";
  /** VulnModel column. */
  public final static String VulnModelColumn = "VulnModel";
  /** WindExp column. */
  public final static String WindExpColumn = "WindExp";

  /** The assset table information. */
  protected final static TableInfo AssetTable = new TableInfo("Asset");
  /** The asset group table information */
  protected final static TableInfo AssetGroupTable = new TableInfo("AssetGroup");
  /** The site table information. */
  protected final static TableInfo SiteTable = new TableInfo("Site");
  /** The soil table information. */
  protected final static TableInfo SoilTable = new TableInfo("Soil");
  /** The Vs30 table information. */
  protected final static TableInfo Vs30Table = new TableInfo("Vs30");
  /** The vulnerability model table information. */
  protected final static TableInfo VulnModelTable = new TableInfo("VulnModel");
  /** The wind exposure table information. */
  protected final static TableInfo WindExpTable = new TableInfo("WindExp");
  /** The default table information. */
  protected final static TableInfo defaultTable = AssetTable;
  /** The list of 'TableInfo' objects. */
  protected final List dbTables;
  /** The CSV column names. */
  protected final List csvColumnNames;

  /**
   * An entry in the portfolio column list.
   */
  public class Entry
  {
    /** CSV column name. */
    public final String CSV_COLUMN_NAME;
    /** Database table information. */
    public final TableInfo DB_TABLE_INFO;
    /** Database column name. */
    public final String DB_COLUMN_NAME;
    /** Database row selection flag. */
    public final boolean DB_ROW_SELECT_FLAG;

    /**
     * Creates the entry with the default database table.
     * @param csvColumnName the CSV column name.
     */
    public Entry(String csvColumnName)
    {
      this(csvColumnName, null, null, false);
    }

    /**
     * Creates the entry with the specified database table.
     * @param csvColumnName the CSV column name.
     * @param dbTableInfo the database table information or null for the default.
     */
    public Entry(String csvColumnName, TableInfo dbTableInfo)
    {
      this(csvColumnName, dbTableInfo, null, true);
    }

    /**
     * Creates the entry with the specified database table.
     * @param csvColumnName the CSV column name.
     * @param dbTableInfo the database table information or null for the default.
     * @param dbColumnName the database column name or null for the default.
     */
    public Entry(String csvColumnName, TableInfo dbTableInfo,
                 String dbColumnName)
    {
      this(csvColumnName, dbTableInfo, dbColumnName, true);
    }

    /**
     * Creates the entry with the specified database table and column.
     * @param csvColumnName the CSV column name.
     * @param dbTableInfo the database table information or null for the default.
     * @param dbColumnName the database column name or null for the default.
     * @param selectFlag true if this column is used for database row selection.
     */
    public Entry(String csvColumnName, TableInfo dbTableInfo,
                 String dbColumnName, boolean selectFlag)
    {
      if (dbTableInfo == null)
      {
        dbTableInfo = defaultTable;
      }
      if (dbColumnName == null)
      {
        dbColumnName = csvColumnName;
      }
      CSV_COLUMN_NAME = csvColumnName;
      DB_TABLE_INFO = dbTableInfo;
      DB_COLUMN_NAME = dbColumnName;
      DB_ROW_SELECT_FLAG = selectFlag;
    }

    /**
     * Determines if this entry is for the default database table.
     * @return true if this entry is for the default database table, false otherwise.
     */
    public boolean isDefaultDbTable()
    {
      return DB_TABLE_INFO.equals(defaultTable);
    }

    /**
     * Determines if this entry is used for database row selection.
     * @return true if this entry is used for database row selection, false otherwise.
     */
    public boolean isSelect()
    {
      return DB_ROW_SELECT_FLAG;
    }

    /**
     * Get a string representation of the entry.
     * @return a string representation of the entry.
     */
    public String toString()
    {
      return CSV_COLUMN_NAME + ',' + DB_TABLE_INFO + ',' +
          DB_COLUMN_NAME + ',' + DB_ROW_SELECT_FLAG;
    }
  };

  /**
   * Table information.
   */
  public static class TableInfo
  {
    /** The table name. */
    public final String TABLE_NAME;
    /** The table ID column name. */
    public final String TABLE_ID_COLUMN_NAME;

    /**
     * Creates the table information.
     * @param tableName the table name.
     */
    public TableInfo(String tableName)
    {
      this(tableName, tableName + "ID");
    }

    /**
     * Creates the table information.
     * @param tableName the table name.
     * @param tableIdColumnName the table ID column name.
     */
    public TableInfo(String tableName, String tableIdColumnName)
    {
      TABLE_NAME = tableName;
      TABLE_ID_COLUMN_NAME = tableIdColumnName;
    }

    /**
     * Get a string representation of the table information.
     * @return a string representation of the table information.
     */
    public String toString()
    {
      return getFullColumnName(TABLE_NAME, TABLE_ID_COLUMN_NAME);
    }
  }

  /** Entry list. */
  private final List portfolioColumnList;

  /**
   * Create the mapping of CSV columns to database table/columns.
   * The 'addEntries()' method should be called to populate the lists.
   */
  public PortfolioColumns()
  {
    portfolioColumnList = new ArrayList();
    dbTables = new VectorSet();
    csvColumnNames = new VectorSet();
  }

  /**
   * Adds all of the entries.
   */
  public void addEntries()
  {
    addEntry(new Entry(IdColumn, null, null, true));
    addEntry(new Entry(AssetGroupNameColumn, AssetGroupTable));
    addEntry(new Entry(AssetIDColumn));
    addEntry(new Entry(AssetNameColumn));
    addEntry(new Entry(BaseHtColumn));
    addEntry(new Entry(DedColumn));
    addEntry(new Entry(LimitLiabColumn));
    addEntry(new Entry(ShareColumn));
    addEntry(new Entry(SiteNameColumn, SiteTable));
    addEntry(new Entry(SiteElevationColumn, SiteTable, null, false));
    addEntry(new Entry(SiteLatitudeColumn, SiteTable, null, false));
    addEntry(new Entry(SiteLongitudeColumn, SiteTable, null, false));
    addEntry(new Entry(SoilColumn, SoilTable));
    addEntry(new Entry(ValHiColumn));
    addEntry(new Entry(ValLoColumn));
    addEntry(new Entry(ValueColumn));
    addEntry(new Entry(ValYrColumn));
    addEntry(new Entry(Vs30Column, Vs30Table));
    addEntry(new Entry(VulnModelColumn, VulnModelTable));
    addEntry(new Entry(WindExpColumn, WindExpTable));
  }

  /**
   * Get the CSV column names.
   * @return the CSV column names.
   */
  public List getCsvColumnNames()
  {
    return Collections.unmodifiableList(csvColumnNames);
  }

  /**
   * Get the database tables.
   * @return the list of 'TableInfo' objects.
   */
  public List getDbTables()
  {
    return Collections.unmodifiableList(dbTables);
  }

  /**
   * Gets the full column name.
   * @param tableName the table name.
   * @param tableIdColumnName the table ID column name.
   * @return the full column name.
   */
  public static String getFullColumnName(
      String tableName, String tableIdColumnName)
  {
    return tableName + '.' + tableIdColumnName;
  }

  /**
   * Gets the full column name.
   * @param dbTableInfo the database table information.
   * @return the full column name.
   */
  public static String getFullColumnName(
      TableInfo dbTableInfo)
  {
    return getFullColumnName(
        dbTableInfo.TABLE_NAME, dbTableInfo.TABLE_ID_COLUMN_NAME);
  }

  /**
   * Gets the full column name.
   * @param dbTableInfo the database table information.
   * @param tableIdColumnName the table ID column name.
   * @return the full column name.
   */
  public static String getFullColumnName(
      TableInfo dbTableInfo, String tableIdColumnName)
  {
    return getFullColumnName(dbTableInfo.TABLE_NAME, tableIdColumnName);
  }

  /**
   * Get the CSV columns.
   * @return the list of 'Entry' values for each column.
   */
  public List getPortfolioColumns()
  {
    return Collections.unmodifiableList(portfolioColumnList);
  }

  /**
   * Gets the entry for the porfolio column.
   * @param columnIndex the column index.
   * @return the entry or null if none.
   */
  public Entry getPortfolioEntry(int columnIndex)
  {
    return (Entry) portfolioColumnList.get(columnIndex);
  }

  /**
   * Adds the entry to the portfolio column list.
   * @param entry the Entry.
   */
  protected void addEntry(Entry entry)
  {
    dbTables.add(entry.DB_TABLE_INFO);
    if (csvColumnNames.add(entry.CSV_COLUMN_NAME))
    {
      portfolioColumnList.add(entry);
    }
    else
    {
      System.err.println("CSV column \"" + entry.CSV_COLUMN_NAME +
                         "\" was already found");
    }
  }
}
