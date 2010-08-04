package org.opensha.commons.util.threads;

/**
 * Interface for an embarassingly parallel Task which can be computed in a threaded fashion
 * 
 * @author kevin
 *
 */
public interface Task {
	
	public void compute();

}
