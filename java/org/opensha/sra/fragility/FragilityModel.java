package org.opensha.sra.fragility;

/**
 * A <code>FragilityModel</code> represents a probabilistic relationship
 * between an Intensity Measure Type (IMT) and discrete <code>LimitState</code>
 * for a given <code>AssetType</code>. An IMT can be a scalar measure
 * of the degree of excitation in an event, such as peak ground acceleration.
 * A <code>FragilityModel</code> provides methods to calculate 
 * the distribution of a <code>LimitState</code> for a given Intensity Measure 
 * Level (IML). A <code>FragilityModel</code> wraps one or more <code>
 * FragilityFunction</code>s.
 * 
 * TODO revisit
 *
 * @author Peter Powers
 * @version $Id:$
 */
public interface FragilityModel {

}
