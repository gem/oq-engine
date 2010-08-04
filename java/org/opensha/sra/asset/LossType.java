package org.opensha.sra.asset;

import java.util.ArrayList;
import java.util.List;

/**
 * This <code>enum</code> identifies different types of losses. For a 
 * building or contents <code>AssetType</code>, the only loss type is 
 * repair cost. People have several possible loss types related to injury:
 * Maximum Abbreviated Injury Severity (0, 1, 2, … 6); HAZUS injury 
 * severity (0, 1, … 4); or workers’ comp injury severity 
 * (none, PT, PP, TT, or TP). Economic output has one loss type: economic 
 * cost of loss of use.
 * 
 * @author Peter Powers
 * @version $Id:$
 * @see AssetCategory
 */
public enum LossType {

	/** Repair cost as a fraction of replacement cost. */
	REPAIR_COST(new AssetCategory[] {AssetCategory.BUILDING, AssetCategory.CONTENTS}),
	
	/** Fraction of indoor occupants injured to HAZUS severity 1. */
	HAZUS_1(new AssetCategory[] {AssetCategory.OCCUPANTS}),
	
	/** Fraction of indoor occupants injured to HAZUS severity 2. */
	HAZUS_2(new AssetCategory[] {AssetCategory.OCCUPANTS}),
	
	/** Fraction of indoor occupants injured to HAZUS severity 3. */
	HAZUS_3(new AssetCategory[] {AssetCategory.OCCUPANTS}),
	
	/** Fraction of indoor occupants injured to HAZUS severity 4. */
	HAZUS_4(new AssetCategory[] {AssetCategory.OCCUPANTS}),
	
	/** Fraction of indoor occupants injured to ATC-13 severity 1. */
	ATC_13_1(new AssetCategory[] {AssetCategory.OCCUPANTS}),
	
	/** Fraction of indoor occupants injured to ATC-13 severity 2. */
	ATC_13_2(new AssetCategory[] {AssetCategory.OCCUPANTS}),
	
	/** Fraction of indoor occupants injured to ATC-13 severity 3. */
	ATC_13_3(new AssetCategory[] {AssetCategory.OCCUPANTS}),
	
	/** Fraction of a year required to make facility operational. */
	DOWN_TIME(new AssetCategory[] {AssetCategory.ECONOMIC});
	
	private List<AssetCategory> assetTypes;
	
	private LossType(AssetCategory[] assetTypes) {
		this.assetTypes = new ArrayList<AssetCategory>();
		for (AssetCategory at : assetTypes) {
			this.assetTypes.add(at);
		}
	}
	
	/**
	 * Returns the <code>AssetType</code>s for which this <code>LossType</code>
	 * is applicable.
	 *  
	 * @return a <code>Collection</code> of <code>AssetType</code>s
	 */
	public List<AssetCategory> getSupportedAssetTypes() {
		return null;
	}
	
}
