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

package org.opensha.sha.cybershake.db;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.IOException;
import java.io.PrintWriter;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.SQLWarning;
import java.sql.Statement;
import java.text.SimpleDateFormat;
import java.util.Date;

import org.opensha.commons.gui.UserAuthDialog;



/**
 * DbConnectionBroker
 * A servlet-based broker for database connections.
 * Creates and manages a pool of database connections.
 * @version 1.0.13 3/12/02
 * @author Marc A. Mnich
 * modified by Vipin Gupta , Nitin Gupta
 */
public class DBAccess implements Runnable{
	private boolean readOnly = false;
	
    private Thread runner;

    private Connection[] connPool;
    private int[] connStatus;

    private long[] connLockTime, connCreateDate;
    private String[] connID;
    private String dbDriver, dbServer, dbLogin, dbPassword, logFileString;
    private int currConnections, connLast, minConns, maxConns, maxConnMSec,
        maxCheckoutSeconds, debugLevel;

    //available: set to false on destroy, checked by getConnection()
    private boolean available=true;

    private PrintWriter log;
    private SQLWarning currSQLWarning;
    private String pid;

    private final int DEFAULTMAXCHECKOUTSECONDS=60;
    private final int DEFAULTDEBUGLEVEL=0;



    /**
     * Class default constructor
     * Creates a new Connection Broker after reading the JDBC info from the
     * data file.
     */
    public DBAccess(String hostname,String dbName) {
      
        String dbDriver = "com.mysql.jdbc.Driver";
        String dbServer = "jdbc:mysql://"+hostname+":"+3306+"/"+dbName;
        String dbLogin = "cybershk_ro";
        String dbPassword = "CyberShake2007";
        readOnly = true;
        int minConns =1;
        int maxConns = 100;
        String logFileString = null;
        double maxConnTime = 0.5;

        try {
			setupBroker(dbDriver, dbServer, dbLogin, dbPassword, minConns,
			            maxConns, logFileString, maxConnTime, false,
			            DEFAULTMAXCHECKOUTSECONDS, DEFAULTDEBUGLEVEL);
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}

    }
    
    /**
     * Class default constructor
     * Creates a new Connection Broker after reading the JDBC info from the
     * data file.
     * @throws IOException 
     */
    public DBAccess(String hostname,String dbName, String user, String pass) throws IOException {
      
        String dbDriver = "com.mysql.jdbc.Driver";
        String dbServer = "jdbc:mysql://"+hostname+":"+3306+"/"+dbName;
        String dbLogin = user;
        String dbPassword = pass;
        int minConns =1;
        int maxConns = 100;
        String logFileString = null;
        double maxConnTime = 0.5;

		setupBroker(dbDriver, dbServer, dbLogin, dbPassword, minConns,
			            maxConns, logFileString, maxConnTime, false,
			            DEFAULTMAXCHECKOUTSECONDS, DEFAULTDEBUGLEVEL);

    }
    
    public boolean isReadOnly() {
    	return readOnly;
    }
    
    public void setReadOnly(boolean readOnly) {
    	this.readOnly = readOnly;
    }
    
    public static DBAccess createWithAuthDialog(String host, String dbName) throws IOException {
    	UserAuthDialog auth = new UserAuthDialog(null, true);
		auth.setVisible(true);
		
		if (auth.isCanceled())
			return null;
		
		DBAccess db = new DBAccess(host, dbName, auth.getUsername(), new String(auth.getPassword()));
		return db;
    }


    /**
     * Creates a new Connection Broker<br>
     * dbDriver:        JDBC driver. e.g. 'com.mysql.jdbc.Driver'<br>
     * dbServer:        JDBC connect string. e.g. 'jdbc:oracle:thin:@203.92.21.109:1526:orcl'<br>
     * dbLogin:         Database login name.  e.g. 'Scott'<br>
     * dbPassword:      Database password.    e.g. 'Tiger'<br>
     * minConns:        Minimum number of connections to start with.<br>
     * maxConns:        Maximum number of connections in dynamic pool.<br>
     * logFileString:   Absolute path name for log file. e.g. 'c:/temp/mylog.log' <br>
     * maxConnTime:     Time in days between connection resets. (Reset does a basic cleanup)<br>
     * logAppend:       Append to logfile (optional)<br>
     * maxCheckoutSeconds:       Max time a connection can be checked out before being recycled. Zero value turns option off, default is 60 seconds.
     * debugLevel:      Level of debug messages output to the log file.  0 -> no messages, 1 -> Errors, 2 -> Warnings, 3 -> Information
     */
    public DBAccess(String dbDriver, String dbServer, String dbLogin,
        String dbPassword, int minConns, int maxConns,
            String logFileString, double maxConnTime) throws IOException {

        setupBroker(dbDriver, dbServer, dbLogin, dbPassword, minConns,
                    maxConns, logFileString, maxConnTime, false,
                    DEFAULTMAXCHECKOUTSECONDS, DEFAULTDEBUGLEVEL);
    }

    /*
     * Special constructor to handle logfile append
     */
    public DBAccess(String dbDriver, String dbServer, String dbLogin,
        String dbPassword, int minConns, int maxConns,
            String logFileString, double maxConnTime, boolean logAppend)
        throws IOException {

        setupBroker(dbDriver, dbServer, dbLogin, dbPassword, minConns,
                    maxConns, logFileString, maxConnTime, logAppend,
                    DEFAULTMAXCHECKOUTSECONDS, DEFAULTDEBUGLEVEL);
    }

    /*
     * Special constructor to handle connection checkout expiration
     */
    public DBAccess(String dbDriver, String dbServer, String dbLogin,
        String dbPassword, int minConns, int maxConns,
            String logFileString, double maxConnTime, boolean logAppend,
                              int maxCheckoutSeconds, int debugLevel)
        throws IOException {

        setupBroker(dbDriver, dbServer, dbLogin, dbPassword, minConns,
                    maxConns, logFileString, maxConnTime, logAppend,
                    maxCheckoutSeconds, debugLevel);
    }



    private void setupBroker(String dbDriver, String dbServer, String dbLogin,
        String dbPassword, int minConns, int maxConns,
            String logFileString, double maxConnTime, boolean logAppend,
                             int maxCheckoutSeconds, int debugLevel)
        throws IOException {

        connPool = new Connection[maxConns];
        connStatus = new int[maxConns];
        connLockTime = new long[maxConns];
        connCreateDate = new long[maxConns];
        connID = new String[maxConns];
        currConnections = minConns;
        this.maxConns = maxConns;
        this.dbDriver = dbDriver;
        this.dbServer = dbServer;
        this.dbLogin = dbLogin;
        this.dbPassword = dbPassword;
        this.logFileString = logFileString;
        this.maxCheckoutSeconds = maxCheckoutSeconds;
        this.debugLevel = debugLevel;
        maxConnMSec = (int)(maxConnTime * 86400000.0);  //86400 sec/day
        if(maxConnMSec < 30000) {  // Recycle no less than 30 seconds.
            maxConnMSec = 30000;
        }


        try {
            log = new PrintWriter(new FileOutputStream(logFileString,
                                                       logAppend),true);

            // Can't open the requested file. Open the default file.
        } catch (Exception e1) {
        	try {
        		File tempFile = File.createTempFile("OpenSHA_CyberShake_db_access", ".log");
//        		System.err.println("WARNING: couldn't write to db log file, using temporary file: " + tempFile.getAbsolutePath());
				log = new PrintWriter(new FileOutputStream(tempFile),true);
			} catch (Exception e) {
				throw new IOException("Can't open any log file");
			}
        }



        // Write the pid file (used to clean up dead/broken connection)
        SimpleDateFormat formatter
            = new SimpleDateFormat ("yyyy.MM.dd G 'at' hh:mm:ss a zzz");
        Date nowc = new Date();
        pid = formatter.format(nowc);

       


        // Initialize the pool of connections with the mininum connections:
        // Problems creating connections may be caused during reboot when the
        //    servlet is started before the database is ready.  Handle this
        //    by waiting and trying again.  The loop allows 5 minutes for
        //    db reboot.
        boolean connectionsSucceeded=false;
        int dbLoop=2;

        try {
            for(int i=1; i < dbLoop; i++) {
                try {
                    for(int j=0; j < currConnections; j++) {
                        createConn(j);
                    }
                    connectionsSucceeded=true;
                    break;
                } catch (SQLException e){
                    if(debugLevel > 0) {
                        log.println("--->Attempt (" + String.valueOf(i) +
                                    " of " + String.valueOf(dbLoop) +
                                    ") failed to create new connections set at startup: ");
                        log.println("    " + e);
                    }
                }
            }
            if(!connectionsSucceeded) { // All attempts at connecting to db exhausted
                if(debugLevel > 0) {
                    log.println("\r\nAll attempts at connecting to Database exhausted");
                }
                throw new IOException();
            }
        } catch (Exception e) {
            throw new IOException();
        }

        // Fire up the background housekeeping thread

        runner = new Thread(this);
        runner.start();

    }//End DbConnectionBroker()


    /**
     * Housekeeping thread.  Runs in the background with low CPU overhead.
     * Connections are checked for warnings and closure and are periodically
     * restarted.
     * This thread is a catchall for corrupted
     * connections and prevents the buildup of open cursors. (Open cursors
     * result when the application fails to close a Statement).
     * This method acts as fault tolerance for bad connection/statement programming.
     */
    public void run() {
        boolean forever = true;
        Statement stmt=null;
        String currCatalog=null;
        long maxCheckoutMillis = maxCheckoutSeconds * 1000;


        while(forever) {

            // Make sure the log file is the one this instance opened
            // If not, clean it up!
            try {
                BufferedReader in = new BufferedReader(new
                                       FileReader(logFileString + "pid"));
                String curr_pid = in.readLine();
                if(curr_pid.equals(pid)) {
                    //log.println("They match = " + curr_pid);
                } else {
                    //log.println("No match = " + curr_pid);
                    log.close();

                    // Close all connections silently - they are definitely dead.
                    for(int i=0; i < currConnections; i++) {
                        try {
                            connPool[i].close();
                        } catch (SQLException e1) {} // ignore
                    }
                    // Returning from the run() method kills the thread
                    return;
                }

                in.close();

            } catch (IOException e1) {
                log.println("Can't read the file for pid info: " +
                            logFileString + "pid");
            }


            // Get any Warnings on connections and print to event file
            for(int i=0; i < currConnections; i++) {
                try {
                    currSQLWarning = connPool[i].getWarnings();
                    if(currSQLWarning != null) {
                        if(debugLevel > 1) {
                            log.println("Warnings on connection " +
                                        String.valueOf(i) + " " + currSQLWarning);
                        }
                        connPool[i].clearWarnings();
                    }
                } catch(SQLException e) {
                    if(debugLevel > 1) {
                        log.println("Cannot access Warnings: " + e);
                    }
                }

            }

            for(int i=0; i < currConnections; i++) { // Do for each connection
                long age = System.currentTimeMillis() - connCreateDate[i];


                try {  // Test the connection with createStatement call
                    synchronized(connStatus) {
                        if(connStatus[i] > 0) { // In use, catch it next time!

                            // Check the time it's been checked out and recycle
                            long timeInUse = System.currentTimeMillis() -
                                connLockTime[i];
                            if(debugLevel > 2) {
                                log.println("Warning.  Connection " + i +
                                            " in use for " + timeInUse +
                                            " ms");
                            }
                            if(maxCheckoutMillis != 0) {
                                if(timeInUse > maxCheckoutMillis) {
                                    if(debugLevel > 1) {
                                        log.println("Warning. Connection " +
                                                    i + " failed to be returned in time.  Recycling...");
                                    }
                                    throw new SQLException();
                                }
                            }

                            continue;
                        }
                        connStatus[i] = 2; // Take offline (2 indicates housekeeping lock)
                    }


                    if(age > maxConnMSec) {  // Force a reset at the max conn time
                        throw new SQLException();
                    }

                    stmt = connPool[i].createStatement();
                    connStatus[i] = 0;  // Connection is O.K.
                    //log.println("Connection confirmed for conn = " +
                    //             String.valueOf(i));

                    // Some DBs return an object even if DB is shut down
                    if(connPool[i].isClosed()) {
                        throw new SQLException();
                    }


                    // Connection has a problem, restart it
                } catch(SQLException e) {

                    if(debugLevel > 1) {
                        log.println(new Date().toString() +
                                    " ***** Recycling connection " +
                                    String.valueOf(i) + ":");
                    }

                    try {
                        connPool[i].close();
                    } catch(SQLException e0) {
                        if(debugLevel > 0) {
                            log.println("Error!  Can't close connection!  Might have been closed already.  Trying to recycle anyway... (" + e0 + ")");
                        }
                    }

                    try {
                        createConn(i);
                    } catch(SQLException e1) {
                        if(debugLevel > 0) {
                            log.println("Failed to create connection: " + e1);
                        }
                        connStatus[i] = 0;  // Can't open, try again next time
                    }
                } finally {
                    try{if(stmt != null) {stmt.close();}} catch(SQLException e1){};
                }

            }

            try { Thread.sleep(20000); }  // Wait 20 seconds for next cycle

            catch(InterruptedException e) {
                // Returning from the run method sets the internal
                // flag referenced by Thread.isAlive() to false.
                // This is required because we don't use stop() to
                // shutdown this thread.
                return;
            }

        }

    } // End run

    /**
     * This method hands out the connections in round-robin order.
     * This prevents a faulty connection from locking
     * up an application entirely.  A browser 'refresh' will
     * get the next connection while the faulty
     * connection is cleaned up by the housekeeping thread.
     *
     * If the min number of threads are ever exhausted, new
     * threads are added up the the max thread count.
     * Finally, if all threads are in use, this method waits
     * 2 seconds and tries again, up to ten times.  After that, it
     * returns a null.
     */
    public Connection getConnection() {

        Connection conn=null;

        if(available){
            boolean gotOne = false;

            for(int outerloop=1; outerloop<=10; outerloop++) {

                try  {
                    int loop=0;
                    int roundRobin = connLast + 1;
                    if(roundRobin >= currConnections) roundRobin=0;

                    do {
                         synchronized(connStatus) {
                            if((connStatus[roundRobin] < 1) &&
                               (! connPool[roundRobin].isClosed())) {
                                    conn = connPool[roundRobin];
                                    connStatus[roundRobin]=1;
                                    connLockTime[roundRobin] =
                                        System.currentTimeMillis();
                                    connLast = roundRobin;
                                    gotOne = true;
                                    break;
                            } else {
                                loop++;
                                roundRobin++;
                                if(roundRobin >= currConnections) roundRobin=0;
                            }
                         }
                    }
                    while((gotOne==false)&&(loop < currConnections));

                }
                catch (SQLException e1) {
                    log.println("Error: " + e1);
                }

                if(gotOne) {
                    break;
                } else {
                    synchronized(this) {  // Add new connections to the pool
                        if(currConnections < maxConns) {

                            try {
                                createConn(currConnections);
                                currConnections++;
                            } catch(SQLException e) {
                                if(debugLevel > 0) {
                                    log.println("Error: Unable to create new connection: " + e);
                                }
                            }
                        }
                    }

                    try { Thread.sleep(2000); }
                    catch(InterruptedException e) {}
                    if(debugLevel > 0) {
                        log.println("-----> Connections Exhausted!  Will wait and try again in loop " +
                                    String.valueOf(outerloop));
                    }
                }

            } // End of try 10 times loop

        } else {
            if(debugLevel > 0) {
                log.println("Unsuccessful getConnection() request during destroy()");
            }
        } // End if(available)

        if(debugLevel > 2) {
            log.println("Handing out connection " +
                        idOfConnection(conn) + " --> " +
                        (new SimpleDateFormat("MM/dd/yyyy  hh:mm:ss a")).format(new java.util.Date()));
        }

        return conn;

    }

    /**
     * Returns the local JDBC ID for a connection.
     */
    public int idOfConnection(Connection conn) {
        int match;
        String tag;

        try {
            tag = conn.toString();
        }
        catch (NullPointerException e1) {
            tag = "none";
        }

        match=-1;

        for(int i=0; i< currConnections; i++) {
            if(connID[i].equals(tag)) {
                match = i;
                break;
            }
        }
        return match;
    }

    /**
     * Frees a connection.  Replaces connection back into the main pool for
     * reuse.
     */
    public String freeConnection(Connection conn) {
        String res="";

        int thisconn = idOfConnection(conn);
        if(thisconn >= 0) {
            connStatus[thisconn]=0;
            res = "freed " + conn.toString();
            //log.println("Freed connection " + String.valueOf(thisconn) +
            //            " normal exit: ");
        } else {
            if(debugLevel > 0) {
                log.println("----> Error: Could not free connection!!!");
            }
        }

        return res;

    }

    /**
     * Returns the age of a connection -- the time since it was handed out to
     * an application.
     */
    public long getAge(Connection conn) { // Returns the age of the connection in millisec.
        int thisconn = idOfConnection(conn);
        return System.currentTimeMillis() - connLockTime[thisconn];
    }

    private void createConn(int i)

        throws SQLException {

        Date now = new Date();

        try {
            Class.forName (dbDriver);

            connPool[i] = DriverManager.getConnection
                          (dbServer,dbLogin,dbPassword);

            connStatus[i]=0;
            connID[i]=connPool[i].toString();
            connLockTime[i]=0;
            connCreateDate[i] =  now.getTime();
        } catch (ClassNotFoundException e2) {
            if(debugLevel > 0) {
                log.println("Error creating connection: " + e2);
            }
        }

        log.println(now.toString() + "  Opening connection " + String.valueOf(i) +
                    " " + connPool[i].toString() + ":");
    }

    /**
     * Shuts down the housekeeping thread and closes all connections
     * in the pool. Call this method from the destroy() method of the servlet.
     */

    /**
     * Multi-phase shutdown.  having following sequence:
     * <OL>
     * <LI><code>getConnection()</code> will refuse to return connections.
     * <LI>The housekeeping thread is shut down.<br>
     *    Up to the time of <code>millis</code> milliseconds after shutdown of
     *    the housekeeping thread, <code>freeConnection()</code> can still be
     *    called to return used connections.
     * <LI>After <code>millis</code> milliseconds after the shutdown of the
     *    housekeeping thread, all connections in the pool are closed.
     * <LI>If any connections were in use while being closed then a
     *    <code>SQLException</code> is thrown.
     * <LI>The log is closed.
     * </OL><br>
     * Call this method from a servlet destroy() method.
     *
     * @param      millis   the time to wait in milliseconds.
     * @exception  SQLException if connections were in use after
     * <code>millis</code>.
     */
    public void destroy(int millis) throws SQLException {

        // Checking for invalid negative arguments is not necessary,
        // Thread.join() does this already in runner.join().

        // Stop issuing connections
        available=false;

        // Shut down the background housekeeping thread
        runner.interrupt();

        // Wait until the housekeeping thread has died.
        try { runner.join(millis); }
        catch(InterruptedException e){} // ignore

        // The housekeeping thread could still be running
        // (e.g. if millis is too small). This case is ignored.
        // At worst, this method will throw an exception with the
        // clear indication that the timeout was too short.

        long startTime=System.currentTimeMillis();

        // Wait for freeConnection() to return any connections
        // that are still used at this time.
        int useCount;
        while((useCount=getUseCount())>0 && System.currentTimeMillis() - startTime <=  millis) {
            try { Thread.sleep(500); }
            catch(InterruptedException e) {} // ignore
        }

        // Close all connections, whether safe or not
        for(int i=0; i < currConnections; i++) {
            try {
                connPool[i].close();
            } catch (SQLException e1) {
                if(debugLevel > 0) {
                    log.println("Cannot close connections on Destroy");
                }
            }
        }

        if(useCount > 0) {
            //bt-test successful
            String msg="Unsafe shutdown: Had to close "+useCount+
                " active DB connections after "+millis+"ms";
            log.println(msg);
            // Close all open files
            log.close();
            // Throwing following Exception is essential because servlet authors
            // are likely to have their own error logging requirements.
            throw new SQLException(msg);
        }

        // Close all open files
        log.close();

    }//End destroy()


    /**
     * Less safe shutdown.  Uses default timeout value.
     * This method simply calls the <code>destroy()</code> method
     * with a <code>millis</code>
     * value of 10000 (10 seconds) and ignores <code>SQLException</code>
     * thrown by that method.
     * @see     #destroy(int)
     */
    public void destroy() {
        try {
            destroy(10000);
        }
        catch(SQLException e) {}
    }



    /**
     * Returns the number of connections in use.
     */
    // This method could be reduced to return a counter that is
    // maintained by all methods that update connStatus.
    // However, it is more efficient to do it this way because:
    // Updating the counter would put an additional burden on the most
    // frequently used methods; in comparison, this method is
    // rarely used (although essential).
    public int getUseCount() {
        int useCount=0;
        synchronized(connStatus) {
            for(int i=0; i < currConnections; i++) {
                if(connStatus[i] > 0) { // In use
                    useCount++;
                }
            }
        }
        return useCount;
    }//End getUseCount()

    /**
     * Returns the number of connections in the dynamic pool.
     */
    public int getSize() {
        return currConnections;
    }//End getSize()



    /**
     * Inserts  the data into the database
     * @param query
     */
    public int insertUpdateOrDeleteData(String query) throws java.sql.SQLException {
      Connection conn = getConnection();
      Statement stat = conn.createStatement();
      //System.out.println("Query = "+query);
      int rows = stat.executeUpdate(query+";");
      stat.execute("commit;");
      freeConnection(conn);
      return rows;
    }


     /**
      * Runs the select query on the database
      * @param query
      * @return
      */
     public ResultSet selectData(String sql) throws java.sql.SQLException {
       Connection conn = getConnection();
       Statement stat = conn.createStatement();
       //gets the resultSet after running the query
       //System.out.println("Query = "+sql);
       ResultSet result = stat.executeQuery(sql+";");
       // create CachedRowSet and populate
       //CachedRowSetImpl crs = new CachedRowSetImpl();
       //crs.populate(result);
       //result.close();
      
       freeConnection(conn);
       return result;
     }



   } // End class
