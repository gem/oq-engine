package org.opensha.sha.earthquake.rupForecastImpl.remoteERF_Clients;


import static org.junit.Assert.*;

import java.net.MalformedURLException;
import java.rmi.NotBoundException;
import java.rmi.RemoteException;

import org.junit.Before;
import org.junit.Test;

public class Test_RMI_ERFs_Operational {

	@Before
	public void setUp() throws Exception {
	}
	
	@Test
	public void testFrankel96() {
		Frankel96_AdjustableEqkRupForecastClient erf = null;
		try {
			erf = new Frankel96_AdjustableEqkRupForecastClient();
		} catch (RemoteException e) {
			e.printStackTrace();
			fail("RemoteException: " + e.getMessage());
		} catch (MalformedURLException e) {
			e.printStackTrace();
			fail("MalformedURLException: " + e.getMessage());
		} catch (NotBoundException e) {
			e.printStackTrace();
			fail("NotBoundException: " + e.getMessage());
		}
		assertNotNull("ERF should not be null!", erf);
		erf.updateForecast();
	}
	
	@Test
	public void testWG02_Fortran() {
		WG02_FortranWrappedERF_EpistemicListClient erf = null;
		try {
			erf = new WG02_FortranWrappedERF_EpistemicListClient();
		} catch (RemoteException e) {
			e.printStackTrace();
			fail("RemoteException: " + e.getMessage());
		}
		assertNotNull("ERF should not be null!", erf);
		try {
			erf.updateForecast();
		} catch (NullPointerException e) {
			// TODO Auto-generated catch block
			fail("NullPointerException: " + e.getMessage());
		}
	}

}
