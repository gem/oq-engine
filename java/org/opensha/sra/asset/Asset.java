package org.opensha.sra.asset;
import java.util.Currency;
import java.util.HashMap;

import org.opensha.commons.data.Site;
import org.opensha.commons.param.ParameterList;
import org.opensha.sra.vulnerability.Vulnerability;

/**
 * A <code>PointAsset</code> represents a particular <code>AssetType</code> at 
 * a particular site. Potentially could reflect detailed building-specific
 * attributes such as cladding type, setbacks, shape, etc. via an
 * arbitrary parameter list. Flexible enough for earthquake, wind, or
 * flood risk.
 * 
 * NOTE: Concrete implementations of various asset types may be 
 * necessary if more detail/functionality is required than can be provided by
 * an Asset and internal AssetType alone.
 *
 *
 * NOTE: Placeholder
 * 
 * @author Peter Powers
 * @version $Id:$
 */
public class Asset {
	
	public Asset(int id, String name, AssetCategory type, Value value, Vulnerability vuln, Site site) {
		this.id = id;
		this.name = name;
		this.type = type;
		this.value = value;
		this.vuln = vuln;
		this.site = site;
		this.params = new ParameterList();
	}

	/**
	 * Returns the ...
	 * @return the
	 */
	public int getId() {
		return id;
	}
	/**
	 * Returns the ...
	 * @return the
	 */
	public String getName() {
		return name;
	}
	/**
	 * Returns the ...
	 * @return the
	 */
	public AssetCategory getType() {
		return type;
	}
	/**
	 * Returns the ...
	 * @return the
	 */
	public Value getValue() {
		return value;
	}
	/**
	 * Returns the ...
	 * @return the
	 */
	public Vulnerability getVulnerability() {
		return vuln;
	}
	/**
	 * Returns the ...
	 * @return the
	 */
	public Site getSite() {
		return site;
	}
	/**
	 * Returns the ...
	 * @return the
	 */
	public ParameterList getParams() {
		return params;
	}
	private int id;
	private String name;
	private AssetCategory type;
	private Value value;
	private Vulnerability vuln;
	private Site site;
	private ParameterList params;
	
	
	// TODO multiple vulnerabilities with weights
	
}
