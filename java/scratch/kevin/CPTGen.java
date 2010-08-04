package scratch.kevin;

import java.awt.Color;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

import javax.imageio.ImageIO;

import org.opensha.commons.util.cpt.CPT;

public class CPTGen {
	
	String fileName = "";
	
	public CPTGen(ArrayList<int[]> colors, double min, double max, String outFile) throws IOException {
		this(colors, min, max, new File(outFile));
	}

	public CPTGen(ArrayList<int[]> colors, double min, double max, File outFile) throws IOException {
		fileName = outFile.getAbsolutePath();
		
		double step = (max - min) / ((double)colors.size() - 1d);
		FileWriter write = new FileWriter(outFile);
		int i=0;
		for (double curr = min; max-curr > 0.001; curr += step) {
			int color1[] = colors.get(i);
			int color2[] = colors.get(i+1);
			String line = round(curr) + "\t" + color1[0] + "\t" + color1[1] + "\t" + color1[2] + "\t" + round(curr + step) + "\t" + color2[0] + "\t" + color2[1] + "\t" + color2[2];
			System.out.println(line);
			write.write(line + "\n");
			i++;
		}
		int colB[] = colors.get(0);
		int colF[] = colors.get(colors.size() - 1);
		write.write("B " + colB[0] + "\t" + colB[1] + "\t" + colB[2] +"\n");
		write.write("F " + colF[0] + "\t" + colF[1] + "\t" + colF[2] +"\n");
		write.write("N 127	127	127\n");
		// this is a trivial comment to test Trac
		// this is another one!
		write.close();
	}
	
	public CPTGen(ArrayList<int[]> colors, float min, float max, float inc, String outFile) throws IOException {
		this(colors, min, max - inc, File.createTempFile("opensha", "cpt"));
		System.out.println("Loading from " + fileName);
		CPT cpt = CPT.loadFromFile(new File(fileName));
		FileWriter write = new FileWriter(outFile);
		
		for (float val=min; val<max; val+=inc) {
			Color color = cpt.getColor((float)val);
			int r = color.getRed();
			int g = color.getGreen();
			int b = color.getBlue();
			
			String line = val + "\t" + r + "\t" + g + "\t" + b + "\t" + (val+inc) + "\t" + r + "\t" + g + "\t" + b;
			System.out.println(line);
			write.write(line + "\n");
		}
		int colB[] = colors.get(0);
		int colF[] = colors.get(colors.size() - 1);
		write.write("B " + colB[0] + "\t" + colB[1] + "\t" + colB[2] +"\n");
		write.write("F " + colF[0] + "\t" + colF[1] + "\t" + colF[2] +"\n");
		write.write("N 127	127	127\n");
		write.close();
		
		CPT newCPT = CPT.loadFromFile(new File(outFile));
		BufferedImage bi = new BufferedImage(400, 50, BufferedImage.TYPE_INT_RGB);
		newCPT.paintGrid(bi);
		ImageIO.write(bi, "png", new File(outFile + ".png"));
	}
	
	public double round(double num) {
		int newNum = (int)(num * 100d + 0.5);
		return (double)newNum / 100d;
	}
	
	public static void main(String[] args) {
		ArrayList<int[]> colors = new ArrayList<int[]> ();
//		int color1[] = {0, 0, 170};
//		int color2[] = {0, 255, 255};
//		int color3[] = {0, 170, 30};
//		int color4[] = {200, 220, 15};
//		int color5[] = {255, 255, 0};
//		int color6[] = {255, 127, 0};
//		int color7[] = {255, 0, 0};
//		int color8[] = {255, 0, 255};
		
		int color1[] = {0, 0, 255};
		int color2[] = {0, 255, 255};
		int color3[] = {0, 255, 0};
		int color4[] = {255, 255, 0};
		int color5[] = {255, 127, 0};
		int color6[] = {255, 0, 0};
		int color7[] = {255, 0, 255};
		int color8[] = {100, 0, 100};
		int color9[] = {96, 57, 19};
		
		colors.add(color1);
		colors.add(color2);
		colors.add(color3);
		colors.add(color4);
		colors.add(color5);
		colors.add(color6);
		colors.add(color7);
		colors.add(color8);
		colors.add(color9);
		try {
//			new CPTGen(colors, 0, 1.4, "newcpt.cpt");
			new CPTGen(colors, 0f, 1.4f, 0.1f, "/home/kevin/CyberShake/scatterMap/gmt/cpt.cpt");
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}

	}

}
