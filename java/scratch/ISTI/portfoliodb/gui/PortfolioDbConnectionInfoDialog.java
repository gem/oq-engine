package scratch.ISTI.portfoliodb.gui;

import java.awt.Component;
import java.sql.Connection;

import scratch.ISTI.portfoliodb.PortfolioColumns;

import com.isti.util.database.IstiConnectionInfoDialog;

public class PortfolioDbConnectionInfoDialog extends IstiConnectionInfoDialog
{
  private final Component parentComp;
  private Connection _dbConnection = null;

  public PortfolioDbConnectionInfoDialog(final Component parentComp)
  {
    super(parentComp);
    this.parentComp = parentComp;
    getConnectionInfoPanel().setDatabase(PortfolioColumns.DataBaseName);
    getConnectionInfoPanel().setDatabaseVisible(false);
  }

  /**
   * Get the connection.
   * @return the connection or null if none.
   */
  public Connection getConnection()
  {
    if (_dbConnection == null)
    {
      setLocationRelativeTo(parentComp);
      _dbConnection = super.getConnection();
    }
    return _dbConnection;
  }

  /**
   * Sets the connection.
   * @param dbConnection the connection or null if none.
   */
  public void setConnection(Connection dbConnection)
  {
    _dbConnection = dbConnection;
  }
}
