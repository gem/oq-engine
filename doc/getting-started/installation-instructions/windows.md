(installing-windows)=

# Installing the OpenQuake Engine on Windows

The OpenQuake Engine can be installed on Windows with the [universal
installer](universal.md) (recommended if you plan to develop GMPEs)
or with a traditional .exe installer which can be downloaded from
[https://downloads.openquake.org/pkgs/windows/oq-engine/]
(https://downloads.openquake.org/pkgs/windows/oq-engine/). 
The .exe installer includes Python 3.11 and all required dependencies
and (since version 3.19) does not require Windows administrator 
privileges.

## Requirements

Requirements are:

- Windows 10 or 11 (64bit)
- at least 16 GB of RAM (32GB recommended for Windows 11)
- 4 GB of free disk space

**Windows 7** and **Windows 8** are not supported. 

We recommend using a Linux server for large calculations such as 
national or regional-scale models.

## Installation Procedure
Download the installer from 
[https://downloads.openquake.org/pkgs/windows/oq-engine/](https://downloads.openquake.org/pkgs/windows/oq-engine/)
Double-click on the installer to start the installation.  You will probably be 
presented with a popup message similar to the one shown below:

<figure>
	<img src="_images/01_Windows_warning.png" 
		 width="50%" align="centre" alt="Windows popup"/>
	<figcaption>"Windows Protected your PC"popup</figcaption>
</figure>

Click on the “More info” link inside the popup:

<figure>
	<img src="_images/02_Run_anyway.png" alt="Run Anyway"
	 width="50%" align="centre" />
	<figcaption>Run Anyway</figcaption>
</figure>

Check that the App string starts with “OpenQuake_Engine_” and ends with the 
desired version number, if all is in order, click on the “Run anyway” button 
to continue.  You will be presented with an installer dialog similar to the 
one depicted below:

<figure>
	<img src="_images/03_Installer_start.png" alt="Installer Start"
	     width="50%" align="centre" />
	<figcaption>Installer Start</figcaption>
</figure>

Press the "Next" button.  

The AGPL v3 license terms will be displayed - you must accept these terms in 
order to install the OpenQuake engine:

<figure>
	<img src="_images/04_License.png" 
		 width="50%" align="centre" />
	<figcaption>License Terms</figcaption>
</figure>
Press the "I Agree" button.

### Uninstall Previously installed versions

If you have already installed a version of the OpenQuake Engine via the 
Windows installer, you will be presented with a message similar to the one 
depicted below:

<figure>
	<img src="_images/05_Uninstall.png" width="50%" align="centre" />
	<figcaption>Already installed</figcaption>
</figure>

> :warning: **IMPORTANT** even if you have installed the OpenQuake engine via 
> the universal installer, git or some other means, you must ensure that no 
> OpenQuake engine processes are running, that you do not have the User Manual 
> PDF or demo files open before proceeding.   If any OpenQuake processes are 
> running or files are open, the installation may not complete successfully.

If you do not have a previous installation of the OpenQuake Engine installed, 
you can skip ahead to 
[Install OpenQuake Engine Components](#install-components)

Press Next to continue, you will be presented with a reminder message:

<figure>
	<img src="_images/06_Stop_Processes.png" width="50%" align="centre" />
	<figcaption>Stop processes</figcaption>
</figure>

Once you have stopped any running OpenQuake Engine processes and closed all 
associated files, press OK to continue.  The uninstaller will now remove the 
previous OpenQuake engine installation, this may take some time to complete:

<figure>
	<img src="_images/07_Uninstalling.png" width="50%" align="centre" />
	<figcaption>Uninstaller running</figcaption>
</figure>

Once finished, the uninstaller will look like this:
<figure>
	<img src="_images/08_Uninstall_Complete.png" 
		 width="50%" align="centre" />
	<figcaption>Uninstaller completed</figcaption>
</figure>

Press the “Close” button to close the uninstaller.


### Install OpenQuake Engine Components {#install-components}

We are now ready to install the OpenQuake engine components:

<figure>
	<img src="_images/09_Installer_Components.png" 
		 width="50%" align="centre" />
	<figcaption>OpenQuake Engine components</figcaption>
</figure>

Press the “Next” button to continue

It will now be possible to view and if necessary change the installation
location of the OpenQuake Engine.  We recommend using the default value unless
you have a compelling reason to use something else - please note that changing
the installation location may make it more difficult to provide support.

<figure>
	<img src="_images/10_Install_Location.png" 
		 width="50%" align="centre" />
	<figcaption>Installation location</figcaption>
</figure>

Press the “Install” button to continue.

The installer will now execute, this may take some time to complete.

<figure>
	<img src="_images/11_Installing.png" 
         width="50%" align="centre" />
	<figcaption>Installer running</figcaption>
</figure>

Once the installer has completed, it will look something like this:

<figure>
	<img src="_images/12_Complete.png" 
         width="50%" align="centre" />
	<figcaption>OpenQuake Engine installer completed</figcaption>
</figure>

Press Finish to close the installer.  You should now see two OpenQuake Engine
icons on your Windows desktop:

<figure>
	<img src="_images/13_Desktop_Icons.png" 
         width="10%" align="centre" />
	<figcaption>OpenQuake Engine Icons</figcaption>
</figure>

It should also be possible find the OpenQuake Engine by pressing the Windows
key and typing “OpenQuake”:

<figure>
	<img src="_images/14_Win11_Start_menu.png" 
         width="50%" align="centre" />
	<figcaption>OpenQuake Engine App in the Windows Start Menu</figcaption>
</figure>

Double-click the webui icon to start the OpenQuake Engine web user-interface.
The first time the OpenQuake engine is executed, the initialization process 
may take several minutes to complete:

<figure>
	<img src="_images/15_Starting_webui_wait.png" 
         width="50%" align="centre" />
	<figcaption>OpenQuake Engine webui starting</figcaption>
</figure>

Once the webui is ready for use, a web browser tab will be opened:

<figure>
	<img src="_images/16_webui_up.png" 
		 width="50%" align="centre" />
	<figcaption>OpenQuake engine web user-interface</figcaption>
</figure>

Please refer to the 
[Web user-interface instructions](../running-calculations/web-ui.html)
for more information about using the web-ui.

## Getting help
If you need help or have questions/comments/feedback for us, please
subscribe to the 
[OpenQuake users mailing list](https://groups.google.com/g/openquake-users)
