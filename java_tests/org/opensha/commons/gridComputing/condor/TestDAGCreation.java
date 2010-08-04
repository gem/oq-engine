package org.opensha.commons.gridComputing.condor;


import java.io.File;
import java.io.IOException;

import junit.framework.TestCase;

import org.junit.Before;
import org.opensha.commons.gridComputing.condor.SubmitScript.Universe;
import org.opensha.commons.util.FileUtils;

public class TestDAGCreation extends TestCase {

	@Before
	public void setUp() throws Exception {
		
	}
	
	protected static DAG createSimpleTestDAG(String initialDir) {
		SubmitScriptForDAG id = new SubmitScriptForDAG("id", "/usr/bin/id", null,
				initialDir, Universe.SCHEDULER, false);
		SubmitScriptForDAG pwd = new SubmitScriptForDAG("pwd", "/bin/pwd", null,
				initialDir, Universe.SCHEDULER, false);
		SubmitScriptForDAG ls = new SubmitScriptForDAG("ls", "/bin/ls", "-lah",
				initialDir, Universe.SCHEDULER, false);
		SubmitScriptForDAG ps = new SubmitScriptForDAG("ps", "/bin/ps", "aux",
				initialDir, Universe.SCHEDULER, false);
		
		DAG dag = new DAG();
		
		dag.addJob(id);
		dag.addJob(pwd);
		dag.addJob(ls);
		dag.addJob(ps);
		
		dag.addParentChildRelationship(id, pwd);
		dag.addParentChildRelationship(id, ls);
		dag.addParentChildRelationship(pwd, ps);
		dag.addParentChildRelationship(ls, ps);
		
		return dag;
	}
	
	public void testDAGCreation() throws IOException {
		File tempDir = FileUtils.createTempDir();
		String dir = tempDir.getAbsolutePath() + File.separator;
		
		System.out.println("DIR: " + dir);
		
		DAG dag = createSimpleTestDAG(tempDir.getAbsolutePath());
		
		for (SubmitScriptForDAG job : dag.getJobs()) {
			job.writeScriptInDir(dir);
		}
		
		dag.writeDag(dir + "main.dag");
	}

}
