package org.opensha.commons.util.threads;

import java.util.ArrayList;
import java.util.Stack;
import java.util.TimerTask;

public class StackPrecentWatcher extends TimerTask {
	
	private Stack<?> stack;
	private int precentMod;
	
	private int initialSize;
	
	ArrayList<Integer> notifications = new ArrayList<Integer>();
	
	private ArrayList<TaskProgressListener> listeners;
	
	public StackPrecentWatcher(Stack<?> stack, int precentMod, ArrayList<TaskProgressListener> listeners) {
		this.stack = stack;
		this.precentMod = precentMod;
		initialSize = stack.size();
		this.listeners = listeners;
	}

	@Override
	public void run() {
		int tasksLeft = stack.size();
		int tasksDone = initialSize - tasksLeft;
		double pdone = (double)tasksDone / (double) initialSize * 100d;
		Integer pDivMod = (int)(pdone / (double)precentMod);
		
		if (notifications.contains(pDivMod))
			return;
//		System.out.println("Adding notification mod: " + pDivMod);
		notifications.add(pDivMod);
		for (TaskProgressListener listener : listeners) {
			listener.taskProgressUpdate(tasksDone, tasksLeft, initialSize);
		}
	}
	
}
