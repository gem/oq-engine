package org.opensha.commons.mapping.gmt;

import static org.junit.Assert.*;

import java.awt.image.BufferedImage;
import java.io.IOException;
import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;

import javax.imageio.ImageIO;

import org.junit.BeforeClass;
import org.junit.Test;
import org.opensha.commons.data.ArbDiscretizedXYZ_DataSet;
import org.opensha.commons.exceptions.GMT_MapException;

public class TestGMT_MapGenerator {
	
	private static GMT_MapGenerator gmt;
	private static ArbDiscretizedXYZ_DataSet xyz;
	
	public static ArbDiscretizedXYZ_DataSet generateTestData() {
		ArbDiscretizedXYZ_DataSet xyz = new ArbDiscretizedXYZ_DataSet();
		int y = 0;
		for (double lat=33.5; lat<=35; lat+=0.1) {
			int x = 0;
			for (double lon=-119; lon<=-117; lon+=0.1) {
				xyz.addValue(lat, lon, x + y);
//				xyz.addValue(lon, lat, x + y);
				x++;
			}
			y++;
		}
		System.out.println("X Range: " + xyz.getMinX() + " => " + xyz.getMaxX());
		System.out.println("Y Range: " + xyz.getMinY() + " => " + xyz.getMaxY());
		System.out.println("Z Range: " + xyz.getMinZ() + " => " + xyz.getMaxZ());
		return xyz;
	}
	
	@BeforeClass
	public static void setUp() throws Exception {
		gmt = new GMT_MapGenerator();
		xyz = generateTestData();
	}
	

	@Test
	public void testGetGMTMapSpecification() {
		GMT_Map map = gmt.getGMTMapSpecification(xyz);
		assertNotNull(map);
	}

}
