package scratch.peter.coords;

import java.util.Arrays;

import org.apache.commons.lang.builder.ToStringBuilder;
import org.apache.commons.math.util.MathUtils;

/**
 * Add comments here
 *
 * 
 * @author Peter Powers
 * @version $Id:$
 * 
 */
public class Gridding {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		double minLon = -117.;
		double maxLon = -115.21;
		double minLat = 33.0;
		double maxLat = 35.69;
		
		double spacing = 0.25;
		
//		double numLonNodes = Math.floor((maxLon - minLon) / spacing) + 1;
//		double numLatNodes = Math.floor((maxLat - minLat) / spacing) + 1;
//		
//		System.out.println(numLonNodes);
//		System.out.println(numLatNodes);
		
		double[] lonNodes = initNodeCenters(minLon, maxLon, spacing);
		double[] latNodes = initNodeCenters(minLat, maxLat, spacing);
		
		//int numLonNodes = lonNodes.length;
		//int numLatNodes = latNodes.length;
		
		double[] lonNodeEdges = initNodeEdges(minLon, maxLon, spacing);
		double[] latNodeEdges = initNodeEdges(minLat, maxLat, spacing);
		
		System.out.println(new ToStringBuilder(lonNodes).append(lonNodes).toString());
		System.out.println(new ToStringBuilder(lonNodeEdges).append(lonNodeEdges).toString());
		
		System.out.println(new ToStringBuilder(latNodes).append(latNodes).toString());
		System.out.println(new ToStringBuilder(latNodeEdges).append(latNodeEdges).toString());
		
		//int idx = Arrays.binarySearch(latNodeEdges, 32.5);
		//System.out.println(idx);
		//search()
		
		System.out.println(getNodeIndex(latNodeEdges, 33.874));
		// 
	}
	
	/*
	 * Returns the node index of the value or -1 if the value is 
	 * out of range. Expects the array of edge values.
	 */
	private static int getNodeIndex(double[] edgeVals, double value) {
		// If a value exists in an array, binary search returns the index
		// of the value. If the value is less than the lowest array value,
		// binary search returns -1. If the value is within range or 
		// greater than the highest array value, binary search returns
		// (-insert_point-1). The SHA rule of thumb follows the java rules
		// of insidedness, so any exact node edge value is associated with 
		// the node above. Therefore, the negative within range values are 
		// adjusted to the correct node index with (-idx-2). Below range
		// values are already -1; above range values are corrected to -1.
		int idx = Arrays.binarySearch(edgeVals, value);
		return (idx < -1) ? (-idx - 2) : (idx == edgeVals.length-1) ? -1 : idx;
	}
	
	/*
	 * Initializes an array of node centers. The first (lowest) bin is 
	 * centered on the min value.
	 */
	private static double[] initNodeCenters(
			double min, double max, double width) {
		// nodeCount is num intervals between min and max + 1
		int nodeCount = (int) Math.floor((max - min) / width) + 1;
		double firstCenterVal = min;
		return buildArray(firstCenterVal, nodeCount, width);
	}
	
	/* 
	 * Initializes an array of node edges which can be used to associate
	 * a value with a particular node using binary search.
	 */
	private static double[] initNodeEdges(
			double min, double max, double width) {
		// edges is binCount + 1
		int edgeCount = (int) Math.floor((max - min) / width) + 2;
		// offset first bin edge half a binWidth
		double firstEdgeVal = min - (width / 2);
		return buildArray(firstEdgeVal, edgeCount, width);
	}
	
	/*
	 * Node edge and center array builder.
	 */
	private static double[] buildArray(
			double startVal, int count, double interval) {
		 
		double[] values = new double[count];
		double val = startVal;
		// store 'clean' values that do not reflect realities of
		// decimal precision, e.g. 34.5 vs. 34.499999999997, by forcing
		// meter-scale rounding precision.
		int scale = 5;
		for (int i=0; i<count; i++) {
			startVal = MathUtils.round(startVal, scale);
			values[i] = val;
			val += interval;
		}
		return values;
	}

}
