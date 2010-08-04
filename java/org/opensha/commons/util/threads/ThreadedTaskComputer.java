package org.opensha.commons.util.threads;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.EmptyStackException;
import java.util.Stack;
import java.util.Timer;
import java.util.TimerTask;

/**
 * Class for calculating a {@link Collection} of embarassingly parallel {@link Task}
 * items in parallel on a single machine.
 * 
 * @author kevin
 *
 */
public class ThreadedTaskComputer implements Runnable {
	
	private Stack<? extends Task> stack;
	
	private TimerTask progressTimerTask = null;
	private int timerPeriodMilis = 5000;
	
	public ThreadedTaskComputer(Collection<? extends Task> tasks) {
		this(tasks, true);
	}
	
	private static Stack<Task> colToStack(Collection<? extends Task> tasks) {
		Stack<Task> stack = new Stack<Task>();
		for (Task task : tasks)
			stack.push(task);
		return stack;
	}
	
	public ThreadedTaskComputer(Collection<? extends Task> tasks, boolean shuffle) {
		this(colToStack(tasks), shuffle);
	}
	
	public ThreadedTaskComputer(Stack<? extends Task> stack, boolean shuffle) {
		this.stack = stack;
		
		if (shuffle)
			Collections.shuffle(stack);
	}
	
	private synchronized Task getNextTask() {
		return stack.pop();
	}
	
	public void computeSingleThread() {
		run();
	}
	
	/**
	 * Calculates all {@link Task}s in parellel with the number of available processors.
	 * 
	 * This method will block until all threads have completed
	 * 
	 * @param numThreads
	 * @throws InterruptedException
	 */
	public void computThreaded() throws InterruptedException {
		computThreaded(Runtime.getRuntime().availableProcessors());
	}
	
	/**
	 * Calculates all {@link Task}s in parellel with the given number of threads.
	 * 
	 * This method will block until all threads have completed
	 * 
	 * @param numThreads
	 * @throws InterruptedException
	 */
	public void computThreaded(int numThreads) throws InterruptedException {
		if (numThreads < 2) {
			computeSingleThread();
			return;
		}
		
		ArrayList<Thread> threads = new ArrayList<Thread>();
		
		Timer timer = null;
		
		// create the threads
		for (int i=0; i<numThreads; i++) {
			Thread t = new Thread(this);
			threads.add(t);
		}
		
		// init the progress timer
		if (progressTimerTask != null) {
			timer = new Timer();
			timer.schedule(progressTimerTask, 0, timerPeriodMilis);
		}

		// start the threads
		for (Thread t : threads) {
			t.start();
		}
		
		// join the threads
		for (Thread t : threads) {
			t.join();
		}
		
		// kill the timer
		if (timer != null) {
			timer.cancel();
		}
	}

	@Override
	public void run() {
		while (true) {
			try {
				Task task = getNextTask();
				task.compute();
			} catch (EmptyStackException e) {
				break;
			}
		}
	}
	
	public void setProgressTimer(TimerTask progressTimerTask) {
		this.progressTimerTask = progressTimerTask;
	}
	
	public void setProgressTimer(TaskProgressListener listener, int precentMod) {
		ArrayList<TaskProgressListener> listeners = new ArrayList<TaskProgressListener>();
		listeners.add(listener);
		setProgressTimer(listeners, precentMod);
	}
	
	public void setProgressTimer(ArrayList<TaskProgressListener> listeners, int precentMod) {
		progressTimerTask = new StackPrecentWatcher(stack, precentMod, listeners);
	}

}
