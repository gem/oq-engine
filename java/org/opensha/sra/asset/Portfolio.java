package org.opensha.sra.asset;

import java.util.ArrayList;

import org.opensha.commons.data.NamedObjectAPI;

/**
 * A <code>Portfolio</code> represents a collecion of <code>Asset</code>s.
 * 
 * @author Peter Powers
 * @version $Id:$
 */
public class Portfolio extends ArrayList<Asset> implements NamedObjectAPI {

	private String name;
	
	/**
	 * Creates a new <code>Portfolio</code> with the given name.
	 * @param name the name of the <code>Portfolio</code>
	 */
	public Portfolio(String name) {
		this.name = name;
	}
	
	
	@Override
	public String getName() {
		return name;
	}

}
