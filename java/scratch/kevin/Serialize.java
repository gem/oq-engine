package scratch.kevin;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.StringTokenizer;

public class Serialize {

	String codeBase = "";
	
	public Serialize(String codeBase) {
		this.codeBase = codeBase;
	}
	
	public void handleException(String trace) {
		StringTokenizer tok = new StringTokenizer(trace);
		while (tok.hasMoreTokens()) {
			String exception = tok.nextToken();
			if (exception.contains("java.io.NotSerializableException:")) {
				String className = tok.nextToken();
				System.out.println("Handling: " + className);
				String dirName = className.replaceAll("\\.", "/");
				String fileName = codeBase + dirName + ".java";
				System.out.println("File Name: " + fileName);
				StringTokenizer shortNameTok = new StringTokenizer(className, ".");
				String shortName = "";
				while (shortNameTok.hasMoreTokens()) {
					shortName = shortNameTok.nextToken();
				}
				if (className.equals("")) {
					System.out.println("FAILED!!");
					break;
				}
				System.out.println("Class Name: " + shortName);
				
				ArrayList<String> file = new ArrayList<String>();
				
				try {
			        BufferedReader in = new BufferedReader(new FileReader(fileName));
			        String line;
			        int i = 0;
			        boolean done = false;
			        while ((line = in.readLine()) != null) {
			            if (!done) {
			            	//System.out.println("******************************************");
				        	//System.out.println(line);
			            	if (line.contains(shortName) && line.contains("class")) {
			            		String before = line.substring(0, line.indexOf(shortName));
			            		String after = line.substring(line.indexOf(shortName) + shortName.length());
			            		System.out.println("BEFORE: " + before);
			            		System.out.println("AFTER: " + after);
			            		if (after.contains("{")) { // it is a one line definition
			            			System.out.println("One line def!");
			            		} else { // it's a multiline
			            			System.out.println("Multi line def!");
			            			while (true) {
			            				String newLine = in.readLine();
			            				line += " " + newLine;
			            				if (newLine.contains("{"))
			            					break;
			            			}
			            			System.out.println("new LINE: " + line);
			            			after = line.substring(line.indexOf(shortName) + shortName.length());
			            			System.out.println("new AFTER: " + after);
			            		}
			            		if (after.contains("implements")) {
			            			String beforeImp = line.substring(0, line.indexOf("implements"));
			            			String afterImp = line.substring(line.indexOf("implements") + 10);
			            			line = beforeImp + "implements java.io.Serializable," + afterImp; 
			            			//java.io.Serializable
		            			} else {
		            				String beforeBracket = before + shortName + after.substring(0, after.indexOf("{"));
			            			String afterBracket = line.substring(line.indexOf("{") + 1);
			            			line = beforeBracket + " implements java.io.Serializable {" + afterBracket; 
		            			}
			            		System.out.println("Final Line: " + line);
			            		done = true;
			            	}
			            }
			            file.add(line);
			        	i++;
			        }
			        in.close();
			        
			        if (done) {
			        	BufferedWriter out = new BufferedWriter(new FileWriter(fileName));
			        	for (String str : file) {
			        		out.write(str + "\n");
			        	}
			        	out.close();
			        	System.out.println("***DONE!!!***");
			        } else {
			        	System.out.println("FAILED!!!");
			        }
			    } catch (IOException e) {
			    	e.printStackTrace();
			    }
				break;
			}
		}
	}
}
