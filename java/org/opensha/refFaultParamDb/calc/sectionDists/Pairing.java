package org.opensha.refFaultParamDb.calc.sectionDists;

import java.io.Serializable;

public class Pairing implements Serializable {
	
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	
	private int id1;
	private int id2;
	
	public Pairing() {}
	
	public Pairing(int id1, int id2) {
		this.id1 = id1;
		this.id2 = id2;
	}
	
	@Override
	public int hashCode() {
		final int prime = 31;
		int result = 1;
		result = prime * result + id1;
		result = prime * result + id2;
		return result;
	}

	@Override
	public boolean equals(Object obj) {
		if (this == obj)
			return true;
		if (obj == null)
			return false;
		if (getClass() != obj.getClass())
			return false;
		Pairing other = (Pairing) obj;
		if (id1 != other.id1)
			return false;
		if (id2 != other.id2)
			return false;
		return true;
	}
	
	public int getID1() {
		return id1;
	}

	public int getID2() {
		return id2;
	}

}
