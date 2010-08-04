package org.opensha.sra.asset;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.List;

/**
 * This <code>enum</code> identifies the different types of assets of interest
 * in loss calculations.
 * 
 * @author Peter Powers
 * @version $Id:$
 * @see LossType
 */
public enum AssetCategory {

	/** Building asset type. */
	BUILDING(new LossType[] {LossType.REPAIR_COST}),
	
	
	/** Contents of building asset type. */
	CONTENTS(new LossType[] {LossType.REPAIR_COST}),
	
	
	/** Human asset type. */
	OCCUPANTS(new LossType[] {
			LossType.HAZUS_1,
			LossType.HAZUS_2,
			LossType.HAZUS_3,
			LossType.HAZUS_4,
			LossType.ATC_13_1,
			LossType.ATC_13_2,
			LossType.ATC_13_3 }),
	
	
	/** Economic value of lost time asset type. */
	ECONOMIC(new LossType[] {LossType.DOWN_TIME});
	
	private List<LossType> lossTypes;
	
	private AssetCategory(LossType[] lossTypes) {
		this.lossTypes = new ArrayList<LossType>();
		for (LossType lt : lossTypes) {
			this.lossTypes.add(lt);
		}
	}
	
	/**
	 * Returns an immutable list of supported <code>LossType</code>s for this
	 * <code>AssetType</code>.
	 * 
	 * @return the list of supported loss types
	 */
	public List<LossType> getLossTypes() {
		return Collections.unmodifiableList(lossTypes);
	}
}
