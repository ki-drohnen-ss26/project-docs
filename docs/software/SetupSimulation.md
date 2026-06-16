# Setup Simulation for a drone

Here we will set up a simulation to simulate a drone that we can in turn send mavlink commands to control, 
based on the ardupilot documentation: https://ardupilot.org/dev/docs/simulation-2.html

We will install a Software in the loop(SITL) programm that runs the ArdiPilot firmware and sends the servo and motor outputs to the simulation, and the simulator Gazebo that receives the inputs from the SITL, uses them to move a simulated drone on a screen, and sends back the vehicle position, velocities and other data back to the firmware simulation, basically simulating real world sensors.

## Install WSL
Gazebo only runs under Linux and Mac distributions which is why we first install Windows subsystem for Linux(WSL), that allows us to run a Linux environment on our Windows machine. Guides for the installation and basic commands can be found under https://learn.microsoft.com/en-us/windows/wsl/basic-commands.

First we install Ubuntu-24.04 as our linux distribution using the command:
```
wsl --install -d Ubuntu-24.04
```
In case we want another distribution, we can see all available distributions under
```
wsl --list --online
```
and install any available distribution by adding the `-d` option to our install command. Already installed subsystems can be checked using the command
```
wsl --list --verbose
```
that also shows the WSL version version:

<img width="381" height="56" alt="image" src="https://github.com/user-attachments/assets/2a75edbd-ec0c-43f2-bcb0-354a8798f669" />

For our use case we need WSL version 2, as we need graphics. In case the version is 1, we can change the WSL version using
```
wsl --set-version <distribution name> <versionNumber>
```
Just using the `wsl` command will run the default Linux distribution, to set the default distribution we use the command
```
wsl --set-default <Distribution Name>
```
In case we want to run a distribution other than our default version, we can run
```
wsl --distribution <Distribution Name> --user <User Name>
```
After we set up WSL for our windows computer, we can install the SITL and the Gazebo simulation.

## Install Software in the loop (SITL)
To install and run the SITL we first clone the ardupilot git repository
```
git clone --recursive https://github.com/ArduPilot/ardupilot.git
```
and run the auto installer:
```
ardupilot/Tools/environment_install/install-prereqs-ubuntu.sh -y
```
For the changes to take effect we reload the provile using 
```
source ~/.bashrc
```
Now we can run our software using
```
ardupilot/Tools/autotest/sim_vehicle.py -v ArduCopter --map --console
```
The option `-v` sets the vehicle type, as we want to simulate a quadcopter, we set it to ArduCopter, but there can be many different vehicle types. like ArduPlane or Rover, and it is a needed option to run the SITL. The main command opens up the command line client that allows us to run commands through our SITL.

<img width="939" height="520" alt="image" src="https://github.com/user-attachments/assets/4140e002-e35f-44bb-9d1d-b90c8492f0f6" />

It will also open the SITL elf execution window, that outputs raw flight controller logs and debug data directly from the simulated hardware.
<img width="810" height="517" alt="image" src="https://github.com/user-attachments/assets/61dbe98c-3634-4d43-9644-bb3388b38129" />
Do not close theís window, as this is the simulated flight controller and without it everything else will crash.

The `--map` option opens a 2D map that shows our drone

<img width="747" height="604" alt="image" src="https://github.com/user-attachments/assets/1972f866-1733-4a63-b44c-12f572ce23eb" />

and the `--console` command opens a status terminal for messages

<img width="746" height="248" alt="image" src="https://github.com/user-attachments/assets/c386103e-defb-4a6e-b3a1-d893cd2dd20d" />

We can also connect our Mission planner with the simulated flight controller. Normally the mission planner connects automatically if the SITL is already running, else we will have to look after the UDP connection:

<img width="325" height="50" alt="image" src="https://github.com/user-attachments/assets/de0b0c99-ae7e-4e43-961a-871211ba9356" />

Now that we have started our application, we can look at some commands to see if everything works as intended.
First we will change into guided mode using the command
```
mode guided
```
then we can arm the throne using, take note that the drone will automatically disarm after 15 seconds,
```
arm throttle
```
and lastly we can the takeoff command
```
takeoff 40
```
that will increase the drones altitude by 40 meters, which we can confirm using the console, where we will see the Alt parameter being 40. 

<img width="905" height="163" alt="image" src="https://github.com/user-attachments/assets/c6fbb28c-8042-4d7d-9949-a187b53278f5" />

If we have the mission planner connected, we can also see the same in the mission planner data.

<img width="590" height="459" alt="image" src="https://github.com/user-attachments/assets/921dd91d-1571-4e78-b783-3c61b3f0618c" />

Further commands to try are setting the throttle to 1500 PWM
```
rc 3 1500
```
set the circle mode that makes the drone spin in a radius
```
mode circle
```
and change the parameter for the radius to 20 m:
```
param set CIRCLE_RADIUS_M 20
```

We can look at the mission planner how our drone behaves, we see the drone is tilted and on the map we can see how it circles.

<img width="1919" height="1028" alt="image" src="https://github.com/user-attachments/assets/fe1cf58e-eb23-4556-9e66-253253fc6996" />

If everything works as intended, we have succesfully set up the system in the loop and can now install the Gazebo simulation that lets us simulate a drone in three dimensions.
Sources for the installation and use of SITL:
- https://ardupilot.org/dev/docs/sitl-on-windows-wsl.html
- https://ardupilot.org/dev/docs/using-sitl-for-ardupilot-testing.html#using-sitl-for-ardupilot-testing

## Install Gazebo
To install Gazebo we use the tutorial by ardupilot under https://ardupilot.org/dev/docs/sitl-with-gazebo.html.

For the installation we first make sure all packages are up to date and install the needed packages
```
sudo apt-get update
sudo apt-get install lsb-release gnupg
sudo apt-get install rapidjson-dev -y
sudo apt-get install libopencv-dev -y
sudo apt-get install libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev -y
```
Then we get the Gazebo GPG key,
```
sudo wget https://packages.osrfoundation.org/gazebo.gpg -O /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
```
add the Gazebo repository to our souce list

```
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null
```
and install gazebo harmonic:
```
sudo apt-get update
sudo apt-get install gz-harmonic -y
```
Right after installing gazebo we clone the ardupilot gazebo repository
```
git clone https://github.com/ArduPilot/ardupilot_gazebo
```
Inside the downloaded ardupilot_gazebo folder we will create a build folder, navigate into it and build the plugin.
```
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=RelWithDebInfo
make -j$(nproc)
```
After we set everything up, we add to our `.bashrc` the environment variables that Gazebo uses to locate plugins and models at runtime. Open .bashrc
```
nano ~/.bashrc
```
and paste in the following lines:
```
export GZ_SIM_SYSTEM_PLUGIN_PATH=$HOME/ardupilot_gazebo/build:$GZ_SIM_SYSTEM_PLUGIN_PATH 
export GZ_SIM_RESOURCE_PATH=$HOME/ardupilot_gazebo/models:$HOME/ardupilot_gazebo/worlds:$GZ_SIM_RESOURCE_PATH
```
After the changes we need to refresh our `.bashrc`
```
source ~/.bashrc
```

Now we have set everything we needed up and can run gazebo along our SITL. We use one terminal to run
```
gz sim -v4 -r iris_runway.sdf
```

and a second to run
```
~/ardupilot/ArduCopter/Tools/autotest/sim_vehicle.py -v ArduCopter -f gazebo-iris --model JSON --map --console
```
where the `-f` option tells the arducopter simulation to look for a gazebo physics mode and `--model JSON` tells it to use the JSON communication protocol.

<img width="1917" height="1025" alt="image" src="https://github.com/user-attachments/assets/4b54c330-abac-459c-a98f-2e68a3007268" />


At first we will not be able to arm the drone, as the frame class and type seem to not be set, so we use the following commands in the MAVProxy command line:

```
param set FRAME_CLASS 1
param set FRAME_TYPE 1
```
Now we can use the same commands used to try the SITL and see if the drone moves as expected.
Sometimes the acceleration might be inconsistent, if that is the case we can use the command 
```
accelcal
```
and once it asks us to place the vehicle level, we once again just type `accelcal`.

It is also possible to add simulated peripherals, see https://ardupilot.org/dev/docs/adding_simulated_devices.html.
