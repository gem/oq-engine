package scratch.matt.calc;

/**
 * <p>Title: </p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

//Matching value not found
public class NoValMatchFoundExcption extends RuntimeException {
  
  /**
   * default constructor for this class
   */
  public NoValMatchFoundExcption() {
    super("No matching value found...");
  }

}