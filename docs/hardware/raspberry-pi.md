# Setup Board Computer

This section looks at how we are able to connect our board computer, in our case a Raspberry Pi Zero 2 WH, to our flight controller. First off, there are multiple possibilities to set up a board computer to work with a flight controller. For example there are prebuild operating systems we could install, like [BlueOS](https://blueos.cloud/docs/latest/usage/installation/), [Rpanion-Server](https://www.docs.rpanion.com/software/rpanion-server) or [APSync](https://firmware.ardupilot.org/Companion/apsync/) and multiple programms that allow us to use the MAVLink protocol, such as [MAVProxy](https://ardupilot.org/mavproxy/docs/getting_started/download_and_installation.html#mavproxy-downloadinstalllinux), [DroneKit](https://github.com/dronekit/dronekit-python/), [MAVSDK](https://github.com/ArduPilot/ardupilot-mavsdk) or [mavlink-router](https://github.com/mavlink-router/mavlink-router). As we are constrained in using a Raspberry Pi Zero, we will use the lightweight mavlink-router for our project. An overview about the most common ways to use a Raspberry Pi with ardupilot can be found under https://ardupilot.org/dev/docs/raspberry-pi-via-mavlink.html.

## Configure serial port on pi
We have to set up our Pi to allow the use of the serial ports we need, as the Raspberry Pi Linux uses the hardware serial pins GPIO 14 and GPIO 15 for a Linux console login shell, which blocks mavlink-router from reading the pins. To do that we use the command
```
sudo raspi-config
```
This will open the following window, where we will navigate to Interface Options 

and then to Serial Port.

It will ask: "Would you like a login shell to be accessible over serial?", where we will select No
and it ask: "Would you like the serial port hardware to be enabled?" directly after, where we will have to select Yes.

We save our changes, exit and reboot the Pi, which allows us to use the hardware serial pins for our MAVLink protocol.

## Setup the flight controller
While we already set the needed options in the setup section of our drone, we will repeat the needed settings for our flight controller to be able to work with our board computer. 
We need to set the following parameters, do note that for our setup we need to set the options for serial port 4, this might be different for other configurations:
- `SERIAL4_PROTOCOL` = 2  to enable MAVLink 2 on the serial port.
- `SERIAL4_BAUD` = 921 to set the 921600 baud rate.
- `LOG_BACKEND_TYPE` = 3 We only need this option if we want to save logs onto our Raspberry Pi.
## Install MAVLink-router
MAVLink(Micro Air Vehicle Link) is the standard communication protocol used by autopilots to talk to ground control software and companion computers, like our Raspberry Pi.
We need a program that listens for MAVLink traffic on one port and forwards it to others. We use `mavlink-router` for this: https://github.com/mavlink-router/mavlink-router

The packages that we need to install mavlink router are
```
sudo apt install git meson ninja-build pkg-config gcc g++ systemd
```
If we have all packages installed we can download mavlink-router,
```
git clone --recurse-submodules https://github.com/mavlink-router/mavlink-router.git
```
run the meson build inside our downloaded folder
```
cd mavlink-router
meson setup build .
```
and compile and install the files:
```
sudo ninja -C build
sudo ninja -C build instal
```
After we installed everything, we will create the config file we will need.
```
sudo mkdir /etc/mavlink-router
sudo nano /etc/mavlink-router/main.conf
```
To see an example of the config file we can look at the official github page https://github.com/mavlink-router/mavlink-router/blob/master/examples/config.sample where we can see all possible options. For now we will only look at the basic options we will need for communication via MAVLink to our flight controller, but it also allows for options that allow us to easily log data from our flight controller, if we wish to save the logs on our board computer. The File should contain the :
```
[General]
# Basic configuration
ReportStats=false
MavlinkVersion=2.0

[UartEndpoint flightcontroller]
# Connects to FC via GPIO hardware serial pins
Device = /dev/serial0
Baud = 921600

[UdpEndpoint local_script]
# Routes data to port 14550 for Python scripts running on the Pi
Mode = normal
Address = 127.0.0.1
Port = 14550

[UdpEndpoint ground_station]
# OPTIONAL: Routes data over Wi-Fi to a Ground Control Station (GCS)
# Replace with your laptop's actual IP address on the network
Mode = Normal
Address = 192.168.1.50
Port = 14550
```

