package org.gem.engine.hazard.parsers.turkeyEmme;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class TurkeyReadSourceData {

    public Map<String, String> name = new HashMap<String, String>();
    public Map<String, Double> aGR = new HashMap<String, Double>();
    public Map<String, Double> bGR = new HashMap<String, Double>();
    public Map<String, Double> mMin = new HashMap<String, Double>();
    public Map<String, Double> mMax = new HashMap<String, Double>();

    // Define patterns
    Pattern CDPATT = Pattern.compile(";");
    Pattern FAULTPATT = Pattern
            .compile("^<fme:FAULT_NAME>(.+)</fme:FAULT_NAME>");
    Pattern COORTPATT = Pattern.compile("^<gml:posList>(.+)</gml:posList>");

    public TurkeyReadSourceData(BufferedReader input) {

        // Reading the file
        String code = null;

        try {
            // Instantiate a BufferedReader
            // BufferedReader input = new BufferedReader(new
            // FileReader(filename));
            // Try to read file containing source data
            try {

                String sCurrentLine;
                // Cycle over lines
                while ((sCurrentLine = input.readLine()) != null) {
                    sCurrentLine = sCurrentLine.trim();
                    // Search codes
                    Matcher match = CDPATT.matcher(sCurrentLine);
                    // First line identified (Source code + Name)
                    if (match.find()) {
                        String[] strarr = sCurrentLine.split(";");
                        code = strarr[1];
                        code = code.trim();
                        // Update the hash map
                        this.name.put(code, strarr[2]);
                        // Second line identified (aGR, bGR, mMin,mMax)
                    } else {
                        if (code != null) {
                            String[] strarr = sCurrentLine.split("\\s+");
                            this.aGR.put(code, Double.valueOf(strarr[0])
                                    .doubleValue());
                            this.bGR.put(code, Double.valueOf(strarr[1])
                                    .doubleValue());
                            this.mMin.put(code, Double.valueOf(strarr[2])
                                    .doubleValue());
                            this.mMax.put(code, Double.valueOf(strarr[3])
                                    .doubleValue());
                        }
                    }
                }

            } finally {
                input.close();
            }

            // Set<String>key = aGR.keySet();
            // System.out.println( "sources:" );
            // System.out.println( "sources:"+key.size());
            // int cnt = 0;
            // for (Iterator<String> it = key.iterator(); it.hasNext();) {
            // String tmpkey = it.next();
            // System.out.println(tmpkey);
            // System.out.println("  "+name.get(tmpkey));
            // System.out.println("  "+aGR.get(tmpkey));
            // System.out.println("  "+bGR.get(tmpkey));
            // }

        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    /**
     * 
     * @param filename
     */
    public TurkeyReadSourceData(File fleName) {

        // Reading the file
        String code = null;

        try {
            // Instantiate a BufferedReader
            BufferedReader input = new BufferedReader(new FileReader(fleName));
            // Try to read file containing source data
            try {

                String sCurrentLine;
                // Cycle over lines
                while ((sCurrentLine = input.readLine()) != null) {
                    sCurrentLine = sCurrentLine.trim();
                    // Search codes
                    Matcher match = CDPATT.matcher(sCurrentLine);
                    // First line identified (Source code + Name)
                    if (match.find()) {
                        String[] strarr = sCurrentLine.split(";");
                        code = strarr[1];
                        code = code.trim();
                        // Update the hash map
                        this.name.put(code, strarr[2]);
                        // Second line identified (aGR, bGR, mMin,mMax)
                    } else {
                        if (code != null) {
                            String[] strarr = sCurrentLine.split("\\s+");
                            this.aGR.put(code, Double.valueOf(strarr[0])
                                    .doubleValue());
                            this.bGR.put(code, Double.valueOf(strarr[1])
                                    .doubleValue());
                            this.mMin.put(code, Double.valueOf(strarr[2])
                                    .doubleValue());
                            this.mMax.put(code, Double.valueOf(strarr[3])
                                    .doubleValue());
                        }
                    }
                }

            } finally {
                input.close();
            }

            // Set<String>key = aGR.keySet();
            // System.out.println( "sources:" );
            // System.out.println( "sources:"+key.size());
            // int cnt = 0;
            // for (Iterator<String> it = key.iterator(); it.hasNext();) {
            // String tmpkey = it.next();
            // System.out.println(tmpkey);
            // System.out.println("  "+name.get(tmpkey));
            // System.out.println("  "+aGR.get(tmpkey));
            // System.out.println("  "+bGR.get(tmpkey));
            // }

        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }

    }

}
