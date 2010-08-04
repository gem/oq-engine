package org.opensha.sha.imr.attenRelImpl.peer;

public class PeerTest {
	
	TestSet testSet;
	TestCase testCase;
	TestSite testSite;
	
	PeerTest(TestSet testSet, TestCase testCase, TestSite testSite) {
		this.testSet = testSet;
		this.testCase = testCase;
		this.testSite = testSite;
	}
	
	public String toString() {
		return testSet+"-"+testCase+"-"+testSite;
	}
	
	public TestSet getSet() { return testSet; }
	public TestCase getCase() { return testCase; }
	public TestSite getSite() { return testSite; }
	
}
