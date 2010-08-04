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

package org.opensha.commons.gridComputing;

import java.io.File;
import java.net.MalformedURLException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Iterator;

import org.dom4j.Document;
import org.dom4j.DocumentException;
import org.dom4j.Element;
import org.dom4j.io.SAXReader;
import org.opensha.commons.util.FileNameComparator;

public class XMLPresetLoader {
	
	public static final String DEFAULT_RP_SUBDIR = "rp";
	public static final String DEFAULT_SUBMIT_SUBDIR = "submit";
	public static final String DEFAULT_STORAGE_SUBDIR = "storage";
	
	public static final String XML_METADATA_NAME = "GridDefaultDirectores";
	public static final String XML_RP_ATT = "resourceProviders";
	public static final String XML_SUBMIT_ATT = "submitHosts";
	public static final String XML_STORAGE_ATT = "storageHosts";
	
	private String rpDir;
	private String storageDir;
	private String submitDir;
	
	/**
	 * Creates an XMLPresetLoader assuming the default subdirectories of the given directory
	 * @param confDir
	 */
	public XMLPresetLoader(String confDir) {
		this(confDir + File.separator + DEFAULT_RP_SUBDIR, confDir + File.separator + DEFAULT_SUBMIT_SUBDIR,
						confDir + File.separator + DEFAULT_STORAGE_SUBDIR);
	}
	
	/**
	 * Creates an XMLPresetLoader with the specified directories
	 * @param rpDir
	 * @param submitDir
	 * @param storageDir
	 */
	public XMLPresetLoader(String rpDir, String submitDir, String storageDir) {
		this.rpDir = rpDir;
		this.storageDir = storageDir;
		this.submitDir = submitDir;
	}
	
	private ArrayList<File> listXMLFiles(String dirPath) {
		File dir = new File(dirPath);
		
		ArrayList<File> files = new ArrayList<File>();
		
		File dirList[] = dir.listFiles();
		
		Arrays.sort(dirList, new FileNameComparator());
		
		for (File file : dirList) {
			// if it's not a file, skip it
			if (!file.isFile())
				continue;
			// if it's not an xml file, skip it
			if (!file.getName().trim().toLowerCase().endsWith(".xml"))
				continue;
			
			files.add(file);
		}
		
		return files;
	}
	
	private ArrayList<Document> loadXMLFiles(String dirPath) {
		ArrayList<Document> docs = new ArrayList<Document>();
		
		SAXReader reader = new SAXReader();
		
		for (File file : listXMLFiles(dirPath)) {
			try {
				Document doc = reader.read(file);
				
				docs.add(doc);
			} catch (MalformedURLException e) {
				System.err.println("Bad file: " + file.getPath());
			} catch (DocumentException e) {
				System.err.println("Bad XML Parse: " + file.getAbsolutePath());
			}
		}
		
		return docs;
	}
	
	public ArrayList<ResourceProvider> getResourceProviders() {
		ArrayList<ResourceProvider> rps = new ArrayList<ResourceProvider>();
		
		for (Document doc : loadXMLFiles(this.rpDir)) {
			Element root = doc.getRootElement();
			
			// an xml doc can contain multiple rp's
			Iterator<Element> it = root.elementIterator(ResourceProvider.XML_METADATA_NAME);
			
			// for each rp element
			while (it.hasNext()) {
				Element el = it.next();
				
				try {
					ResourceProvider rp = ResourceProvider.fromXMLMetadata(el);
					
					System.out.println("Loaded " + rp.getName());
					
					rps.add(rp);
				} catch (RuntimeException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
			}
		}
		
		return rps;
	}
	
	public ArrayList<SubmitHost> getSubmitHosts() {
		ArrayList<SubmitHost> subs = new ArrayList<SubmitHost>();
		
		for (Document doc : loadXMLFiles(this.submitDir)) {
			Element root = doc.getRootElement();
			
			// an xml doc can contain multiple rp's
			Iterator<Element> it = root.elementIterator(SubmitHost.XML_METADATA_NAME);
			
			// for each rp element
			while (it.hasNext()) {
				Element el = it.next();
				
				try {
					SubmitHost sub = SubmitHost.fromXMLMetadata(el);
					
					System.out.println("Loaded " + sub.getName());
					
					subs.add(sub);
				} catch (RuntimeException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
			}
		}
		
		return subs;
	}
	
	public ArrayList<StorageHost> getStorageHosts() {
		ArrayList<StorageHost> subs = new ArrayList<StorageHost>();
		
		for (Document doc : loadXMLFiles(this.storageDir)) {
			Element root = doc.getRootElement();
			
			// an xml doc can contain multiple rp's
			Iterator<Element> it = root.elementIterator(StorageHost.XML_METADATA_NAME);
			
			// for each rp element
			while (it.hasNext()) {
				Element el = it.next();
				
				try {
					StorageHost storage = StorageHost.fromXMLMetadata(el);
					
					System.out.println("Loaded " + storage.getName());
					
					subs.add(storage);
				} catch (RuntimeException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
			}
		}
		
		return subs;
	}
	
	public GridResourcesList getGridResourcesList() {
		return new GridResourcesList(this.getResourceProviders(), this.getSubmitHosts(), this.getStorageHosts());
	}
	
	public static XMLPresetLoader fromXMLMetadata(Element presetEl) {
		String rpDir = presetEl.attributeValue(XML_RP_ATT);
		String submitDir = presetEl.attributeValue(XML_SUBMIT_ATT);
		String storageDir = presetEl.attributeValue(XML_STORAGE_ATT);
		
		return new XMLPresetLoader(rpDir, submitDir, storageDir);
	}
	
	public static void main(String args[]) {
		XMLPresetLoader loader = new XMLPresetLoader("org/opensha/gridComputing/defaults/");
		
		System.out.println("Loading RP's");
		loader.getResourceProviders();
		System.out.println("Loading Submit Hosts");
		loader.getSubmitHosts();
		System.out.println("Loading Storage Hosts");
		loader.getStorageHosts();
		
//		for (ResourceProvider rp : loader.getResourceProviders()) {
//			System.out.println(rp.toString());
//		}
	}

}
