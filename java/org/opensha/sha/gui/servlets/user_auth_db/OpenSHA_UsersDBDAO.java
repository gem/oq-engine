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

package org.opensha.sha.gui.servlets.user_auth_db;

import java.io.IOException;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.Calendar;

import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
/**
 * <p>Title: OpenSHA_UsersDBDAO.java </p>
 * <p>Description: This class will interact with MySQL database for users management
 * for OpenSHA</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author Vipin Gupta, Nitin Gupta
 * @date Nov 15, 2004
 * @version 1.0
 */

public class OpenSHA_UsersDBDAO implements OpenSHA_UsersDAO {
  private final static String DB_SERVER="gravity.usc.edu";
  private final static String DB_NAME="OpenSHA_users";
  private final static String TABLE_NAME="users";
  private DB_ConnectionPool connect;
  private final static String SMTP_HOST="email.usc.edu";
  private final static String FROM = "OpenSHA-CME@scec.usc.edu";
  private final static String MAIL_SUBJECT = "Your account information on OpenSHA-CME system";
  private final static String SCEC_ADMIN_MAIL_SUBJECT = "New account added on OpenSHA-CME system";




  public OpenSHA_UsersDBDAO() {
	  try {
		connect = new DB_ConnectionPool("org.gjt.mm.mysql.Driver","jdbc:mysql://"+DB_SERVER+":3306/"+DB_NAME,
				  "cmeutils","level3",1,15,"opensha_db.log",0.5);
	} catch (IOException e) {
		// TODO Auto-generated catch block
		e.printStackTrace();
	}
  }


  /**
   * Add new OpenSHA user to the database
   * It encodes the password and then puts it into the MySQL database
   * @param newUserVO
   * @return
   */
  public boolean insertNewUser(OpenSHA_UsersVO newUserVO) {
    Calendar calendar = Calendar.getInstance();
    String datetime = new String(calendar.get(Calendar.YEAR) + "-" +
                                 (calendar.get(Calendar.MONTH) + 1) + "-" +
                                 calendar.get(Calendar.DAY_OF_MONTH) + "  " +
                                 calendar.get(Calendar.HOUR_OF_DAY) + ":" +
                                 calendar.get(Calendar.MINUTE) + ":" +
                                 calendar.get(Calendar.SECOND));

    String insertDataQuery = "insert into "+TABLE_NAME+
                             " (first_name, last_name, email, phone_number, organization, username, password, approved, creation_date, role)"+
                             "values (\""+newUserVO.getFirstName()+"\",\""+newUserVO.getLastName()+"\",\""+
                             newUserVO.getEmail()+"\",\""+newUserVO.getPhone()+"\",\""+
                             newUserVO.getOrganization()+"\",\""+newUserVO.getUsername()+
                             "\",MD5(\""+newUserVO.getPassword()+"\"),'"+newUserVO.getApprovalStatus()+"',\""+
                             datetime+"\",\""+newUserVO.getRole()+"\")";
    try
    { // add the jdbc transaction to get the primary key
      connect.insertUpdateOrDeleteData(insertDataQuery);
      if(true) { // mai lto SCEC admins about this new account
        String message =  "New account has been created on OpenSHA-CME system for user "+
            newUserVO.getFirstName()+" "+newUserVO.getFirstName()+"\n"+
            " username = "+newUserVO.getUsername()+ ", email="+newUserVO.getEmail()+"\n\n"+
            " Go to http://gravity.usc.edu:8080/usermanagement to approve/disapprove the user" ;
        String toEmailList="";
        ArrayList emailList = getAdminEmailList();
        for(int i=0; i<emailList.size();++i) toEmailList=toEmailList+","+emailList.get(i).toString();
        org.opensha.commons.util.MailUtil.sendMail(SMTP_HOST,FROM,toEmailList,SCEC_ADMIN_MAIL_SUBJECT,message);
      }
      return true;
    }
    catch (Exception ex)
    {
      ex.printStackTrace();
    }
    return false; // return false if user was not added successfully to the database
  }

  /**
   * returns an arrayList of emails of all the administrators on this system
   * @return
   */
  private ArrayList getAdminEmailList() {
    ArrayList approvedUsers = this.getApprovedUsers();
    ArrayList emails = new ArrayList();
    for(int i=0; i<approvedUsers.size(); ++i) {
      OpenSHA_UsersVO vo = (OpenSHA_UsersVO)approvedUsers.get(i);
      if(vo.getRole().equalsIgnoreCase(OpenSHA_UsersVO.ROLE_ADMIN))
         emails.add(vo.getEmail());
    }
    return emails;
  }


  /**
   * Update the user info in the database.
   * It will update all the fields except username, password and email
   * @param updatedUserVO
   */
  public void updateUser(OpenSHA_UsersVO updatedUserVO) {
    Calendar calendar = Calendar.getInstance();
    String datetime = new String(calendar.get(Calendar.YEAR) + "-" +
                                (calendar.get(Calendar.MONTH) + 1) + "-" +
                                calendar.get(Calendar.DAY_OF_MONTH) + "  " +
                                calendar.get(Calendar.HOUR_OF_DAY) + ":" +
                                calendar.get(Calendar.MINUTE) + ":" +
                                calendar.get(Calendar.SECOND));
   OpenSHA_UsersVO currentUser = this.getUser(updatedUserVO.getEmail());
   String approvalDate  = currentUser.getApprovalDate();

   // set the approval date if user is approved this time
   if(currentUser.getApprovalStatus() == OpenSHA_UsersVO.NOT_APPROVED &&
      updatedUserVO.getApprovalStatus() == OpenSHA_UsersVO.APPROVED) {
     approvalDate = datetime;
     String message =  "Your account on OpenSHA-CME system has been Approved";
     org.opensha.commons.util.MailUtil.sendMail(SMTP_HOST,FROM,updatedUserVO.getEmail(),MAIL_SUBJECT,message);
   }

   String update = new String("update "+TABLE_NAME+" set first_name=\""+
                                updatedUserVO.getFirstName() +
                                "\", last_name=\""+ updatedUserVO.getLastName()+
                                "\", phone_number=\""+updatedUserVO.getPhone()+
                                "\", organization=\""+updatedUserVO.getOrganization()+
                                "\", approved='"+
                                updatedUserVO.getApprovalStatus()+
                                "', modification_date=\""+datetime+"\""+
                                ", approval_date=\""+approvalDate+"\""+
                                ", role=\""+updatedUserVO.getRole()+"\""+
                                " where email=\""+updatedUserVO.getEmail()+"\"");

    try {
		connect.insertUpdateOrDeleteData(update);
	} catch (SQLException e) {
		// TODO Auto-generated catch block
		e.printStackTrace();
	}
  }

  /**
   *  update the user password
   */
  public void updatePassword(String email, String newPassword) {
    Calendar calendar = Calendar.getInstance();
   String datetime = new String(calendar.get(Calendar.YEAR) + "-" +
                                (calendar.get(Calendar.MONTH) + 1) + "-" +
                                calendar.get(Calendar.DAY_OF_MONTH) + "  " +
                                calendar.get(Calendar.HOUR_OF_DAY) + ":" +
                                calendar.get(Calendar.MINUTE) + ":" +
                                calendar.get(Calendar.SECOND));


   String update = new String("update "+TABLE_NAME+" set password=MD5(\""+newPassword+"\") "+
                              " where email=\""+email+"\"");

   try {
	connect.insertUpdateOrDeleteData(update);
} catch (SQLException e) {
	// TODO Auto-generated catch block
	e.printStackTrace();
}
  }

  /**
   * Reset the paswword for this user
   * @param email
   * @return
   */
   public void resetAndEmailPassword(String email) {
     java.util.Random random = new java.util.Random();
     String password=random.nextLong()+"";
     updatePassword(email,password);
     String message =  "Your username on OpenSHA-CME system is : "+this.getUser(email).getUsername()+"\n"+
         "Your password on OpenSHA-CME system is : "+password;
     org.opensha.commons.util.MailUtil.sendMail(SMTP_HOST,FROM,email,MAIL_SUBJECT,message);
   }

  /**
   * Remove the user from the database
   * @param updatedUserVO
   * @return
   */
  public void deleteUser(String email) {
    String delete = new String("delete from "+TABLE_NAME+" where email=\""+email+"\"");
    try {
		connect.insertUpdateOrDeleteData(delete);
	} catch (SQLException e) {
		// TODO Auto-generated catch block
		e.printStackTrace();
	}
  }

  /**
   * Wheether username/password combination is valid and whether user is approved
   * @param userName
   * @param password
   * @return
   */
  public OpenSHA_UsersVO getUserInfo(String userName, String password) {
    String query = new String("select first_name, last_name, email, phone_number,"+
                              "organization, username, Approved, creation_date,"+
                              "approval_date,modification_date,role "+
                              " from "+this.TABLE_NAME+
                               " where username=\""+userName+"\""+
                               " and password=MD5(\""+password+"\")");
    //System.out.println(query);
    
    try {
    	ResultSet queryResult = this.connect.queryData(query);
    if(queryResult.next())
      return getOpenSHA_UsersVO(queryResult.getString("first_name"),
                         queryResult.getString("last_name"),
                         queryResult.getString("email"),
                         queryResult.getString("phone_number"),
                         queryResult.getString("organization"),
                         queryResult.getString("username"),
                         queryResult.getString("creation_date"),
                         queryResult.getString("approval_date"),
                         queryResult.getString("modification_date"),
                         queryResult.getString("approved"),
                         queryResult.getString("role")
                         );

     else   return null;
    }catch(SQLException e) {
      e.printStackTrace();
    }
    return null;
  }

  /**
  * Get the status
  * @param userName
  * @param password
  * @return
  */
 public boolean isUserAuthorized(OpenSHA_UsersVO userVO) {
   if(userVO.getApprovalStatus()==OpenSHA_UsersVO.APPROVED) return true;
   return false;
 }


  /**
   * Returns  a list of OpenSHA_UsersVO objects
   *
   * @return
   */
  public ArrayList getAllUsers() {
    String query = new String("select first_name, last_name, email, phone_number,"+
                              "organization, username, Approved, creation_date,"+
                              "approval_date,modification_date,role "+
                              " from "+this.TABLE_NAME);
   ArrayList users = new ArrayList();
    try {
        ResultSet queryResult = this.connect.queryData(query);
    while(queryResult.next())
      users.add(getOpenSHA_UsersVO(queryResult.getString("first_name"),
                                    queryResult.getString("last_name"),
                                    queryResult.getString("email"),
                                    queryResult.getString("phone_number"),
                                    queryResult.getString("organization"),
                                    queryResult.getString("username"),
                                    queryResult.getString("creation_date"),
                                    queryResult.getString("approval_date"),
                                    queryResult.getString("modification_date"),
                                    queryResult.getString("approved"),
                                    queryResult.getString("role")
                                    ));
   }catch(SQLException e) {
     e.printStackTrace();
   }
   return users;
  }

  /**
   *
   * @param firstName
   * @param lastName
   * @param email
   * @param phoneNumber
   * @param organization
   * @param username
   * @param creationDate
   * @param approvalDate
   * @param modificationDate
   * @param approved
   * @return
   */
  private OpenSHA_UsersVO getOpenSHA_UsersVO(String firstName, String lastName,
      String email, String phoneNumber, String organization, String username,
      String creationDate, String approvalDate, String modificationDate,
      String approved,String role) {
    OpenSHA_UsersVO vo = new OpenSHA_UsersVO();
    vo.setFirstName(firstName);
    vo.setLastName(lastName);
    vo.setEmail(email);
    vo.setPhone(phoneNumber);
    vo.setOrganization(organization);
    vo.setUsername(username);
    vo.setCreationDate(creationDate);
    vo.setApprovalDate(approvalDate);
    vo.setModificationDate(modificationDate);
    vo.setApprovalStatus(approved.charAt(0));
    vo.setRole(role);
    return vo;
  }

  /**
   * Returns  a list of OpenSHA_UsersVO objects
   *
   * @return
   */
  public ArrayList getApprovedUsers() {
    String query = new String("select first_name, last_name, email, phone_number,"+
                             "organization, username, Approved, creation_date,"+
                             "approval_date,modification_date,role "+
                             " from "+this.TABLE_NAME+
                             " where Approved='"+OpenSHA_UsersVO.APPROVED+"'");
   
   ArrayList users = new ArrayList();
   try {
	   ResultSet queryResult = this.connect.queryData(query);  
     while(queryResult.next())
       users.add(getOpenSHA_UsersVO(queryResult.getString("first_name"),
                                    queryResult.getString("last_name"),
                                    queryResult.getString("email"),
                                    queryResult.getString("phone_number"),
                                    queryResult.getString("organization"),
                                    queryResult.getString("username"),
                                    queryResult.getString("creation_date"),
                                    queryResult.getString("approval_date"),
                                    queryResult.getString("modification_date"),
                                    queryResult.getString("approved"),
                                    queryResult.getString("role")
                                    ));
   }catch(SQLException e) {
     e.printStackTrace();
   }
   return users;

  }

  /**
   * Returns  a list of OpenSHA_UsersVO objects
   *
   * @return
   */

  public ArrayList getUnapprovedUsers() {
    String query = new String("select first_name, last_name, email, phone_number,"+
                            "organization, username, Approved, creation_date,"+
                            "approval_date,modification_date,role "+
                            " from "+this.TABLE_NAME+
                            " where Approved='"+OpenSHA_UsersVO.NOT_APPROVED+"'");
    
    ArrayList users = new ArrayList();
    try {
    	ResultSet queryResult = this.connect.queryData(query);
      while(queryResult.next())
        users.add(getOpenSHA_UsersVO(queryResult.getString("first_name"),
                                     queryResult.getString("last_name"),
                                     queryResult.getString("email"),
                                     queryResult.getString("phone_number"),
                                     queryResult.getString("organization"),
                                     queryResult.getString("username"),
                                     queryResult.getString("creation_date"),
                                     queryResult.getString("approval_date"),
                                     queryResult.getString("modification_date"),
                                     queryResult.getString("approved"),
                                     queryResult.getString("role")
                                     ));
    }catch(SQLException e) {
      e.printStackTrace();
    }
    return users;
  }


  // check whther this username has already been used in the database
  public boolean isNameUsed(String userName) {
    String query = new String("select first_name, last_name, email, phone_number,"+
                            "organization, username, Approved, creation_date,"+
                            "approval_date,modification_date"+
                            " from "+this.TABLE_NAME+
                            " where username=\""+userName+"\"");
    try {
    	ResultSet queryResult = this.connect.queryData(query);	
      if(queryResult.next())
        return true;
      else return false;
    }catch(SQLException e) {
      e.printStackTrace();
    }
    return false;
 }


  // get user info based on email address
  public OpenSHA_UsersVO getUser(String email) {
    String query = new String("select first_name, last_name, email, phone_number,"+
                            "organization, username, Approved, creation_date,"+
                            "approval_date,modification_date,role "+
                            " from "+this.TABLE_NAME+
                            " where email=\""+email+"\"");

    try {
    	ResultSet queryResult = this.connect.queryData(query);
      if(queryResult.next())
        return getOpenSHA_UsersVO(queryResult.getString("first_name"),
                                  queryResult.getString("last_name"),
                                  queryResult.getString("email"),
                                  queryResult.getString("phone_number"),
                                  queryResult.getString("organization"),
                                  queryResult.getString("username"),
                                  queryResult.getString("creation_date"),
                                  queryResult.getString("approval_date"),
                                  queryResult.getString("modification_date"),
                                  queryResult.getString("approved"),
                                  queryResult.getString("role")
                                  );
      else return null;
    }catch(SQLException e) {
      e.printStackTrace();
    }
    return null;
  }



  // email the userinfo to the email address
  public void emailUserName(String email) {
    OpenSHA_UsersVO vo = getUser(email);
    if(vo!=null) {
      String message = "Your username on OpenSHA-CME system is : "+vo.getUsername();
      org.opensha.commons.util.MailUtil.sendMail(SMTP_HOST,FROM,email,MAIL_SUBJECT,message);
    }
  }


  public void makeEmptyForTesting() {
    //String deleteDataQuery = "delete from "+TABLE_NAME;
    //connect.deleteOrUpdateData(deleteDataQuery);
  }

  public static void main(String args[]) {
    /*OpenSHA_UsersDBDAO dao = new OpenSHA_UsersDBDAO();
    OpenSHA_UsersVO newUserVO = new OpenSHA_UsersVO();
    newUserVO.setEmail("vgupta@usc.edu");
    newUserVO.setFirstName("User_firstname");
    newUserVO.setLastName("User_lastname");
    newUserVO.setOrganization("User_organization");
    newUserVO.setPassword("user_password");
    newUserVO.setPhone("11111111");
    newUserVO.setUsername("username-1");
    newUserVO.setApprovalStatus(OpenSHA_UsersVO.NOT_APPROVED);
    System.out.println(dao.insertNewUser(newUserVO));*/


  }

}
