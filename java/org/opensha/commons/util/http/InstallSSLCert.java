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

package org.opensha.commons.util.http;

/*
 * Copyright 2006 Sun Microsystems, Inc.  All Rights Reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 *   - Redistributions of source code must retain the above copyright
 *     notice, this list of conditions and the following disclaimer.
 *
 *   - Redistributions in binary form must reproduce the above copyright
 *     notice, this list of conditions and the following disclaimer in the
 *     documentation and/or other materials provided with the distribution.
 *
 *   - Neither the name of Sun Microsystems nor the names of its
 *     contributors may be used to endorse or promote products derived
 *     from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
 * IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
 * THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR
 * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
 * PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
 * LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
 * NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.security.KeyManagementException;
import java.security.KeyStore;
import java.security.KeyStoreException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.cert.CertificateException;
import java.security.cert.X509Certificate;

import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLException;
import javax.net.ssl.SSLSocket;
import javax.net.ssl.SSLSocketFactory;
import javax.net.ssl.TrustManager;
import javax.net.ssl.TrustManagerFactory;
import javax.net.ssl.X509TrustManager;

/**
 * This class creates a temporary KeyStore and adds the SSL certificate for the specified host.
 * 
 * This allows you to connect to an server over SSL with a self signed certificate. It also has the
 * ability to verify the server's certificate's MD5 sum before adding it.
 * 
 * Example usage:
 * 
 * <code>InstallSSLCert installCert = new InstallSSLCert(intensityMD5, "intensity.usc.edu");
		
		File keystore = installCert.getKeyStore();
		
		if (keystore != null) {
			System.out.println("Loading keystore from: " + keystore.getAbsolutePath());
			System.setProperty("javax.net.ssl.trustStore", keystore.getAbsolutePath());
		}</code>
 * @author kevin
 *
 */
public class InstallSSLCert {
	
	char[] passphrase = "changeit".toCharArray();
	int port = 443;
	
	String expectedMD5;
	String host;
	
	public InstallSSLCert(String expectedMD5, String host) {
		this.expectedMD5 = expectedMD5;
		this.host = host;
	}
	
	public File getKeyStore() {
		try {
			File file = File.createTempFile("openSHA_SSLKeyStore_", ".ks");
			if (this.createKeyStore(file))
				return file;
			else return null;
		} catch (KeyStoreException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (NoSuchAlgorithmException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (CertificateException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (KeyManagementException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		
		return null;
	}
	
	public boolean createKeyStore(File file) throws KeyStoreException, NoSuchAlgorithmException, CertificateException, IOException, KeyManagementException {
		KeyStore ks;
		ks = KeyStore.getInstance(KeyStore.getDefaultType());
		ks.load(null, passphrase);
		
		SSLContext context = SSLContext.getInstance("TLS");
		TrustManagerFactory tmf =
			TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());
		tmf.init(ks);
		X509TrustManager defaultTrustManager = (X509TrustManager)tmf.getTrustManagers()[0];
		SavingTrustManager tm = new SavingTrustManager(defaultTrustManager);
		context.init(null, new TrustManager[] {tm}, null);
		SSLSocketFactory factory = context.getSocketFactory();

		System.out.println("Opening connection to " + host + ":" + port + "...");
		SSLSocket socket = (SSLSocket)factory.createSocket(host, port);
		socket.setSoTimeout(10000);
		
		try {
			System.out.println("Starting SSL handshake...");
			socket.startHandshake();
			socket.close();
			System.out.println();
			System.out.println("No errors, certificate is already trusted");
			return false;
		} catch (SSLException e) {
			System.out.println("Certificate needs to be added");
		}
		
		
		X509Certificate[] chain = tm.chain;
		if (chain == null) {
			System.out.println("Could not obtain server certificate chain");
			return false;
		}

		BufferedReader reader =
			new BufferedReader(new InputStreamReader(System.in));
		
		MessageDigest sha1 = MessageDigest.getInstance("SHA1");
		MessageDigest md5 = MessageDigest.getInstance("MD5");
		int i = 0;
		X509Certificate cert = chain[i];
		sha1.update(cert.getEncoded());
		md5.update(cert.getEncoded());
		String md5String = toHexString(md5.digest()).trim();
		
		md5String = stripMD5(md5String);
		expectedMD5 = stripMD5(expectedMD5);
		
		if (expectedMD5.length() == 0) {
			System.err.println("WARNING: The server's MD5 will not be verified.");
			System.err.println("Server MD5:\t" + md5String);
			expectedMD5 = md5String;
		}
		
		if (md5String.equals(expectedMD5)) {
			System.out.println("Server's MD5 checks out...adding to keystore!");
			
			String alias = host + "-" + (i + 1);
			ks.setCertificateEntry(alias, cert);

			OutputStream out = new FileOutputStream(file);
			ks.store(out, passphrase);
			out.close();

			System.out.println
			("Added certificate to keystore '" + file.getAbsolutePath() + "' using alias '"
					+ alias + "'");
			
			return true;
		} else {
			System.err.println("Server's MD5 does not match expected md5! Will not connect...");
			
			
			System.err.println
			("\nSubject:\t" + cert.getSubjectDN());
			System.err.println("Issuer:\t\t" + cert.getIssuerDN());
			System.err.println("sha1:\t\t" + stripMD5(toHexString(sha1.digest())));
			System.err.println("Expected MD5:\t" + expectedMD5);
			System.err.println("Actual MD5:\t" + md5String);
			
			return false;
		}
	}
	
	private String stripMD5(String md5) {
		md5 = md5.trim();
		md5 = md5.replaceAll(" ", "");
		md5 = md5.replaceAll("-", "");
		md5 = md5.replaceAll(":", "");
		md5 = md5.replaceAll("_", "");
		
		return md5;
	}

	public static void main(String[] args) throws Exception {
//		String host;
//		int port;
//		char[] passphrase;
//		args = new String[1];
//		args[0] = "intensity.usc.edu";
//		if ((args.length == 1) || (args.length == 2)) {
//			String[] c = args[0].split(":");
//			host = c[0];
//			port = (c.length == 1) ? 443 : Integer.parseInt(c[1]);
//			String p = (args.length == 1) ? "changeit" : args[1];
//			passphrase = p.toCharArray();
//		} else {
//			System.out.println("Usage: java InstallCert <host>[:port] [passphrase]");
//			return;
//		}
//
//		File file = new File("jssecacerts");
//		if (file.isFile() == false) {
//			char SEP = File.separatorChar;
//			File dir = new File("scratchJavaDevelopers" + SEP + "kevin" + SEP + "ssl" + SEP + "cert");
//			file = new File(dir, "javacerts");
//		}
//		System.out.println("Loading KeyStore " + file + "...");
////		InputStream in = new FileInputStream(file);
//		KeyStore ks = KeyStore.getInstance(KeyStore.getDefaultType());
//		ks.load(null, passphrase);
////		in.close();
//
//		SSLContext context = SSLContext.getInstance("TLS");
//		TrustManagerFactory tmf =
//			TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());
//		tmf.init(ks);
//		X509TrustManager defaultTrustManager = (X509TrustManager)tmf.getTrustManagers()[0];
//		SavingTrustManager tm = new SavingTrustManager(defaultTrustManager);
//		context.init(null, new TrustManager[] {tm}, null);
//		SSLSocketFactory factory = context.getSocketFactory();
//
//		System.out.println("Opening connection to " + host + ":" + port + "...");
//		SSLSocket socket = (SSLSocket)factory.createSocket(host, port);
//		socket.setSoTimeout(10000);
//		try {
//			System.out.println("Starting SSL handshake...");
//			socket.startHandshake();
//			socket.close();
//			System.out.println();
//			System.out.println("No errors, certificate is already trusted");
//		} catch (SSLException e) {
//			System.out.println();
//			e.printStackTrace(System.out);
//		}
//
//		X509Certificate[] chain = tm.chain;
//		if (chain == null) {
//			System.out.println("Could not obtain server certificate chain");
//			return;
//		}
//
//		BufferedReader reader =
//			new BufferedReader(new InputStreamReader(System.in));
//
//		System.out.println();
//		System.out.println("Server sent " + chain.length + " certificate(s):");
//		System.out.println();
//		MessageDigest sha1 = MessageDigest.getInstance("SHA1");
//		MessageDigest md5 = MessageDigest.getInstance("MD5");
//		for (int i = 0; i < chain.length; i++) {
//			X509Certificate cert = chain[i];
//			System.out.println
//			(" " + (i + 1) + " Subject " + cert.getSubjectDN());
//			System.out.println("   Issuer  " + cert.getIssuerDN());
//			sha1.update(cert.getEncoded());
//			System.out.println("   sha1    " + toHexString(sha1.digest()));
//			md5.update(cert.getEncoded());
//			System.out.println("   md5     " + toHexString(md5.digest()));
//			System.out.println();
//		}
//
//		System.out.println("Enter certificate to add to trusted keystore or 'q' to quit: [1]");
//		String line = reader.readLine().trim();
//		int k;
//		try {
//			k = (line.length() == 0) ? 0 : Integer.parseInt(line) - 1;
//		} catch (NumberFormatException e) {
//			System.out.println("KeyStore not changed");
//			return;
//		}
//
//		X509Certificate cert = chain[k];
//		String alias = host + "-" + (k + 1);
//		ks.setCertificateEntry(alias, cert);
//
//		OutputStream out = new FileOutputStream("jssecacerts");
//		ks.store(out, passphrase);
//		out.close();
//
//		System.out.println();
//		System.out.println(cert);
//		System.out.println();
//		System.out.println
//		("Added certificate to keystore 'jssecacerts' using alias '"
//				+ alias + "'");
	}

	private static final char[] HEXDIGITS = "0123456789abcdef".toCharArray();

	private static String toHexString(byte[] bytes) {
		StringBuilder sb = new StringBuilder(bytes.length * 3);
		for (int b : bytes) {
			b &= 0xff;
			sb.append(HEXDIGITS[b >> 4]);
			sb.append(HEXDIGITS[b & 15]);
			sb.append(' ');
		}
		return sb.toString();
	}

	private static class SavingTrustManager implements X509TrustManager {

		private final X509TrustManager tm;
		private X509Certificate[] chain;

		SavingTrustManager(X509TrustManager tm) {
			this.tm = tm;
		}

		public X509Certificate[] getAcceptedIssuers() {
			throw new UnsupportedOperationException();
		}

		public void checkClientTrusted(X509Certificate[] chain, String authType)
		throws CertificateException {
			throw new UnsupportedOperationException();
		}

		public void checkServerTrusted(X509Certificate[] chain, String authType)
		throws CertificateException {
			this.chain = chain;
			tm.checkServerTrusted(chain, authType);
		}
	}

}
