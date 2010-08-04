package junk.webservices;


import javax.activation.DataHandler;

/**
 * <p>Title: </p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author unascribed
 * @version 1.0
 */

public interface GMT_WebServiceAPI extends java.rmi.Remote{

  public String runGMT_Script(String[] fileName, DataHandler[] dh) throws java.rmi.RemoteException;

}
