package scratch.martinez.util;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.TreeMap;

import javax.swing.JFrame;

import org.opensha.nshmp.sha.gui.beans.ExceptionBean;
import org.opensha.nshmp.sha.gui.beans.GuiBeanAPI;


/**
 * <strong>Title:</strong> DBAccessor<br />
 * <strong>Description:</strong> Interacts with an oracle database.<br />
 * This class provides access to oracle databases through java.  It essentially
 * wraps the oracle driver(s), but makes for a much easier and cleaner user interface.
 * This class was written and tested with the oracle.jdbc.OracleDriver and may or may
 * not work with other drivers.  As is somewhat implied by its name, this class will
 * only allow READ ONLY queries to the database.  
 * 
 * @author <a href="mailto:emartinez@usgs.gov">Eric Martinez</a>
 */
public class DBAccessor {
	
	////////////////////////////////////////////////////////////////////////////////
	//                              PRIVATE VARIABLES                             //
	////////////////////////////////////////////////////////////////////////////////
	
	/* A dummy array to use in case user passes us a bad array */
	private static final String[] BAD_CONN = {"","","","","",""};
	private static final int MINDEX = 0;
	private int MAXDEX = BAD_CONN.length;
	
	/* This will be the connection for the utility */
	private Connection conn = null;
	/* We use this information to create the connection */
	private String[] connectionInfo = {};
	/* This control flag tells us if the user has changed and connection
	 * info since the last connection was made. */
	private boolean changeMade = true; // By default assume new (i.e. changed)
	
	/* These provide easy indexing into the connection info arrays */
	public static final int DRIVER_NAME = 0;
	public static final int SERVER_NAME = 1;
	public static final int PORT_NUMBER = 2;
	public static final int SID = 3;
	public static final int USERNAME = 4;
	public static final int PASSWORD = 5;
	
	////////////////////////////////////////////////////////////////////////////////
	//                              PUBLIC CONSTRUCTORS                           //
	////////////////////////////////////////////////////////////////////////////////
	
	/** 
	 * Default constructor that uses the fake connection info to
	 * initialize the Accessor.  An accessor that is initialized in this 
	 * was cannot actually make a connection to a database as all its
	 * fields are left blank.  
	 */
	public DBAccessor() {this(null);}
	/**
	 * A constructor that uses the <code>connectionInfo</code> array to establish
	 * the connection to the server. The <code>connectionInfo<code> array should have
	 * exactly 6 entries as follows:
	 * <pre>
	 * 	String[] connectionInfo = {"database.driver.name", "server.name", "portNumber",
	 * 		"sid", "username", "password"};
	 * </pre>
	 * A call to this constructor will store away these values, and then attempt to 
	 * make a connection to the specified database.  After instantiating an accessor
	 * one should call <code>hasValidConnection()</code> to ensure that the
	 * connection succeeded.  If a user does not know all the information at the time
	 * of creating an accessor or just does not want a connection to me made immediately,
	 * then they should use the optional <code>makeConnection</code> parameter to 
	 * the constructor to stop the connection attempt.
	 * 
	 * @param connectionInfo An array of <code>String</code>s that holds the information
	 * required to make a connection to the database.
	 */
	public DBAccessor(String[] connectionInfo) {this(connectionInfo, true);}
	/**
	 * A constructor that uses the <code>connectionInfo</code> array to establish
	 * the connection to the server. The <code>connectionInfo<code> array should have
	 * exactly 6 entries as follows:
	 * <pre>
	 * 	String[] connectionInfo = {"database.driver.name", "server.name", "portNumber",
	 * 		"sid", "username", "password"};
	 * </pre>
	 * A call to this constructor will store away these values, and if <code>makeConnection</code>
	 * is <code>true</code> then it will attempt to make a connection to the specified 
	 * database.  After instantiating an accessor one should call 
	 * <code>hasValidConnection()</code> to ensure that the connection succeeded.
	 * 
	 * @param connectionInfo An array of <code>String</code>s that holds the information
	 * required to make a connection to the database.
	 * @param makeConnection A <code>boolean</code> control flag. <code>True</code> if
	 * 	you want to make a connection upon creation of the object, falst otherwise.
	 */
	public DBAccessor(String[] connectionInfo, boolean makeConnection) {
		if(connectionInfo == null || connectionInfo.length != 6)
			connectionInfo = BAD_CONN;
		this.connectionInfo = connectionInfo;
		// this.conn is set implicitely by getConnection, 
		// but for clarity, we set it explicitely as well
		this.conn = getConnection();
		// Set the index bounds
		this.MAXDEX = connectionInfo.length;
	}
	
	////////////////////////////////////////////////////////////////////////////////
	//                               PUBLIC FUNCTIONS                             //
	////////////////////////////////////////////////////////////////////////////////
	
	/**
	 * Gets the current connection to the database.  If no such connection exists or
	 * the <code>changeMade</code> flag has been set (by changing a parameter), then
	 * it uses the current <code>connectionInfo</code> array to make a new connection
	 * to the database.  If an error occurs then <code>null</code> is returned.
	 * 
	 * @return The current object's connection.
	 */
	public Connection getConnection() {
		if(conn == null || changeMade) {
			changeMade = false; // We are creating the most recent connection
			try {
				// Register the driver
				Class.forName(connectionInfo[DRIVER_NAME]);
				// Construct the connection URL
				String url = "jdbc:oracle:thin:@" + connectionInfo[SERVER_NAME] +
					":" + connectionInfo[PORT_NUMBER] + ":" + connectionInfo[SID];
				// Make the connection
				conn = DriverManager.getConnection(url, connectionInfo[USERNAME],
						connectionInfo[PASSWORD]);
			} catch (ClassNotFoundException ex) {
				((JFrame) (new ExceptionBean("Failed to register the class name " + connectionInfo[DRIVER_NAME],
						"Class Not Found!", ex)).getVisualization(GuiBeanAPI.SPLASH)).setVisible(true);
				ex.printStackTrace();
				conn = null;
			} catch (SQLException sqlEx) {
				((JFrame) (new ExceptionBean("The database rejected your connection! " + connectionInfo[SERVER_NAME],
						"SQL Error", sqlEx)).getVisualization(GuiBeanAPI.SPLASH)).setVisible(true);
				sqlEx.printStackTrace();
				conn = null;
			}
		}
		return conn;
	}

	/**
	 * Attempts to set the specified <code>index</code> of the <code>connectionInfo</code> 
	 * array to the given <code>value</code>.  If the given <code>index</code> is out
	 * of bounds for the array, then <code>false</code> is returned and the value is
	 * not changed.  Upon successful change of the value, the <code>changeMade</code>
	 * flag is set so subsequent calls to <code>getConnection()</code> will be forced
	 * to create a new connection for the updated parameters.
	 * 
	 * @param index The index into the <code>connectionInfo</code> for the value we wish to set.
	 * @param value The new value for the specified index.
	 * @return true if successfully set, false otherwise.
	 */
	public boolean setInfoValue(int index, String value) {
		// Make sure we are within bounds.
		if(index < MINDEX || index > MAXDEX)
			return false;
		// We are making a chnage w/o updating the connection, so switch to true.
		changeMade = true;
		// Set the value
		connectionInfo[index] = value;
		return true;
	}
	
	/**
	 * Checks whether there is currently a valid connection to a database.
	 * While it is not required that a user checks this before querying the
	 * database, it is a good idea to avoid unexpected exceptions.
	 * 
	 * @return <code>true</code> if there is a valid connection, false otherwise.
	 */
	public boolean hasValidConnection() {return !(this.conn == null);}

	/**
	 * This will query the database using the currently existing connection and
	 * then return the <code>ResultSet</code> that we get.  It is very straight
	 * forward however if there is no connection, or the <code>sql</code> is
	 * trying to modify the data, null is returned.
	 * 
	 * @param sql The SQL statement to execute.
	 * @return The <code>ResultSet</code> generated by the sql query.
	 */
	public ResultSet query(String sql) {
		// Make sure we have a connection and are doing a READ ONLY query.
		// This class is an _ACCESSOR_ only.  So no updates!!
		if(!hasValidConnection()) return null;
		if(!isReadOnly(sql)) return null;
		ResultSet r = null;
		try {
			Statement s = conn.createStatement();
			r = s.executeQuery(sql);
		} catch (SQLException sqlEx) {
			((JFrame) (new ExceptionBean("The SQL query failed! " + sql, "SQL Error", 
					sqlEx)).getVisualization(GuiBeanAPI.SPLASH)).setVisible(true);
			sqlEx.printStackTrace();
		}
		return r;
	}
	
	/** 
	 * This queries the database and puts the result into an <code>ArrayList</code>
	 * that can then be used repeatedly to access the data.  If the underlying
	 * query fails for any reason, then null is returned.  The format of the returned
	 * <code>ArrayList</code> is as follows: (Viewed as an array)<br />
	 * <pre>
	 *	{
	 * 		{ ColumnName=>Value, ColumnName=>Value, ... , ColumnName=>Value },
	 *		{ ColumnName=>Value, ColumnName=>Value, ... , ColumnName=>Value },
	 *		...
	 *		{ ColumnName=>Value, ColumnName=>Value, ... , ColumnName=>Value },
	 * 	}
	 * </pre><br />
	 * As such, one could access the result set in this manner with something like:<br />
	 * <pre>
	 *	// Note: db is a valid DBAccessor object
	 * 	ArrayList<TreeMap<String, String>> result = db.doQuery("SELECT id, name FROM table");
	 * 	for(int i = 0; i < result.size(); ++i) {
	 * 		System.out.println("Results for row " + i);
	 * 		System.out.println("\tid: " + result.get(i).get("id"));
	 * 		System.out.println("\tname: result.get(i).get("name") + "\n");
	 * 	}
	 * </pre><br />
	 * 
	 * This might produce output like:<br />
	 * <pre>
	 * 	Results for row 0
	 * 		id: 1
	 * 		name: Julie
	 * 
	 * 	Results for row 1
	 * 		id: 2
	 * 		name: Steve
	 * 
	 * 	Results for row 2
	 * 		id: 3
	 * 		name: Chris
	 * 
	 * </pre>
	 * 
	 * @param sql The SQL statment to query.
	 * @return As specified above.
	 */
	public ArrayList<TreeMap<String, String>> doQuery(String sql) {
		ArrayList<TreeMap<String, String>> rtn = new ArrayList<TreeMap<String, String>>();
		ResultSet result = query(sql);
		if(result == null) return null;
		try {
			ResultSetMetaData metadata = result.getMetaData();
			while(result.next()) {
				TreeMap<String, String> row = new TreeMap<String, String>();
				for(int i = 1; i < metadata.getColumnCount(); ++i) {
					row.put(metadata.getColumnName(i), result.getString(i));
				}
				rtn.add(row);
			}
		} catch (SQLException sqlEx) {
			((JFrame) (new ExceptionBean("The SQL query failed! " + sql, "SQL Error", 
					sqlEx)).getVisualization(GuiBeanAPI.SPLASH)).setVisible(true);
			sqlEx.printStackTrace();
		}
		return rtn;
	}
	
	////////////////////////////////////////////////////////////////////////////////
	//                              PRIVATE FUNCTIONS                             //
	////////////////////////////////////////////////////////////////////////////////
	
	/** 
	 * Checks if the sql is modifying the database.  If so, return false;
	 */
	private boolean isReadOnly(String sql) {
		if(sql.startsWith("INSERT")) return false;
		if(sql.startsWith("insert")) return false;
		if(sql.startsWith("DELETE")) return false;
		if(sql.startsWith("delete")) return false;
		if(sql.startsWith("UPDATE")) return false;
		if(sql.startsWith("update")) return false;
		if(sql.startsWith("DROP")) return false;
		if(sql.startsWith("drop")) return false;
		if(sql.startsWith("ALTER")) return false;
		if(sql.startsWith("alter")) return false;
		if(sql.startsWith("CREATE")) return false;
		if(sql.startsWith("create")) return false;
		return true;
	}


}
