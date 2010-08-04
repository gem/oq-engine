package scratch.matt.calc;

/**
 * <p>Title: NoValsFoundException</p>
 * <p>Description: </p>
 * @author Matt Gerstenberger
 * @version 1.0 2004
 */

// Exception if a list is returned empty
public class NoValsFoundException extends RuntimeException{
  public NoValsFoundException() {
    super("No values found in list...");
  }

}
