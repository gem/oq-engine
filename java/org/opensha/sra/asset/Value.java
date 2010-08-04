/**
 * 
 */
package org.opensha.sra.asset;

/**
 * A <code>Value</code> is a deterministic or probabilistic estimate of 
 * the value of the asset. For people, a 4-compoment parameter, all 
 * nonnegative integers: occupants weekday day, occupants weekday night, 
 * occupants weekend day, occupants weekend night. For money, a 3-component 
 * parameter: a nonnegative floating point number, with a year (YYYY) and 
 * an ISO 4217 currency code (CCC). 
 *
 * NOTE: placeholder
 * 
 * @author Peter Powers
 * @version $Id:$
 */
public interface Value {

	public int getValueBasisYear();
}
