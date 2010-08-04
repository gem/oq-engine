/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.commons.geo;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.Iterator;
import java.util.List;
import java.util.ListIterator;

import org.dom4j.Element;
import org.opensha.commons.metadata.XMLSaveable;

/**
 * A customized <code>ArrayList</code> of <code>Location</code>s. In addition to
 * providing the functionality of the <code>List</code> interface, this class
 * provides several custom methods for querying and manipulating a collection of
 * <code>Location</code>s.
 * 
 * @author Peter Powers
 * @author Steven W. Rock
 * @version $Id: LocationList.java 6874 2010-07-29 23:45:55Z kmilner $
 */
public class LocationList extends ArrayList<Location> implements XMLSaveable {

	private static final long serialVersionUID = 1L;

	public static final String XML_METADATA_NAME = "LocationList";

	/**
	 * Convenience method to reverse the <code>Location</code>s in this list.
	 * Simply calls <code>Collections.reverse()</code>.
	 */
	public void reverse() {
		Collections.reverse(this);
	}

	/**
	 * Breaks this <code>LocationList</code> into multiple parts. If 
	 * <code>size</code> is less than or equal to the size of this list, a
	 * <code>List&lt;LocationList&gt;</code> containing only this 
	 * <code>LocationList</code> is returned. The last element in the
	 * <code>List&lt;LocationList&gt;</code> will be a <code>LocationList</code>
	 * of <code>size</code> or fewer <code>Location</code>s.
	 * 
	 * @param size of the smaller lists
	 * @return a <code>List&lt;LocationList&gt;</code> of smaller 
	 *         <code>LocationList</code>s
	 */
	public List<LocationList> split(int size) {
		ArrayList<LocationList> lists = new ArrayList<LocationList>();

		// quickly handle the trivial case
		if (size <= 0 || size() <= size) {
			lists.add(this);
			return lists;
		}

		LocationList cur = new LocationList();

		for (int i = 0; i < size(); i++) {
			if (i % size == 0 && i > 0) {
				lists.add(cur);
				cur = new LocationList();
			}
			cur.add(get(i));
		}

		if (cur.size() > 0) lists.add(cur);

		return lists;
	}

	/**
	 * Computes the horizontal surface distance (in km) to the closest point in 
	 * this list from the supplied <code>Location</code>. This method uses 
	 * {@link LocationUtils#horzDistance(Location, Location)} to compute
	 * the distance.
	 * 
	 * @param loc <code>Location</code> of interest
	 * @return the distance to the closest point in this 
	 *         <code>LocationList</code>
	 * @see LocationUtils#horzDistance(Location, Location)
	 */
	public double minDistToLocation(Location loc) {
		double min = Double.MAX_VALUE;
		double dist = 0;
		for (Location p : this) {
			dist = LocationUtils.horzDistance(loc, p);
			if (dist < min) min = dist;
		}
		return min;
	}

	/**
	 * Computes the shortest horizontal distance (in km) from the supplied
	 * <code>Location</code> to the line defined by connecting the points in 
	 * this <code>LocationList</code>. This method uses 
	 * {@link LocationUtils#distanceToLineFast(Location, Location, Location)}
	 * and is inappropriate for for use at large separations (e.g. &gt;200 km).
	 * 
	 * @param loc <code>Location</code> of interest
	 * @return the shortest distance to the line defined by this
	 *         <code>LocationList</code>
	 */
	public double minDistToLine(Location loc) {
		double min = Double.MAX_VALUE;
		double dist = 0;
		for (int i = 1; i < size(); i++) {
			dist = LocationUtils.distanceToLineFast(
					get(i - 1), get(i), loc);
			if (dist < min) min = dist;
		}
		return min;
	}

	/**
	 * Overriden to return a <code>LocationList</code> with a deep copy of the
	 * <code>Location</code>s spanned by the requested range.
	 * 
	 * @return a deep copy of the range of <code>Location</code>s specified
	 */
	@Override
	public LocationList subList(int fromIndex, int toIndex) {
		List<Location> source = super.subList(fromIndex, toIndex);
		LocationList subLocList = new LocationList();
		for (Location loc : source) {
			subLocList.add(loc.clone());
		}
		return subLocList;
	}
	
	/**
	 * Overriden to return a deep copy of this <code>LocationList</code>.
	 * 
	 * @return a deep copy of this list
	 */
	@Override
	public LocationList clone() {
		LocationList clone = new LocationList();
		for (Location loc : this) {
			clone.add(loc.clone());
		}
		return clone;
	}

	@Override
	public boolean equals(Object obj) {
		if (this == obj) return true;
		if (!(obj instanceof LocationList)) return false;
		LocationList ll = (LocationList) obj;
		if (size() != ll.size()) return false;
		for (int i = 0; i < size(); i++) {
			if (!(get(i).equals(ll.get(i)))) return false;
		}
		return true;
	}

	@Override
	public int hashCode() {
		int v = 0;
		boolean add = true;
		for (Location loc : this) {
			// make each smaller to avoid possible overrun of int
			int locCode = loc.hashCode() / 1000;
			v = (add) ? v + locCode : v - locCode;
			add = !add;
		}
		return v;
	}

	@Override
	public String toString() {
		StringBuffer b = new StringBuffer();
		b.append("LocationList size: " + size() + "\n");
		b.append("LocationList data: ");
		for (Location loc : this) {
			b.append(loc + " ");
		}
		return b.toString();
	}

	public Element toXMLMetadata(Element root) {
		Element locs = root.addElement(LocationList.XML_METADATA_NAME);
		for (int i = 0; i < this.size(); i++) {
			Location loc = this.get(i);
			locs = loc.toXMLMetadata(locs);
		}

		return root;
	}

	public static LocationList fromXMLMetadata(Element locationElement) {
		LocationList locs = new LocationList();
		Iterator<Element> it = locationElement.elementIterator();
		while (it.hasNext()) {
			Element el = it.next();
			if (el.getName().equals(Location.XML_METADATA_NAME)) {
				locs.add(Location.fromXMLMetadata(el));
			}
		}
		return locs;
	}
	
	public static double calcMinLat(Collection<Location> locs) {
		double min = Double.MAX_VALUE;
		for (Location loc : locs) {
			double val = loc.getLatitude();
			if (val < min)
				min = val;
		}
		return min;
	}
	
	public static double calcMinLon(Collection<Location> locs) {
		double min = Double.MAX_VALUE;
		for (Location loc : locs) {
			double val = loc.getLongitude();
			if (val < min)
				min = val;
		}
		return min;
	}
	
	public static double calcMaxLat(Collection<Location> locs) {
		double max = Double.NEGATIVE_INFINITY;
		for (Location loc : locs) {
			double val = loc.getLatitude();
			if (val > max)
				max = val;
		}
		return max;
	}
	
	public static double calcMaxLon(Collection<Location> locs) {
		double max = Double.NEGATIVE_INFINITY;
		for (Location loc : locs) {
			double val = loc.getLongitude();
			if (val > max)
				max = val;
		}
		return max;
	}
	
	/**
	 * Returns an unmodifiable view of this <code>LocationList</code>. Any 
	 * calls to methods that would result in a change to this list will
	 * throw an <code>UnsupportedOperationException</code>. Clones of an
	 * unmodifiable <code>LocationList</code> (deep-copies) are editable.
	 * 
	 * @return an unmodifiable view of this list
	 */
	public LocationList unmodifiableList() {
		return new UnmodifiableLocationList(this);
	}
	
	private final static class UnmodifiableLocationList extends LocationList {
		private static final long serialVersionUID = 1L;

		final LocationList ll;

		UnmodifiableLocationList(LocationList ll) { 
			this.ll = ll;
		}
		
		// Pass-through operations
		
		@Override
		public LocationList clone()			{ return ll.clone(); }
		@Override
		public boolean contains(Object o) 	{ return ll.contains(o); }
		@Override
		public boolean containsAll(Collection<?> coll) {
			return ll.containsAll(coll);
		}
		@Override
		public boolean equals(Object o)		{ return ll.equals(o); }
		@Override
		public Location get(int index)		{ return ll.get(index); }
		@Override
		public int hashCode()				{ return ll.hashCode(); }
		@Override
		public int indexOf(Object o)		{ return ll.indexOf(o); }
		@Override
		public boolean isEmpty()			{ return ll.isEmpty(); }
		@Override
		public int lastIndexOf(Object o)	{ return ll.lastIndexOf(o); }
		@Override
		public int size()					{ return ll.size(); }
		@Override
		public Object[] toArray()			{ return ll.toArray(); }
		@Override
		public <T> T[] toArray(T[] a)		{ return ll.toArray(a); }
		@Override
		public String toString()			{ return ll.toString(); }
		@Override
		public LocationList subList(int fromIndex, int toIndex) {
			return ll.subList(fromIndex, toIndex); 
		}
		
		
		// Unsupported operations
		
		@Override
		public boolean add(Location e) {
			throw new UnsupportedOperationException();
		}
		@Override
		public void add(int index, Location element) {
			throw new UnsupportedOperationException();
		}
		@Override
		public boolean addAll(Collection<? extends Location> coll) {
			throw new UnsupportedOperationException();
		}
		@Override
		public boolean addAll(int index, Collection<? extends Location> coll) {
			throw new UnsupportedOperationException();
		}
		@Override
		public void clear() {
			throw new UnsupportedOperationException();
		}
		@Override
		public Location remove(int index) {
			throw new UnsupportedOperationException();
		}
		@Override
		public boolean remove(Object o) {
			throw new UnsupportedOperationException();
		}
		@Override
		public boolean removeAll(Collection<?> coll) {
			throw new UnsupportedOperationException();
		}
		@Override
		public boolean retainAll(Collection<?> coll) {
			throw new UnsupportedOperationException();
		}
		@Override
		public Location set(int index, Location element) {
			throw new UnsupportedOperationException();
		}
		@Override
		public Iterator<Location> iterator() {
			return new Iterator<Location>() {
				Iterator<? extends Location> it = ll.iterator();
				@Override
				public boolean hasNext() { return it.hasNext(); }
				@Override
				public Location next() { return it.next(); }
				@Override
				public void remove() {
					throw new UnsupportedOperationException();
				}
			};
		}
		@Override
		public ListIterator<Location> listIterator() {
			return listIterator(0);
		}
		@Override
		public ListIterator<Location> listIterator(final int index) {
			return new ListIterator<Location>() {
				ListIterator<? extends Location> it = ll.listIterator(index);
				@Override
				public boolean hasNext() { return it.hasNext(); }
				@Override
				public Location next() { return it.next(); }
				@Override
				public boolean hasPrevious() { return it.hasPrevious(); }
				@Override
				public Location previous() { return it.previous(); }
				@Override
				public int nextIndex() { return it.nextIndex(); }
				@Override
				public int previousIndex() { return it.previousIndex(); }
				@Override
				public void remove() {
					throw new UnsupportedOperationException();
				}
				@Override
				public void set(Location e) {
					throw new UnsupportedOperationException();
				}
				@Override
				public void add(Location e) {
					throw new UnsupportedOperationException();
				}
			};
		}
	}

    
}