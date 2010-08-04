package scratch.kevin;

import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JPasswordField;
import javax.swing.JTextField;

import org.opensha.refFaultParamDb.dao.db.ContributorDB_DAO;

public class MD5GUI extends JFrame implements ActionListener {
	
	private JPasswordField passField = new JPasswordField();
	private JTextField md5Field = new JTextField();
	private JButton updateButton = new JButton("update");
	
	JPanel panel = new JPanel();
	
	public MD5GUI() {
		panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
		panel.add(passField);
		panel.add(md5Field);
		panel.add(updateButton);
		
		updateButton.addActionListener(this);
		
		this.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		this.setContentPane(panel);
	}
	
	public static void main(String args[]) {
		MD5GUI gui = new MD5GUI();
		gui.pack();
		gui.setVisible(true);
	}

	@Override
	public void actionPerformed(ActionEvent arg0) {
		String pass = new String(passField.getPassword());
		md5Field.setText(ContributorDB_DAO.getEnryptedPassword(pass));
	}

}
