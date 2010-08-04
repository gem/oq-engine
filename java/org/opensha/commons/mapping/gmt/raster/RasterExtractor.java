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

package org.opensha.commons.mapping.gmt.raster;

import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.StringTokenizer;

import javax.imageio.ImageIO;

import org.opensha.commons.util.FileUtils;

import com.lowagie.text.pdf.PdfReader;

public class RasterExtractor {
	
	String psFileName;
	String outFileName;
	boolean doTrans = true;
	
	byte transR = 0;
	byte transG = 0;
	byte transB = 0;
	
	public RasterExtractor(String psFileName, String outFileName) {
		this.psFileName = psFileName;
		this.outFileName = outFileName;
	}
	
	public BufferedImage getRasterImage() throws FileNotFoundException, IOException {
		
		ArrayList<String> lines = FileUtils.loadFile(psFileName);
		
		boolean reading = false;
		boolean colorimage = false;
		
		boolean ascii85 = false;
		boolean lzwDecode = false;
		
		int width = 0;
		int height = 0;
		int pixels = 0;
		int expected = 0;
		byte[] bytes = null;
		int byteCount = 0;
		
		int curLine = 0;
		
		String asciiImage = "";
		
		for (String line : lines) {
			if (!reading) {
				if (line.contains("false 3 colorimage")) {
					reading = true;
					StringTokenizer tok = new StringTokenizer(line);
					
					width = Integer.parseInt(tok.nextToken());
					height = Integer.parseInt(tok.nextToken());
					int depth = Integer.parseInt(tok.nextToken());
					if (depth != 8) {
						System.out.println("BAD DEPTH! EXITING!");
						return null;
					}
					pixels = width * height;
					expected = pixels * 3; // pixels * 1 byte for R, G, and B
					bytes = new byte[expected];
					
					System.out.println("time to READ: false 3 colorimage " + width + "x" + height + " " + pixels + " px");
					colorimage = true;
					continue;
				} else if (line.contains("ASCII85Decode")) {
					
					lzwDecode = line.contains("LZWDecode");
					
					int depth = 0;
					
					for (int i=curLine - 2; i<curLine+3; i++) {
						String parseLine = lines.get(i);
						StringTokenizer parseTok = new StringTokenizer(parseLine);
						while (parseTok.hasMoreTokens()) {
							String token = parseTok.nextToken();
							if (token.contains("/Width"))
								width = Integer.parseInt(parseTok.nextToken());
							else if (token.contains("/Height"))
								height = Integer.parseInt(parseTok.nextToken());
							else if (token.contains("/BitsPerComponent"))
								depth = Integer.parseInt(parseTok.nextToken());
						}
						if (width > 0 && height > 0 && depth > 0)
							break;
					}
					
					System.out.println(width + " " + height + " " + depth);
					
					if (width <= 0 || height <= 0 || depth != 8)
						return null;
					
					pixels = width * height;
					expected = pixels * 3; // pixels * 1 byte for R, G, and B
					bytes = new byte[expected];
					
					System.out.println("time to READ! ASCII85Decode " + width + "x" + height + " " + pixels + " px");
					
					reading = true;
					ascii85 = true;
					continue;
				}
			}
			if (reading && bytes != null) { //we're in the middle of the string
				if (ascii85) {
					if (line.startsWith(">> image"))
						continue;
					
					asciiImage += line + "\n";
					
					if (line.contains("~>")) {
//						System.out.println(line);
						break;
					}
				} else if (colorimage) {
					if (line.startsWith("U"))
						break;
					for (int i=0; i<line.length(); i+=2) {
						bytes[byteCount] = (byte) Integer.parseInt(line.substring(i, i+2), 16);
						
						byteCount++;
					}
				}
			}
			
			curLine++;
		}
		
		System.out.println("Done reading...converting.");
		
		
		if (ascii85) {
			InputStream is = new ByteArrayInputStream(asciiImage.getBytes("UTF-8"));
			ASCII85InputStream ais = new ASCII85InputStream(is);
			
//			System.out.println(asciiImage);
			
			while (!ais.isEndReached()) {
				if (byteCount < expected) {
					int data = ais.read();
					bytes[byteCount] = (byte) data;
					byteCount++;
				} else
					break;
			}
			if (lzwDecode) {
				bytes = PdfReader.LZWDecode(bytes);
			}
		}
		
		System.out.println("Read in " + byteCount + " bytes...expected: " + expected);
		
		return this.getBufferedImage(bytes, width, height);
	}
	
	
	public BufferedImage getBufferedImage(byte[] bytes, int width, int height) {
		BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
		
		int i=0;
		
		for (int y=0; y<height; y++) {
			for (int x=0; x<width; x++) {
//				int rgb = (int)bytes[i++]&0xffffff;
				
				byte b = bytes[i++];
				byte g = bytes[i++];
				byte r = bytes[i++];
				
				
				byte a = (byte) 255;
				if (doTrans && r == transR && b == transB && g == transG)
					a = (byte)0;
				
//				int rgb = ((int)r&0xFF)  // R
//                | ((int)g&0xFF) << 8   // G
//                | ((int)b&0xFF) << 16  // B
//                | 0xFF000000;
				
				int argb = ((int)r&0xFF)  // R
				| ((int)g&0xFF) << 8   // G
                | ((int)b&0xFF) << 16  // B
                | ((int)a&0xFF) << 24  // A
                | 0x00000000;
				
				image.setRGB(x, y, argb);
//				int rInt = r ;
//				System.out.println("0x " +r + " " + g + " " + b);
			}
		}
		
//		for (int i=0; i<bytes.length; i+=3) {
//			
//		}
		
		return image;
	}
	
	public void writePNG() throws FileNotFoundException, IOException {
		ImageIO.write(this.getRasterImage(), "png", new File(outFileName));
		System.out.println("DONE!");
	}
	
	
	/**
	 * @param args
	 */
	public static void main(String[] args) {
		String psFileName =  null;
		String pngFileName = null;
		if (args.length == 0) {
			System.err.println("WARNING: Running from debug mode with hardcoded paths!");
			psFileName =  "/home/kevin/OpenSHA/basin/plots/temp/basin.ps";
			pngFileName = "/home/kevin/OpenSHA/basin/plots/temp/extract.png";
		} else if (args.length == 2) {
			psFileName = args[0];
			pngFileName = args[1];
		} else {
			System.err.println("USAGE: RasterExtractor ps_file_name png_file_name");
			System.exit(2);
		}
		
		RasterExtractor extract = new RasterExtractor(psFileName, pngFileName);
		
		try {
			extract.writePNG();
			
			
			
		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}

	}

}
