package org.opensha.sra.riskmaps;

import java.net.MalformedURLException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;

import org.dom4j.Document;
import org.dom4j.DocumentException;
import org.dom4j.Element;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.util.XMLUtils;

public class FragilityCurveReader {
	
	public static ArbitrarilyDiscretizedFunc loadFunc(String fileName, String damageStateName) throws MalformedURLException, DocumentException {
		Document doc = XMLUtils.loadDocument(fileName);
		
		Element root = doc.getRootElement();
		
		Element imlElem = root.element("iml");
		Iterator<Element> imlIt = imlElem.elementIterator("item");
		ArrayList<Double> xvals = new ArrayList<Double>();
		while (imlIt.hasNext()) {
			Element item = imlIt.next();
			double iml = Double.parseDouble(item.attributeValue("value"));
			xvals.add(iml);
		}
		Collections.sort(xvals);
		
		Element fragEl = root.element("fragility");
		Iterator<Element> damageIt = fragEl.elementIterator("damage_state");
		while (damageIt.hasNext()) {
			Element damageEl = damageIt.next();
			String name = damageEl.attributeValue("name");
			if (name.equals(damageStateName)) {
				Iterator<Element> valIt = damageEl.elementIterator("item");
				ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();
				func.setName(name);
				while (valIt.hasNext()) {
					Element valEl = valIt.next();
					int index = Integer.parseInt(valEl.attributeValue("index"));
					double val = Double.parseDouble(valEl.attributeValue("value"));
					func.set(xvals.get(index), val);
				}
				return func;
			}
		}
		
		return null;
	}

	/**
	 * @param args
	 * @throws DocumentException 
	 * @throws MalformedURLException 
	 */
	public static void main(String[] args) throws MalformedURLException, DocumentException {
		String fileName = "/home/kevin/OpenSHA/nico/Fragility_C1H_High_2p0sec.xml";
		ArbitrarilyDiscretizedFunc func = loadFunc(fileName, "Slight");
		System.out.println(func);
	}

}
