# Setup Board Computer

This section looks at how we are able to connect our board computer, in our case a Raspberry Pi Zero 2 WH, to our flight controller. First off, there are multiple possibilities to set up a board computer to work with a flight controller. For example there are prebuild operating systems we could install, like [BlueOS](https://blueos.cloud/docs/latest/usage/installation/), [Rpanion-Server](https://www.docs.rpanion.com/software/rpanion-server) or [APSync](https://firmware.ardupilot.org/Companion/apsync/) and multiple programms that allow us to use the MAVLink protocol, such as [MAVProxy](https://ardupilot.org/mavproxy/docs/getting_started/download_and_installation.html#mavproxy-downloadinstalllinux), [DroneKit](https://github.com/dronekit/dronekit-python/), [MAVSDK](https://github.com/ArduPilot/ardupilot-mavsdk) or [mavlink-router](https://github.com/mavlink-router/mavlink-router). As we are constrained in using a Raspberry Pi Zero, we will use the lightweight mavlink-router for our project. An overview about the most common ways to use a Raspberry Pi with ardupilot can be found under https://ardupilot.org/dev/docs/raspberry-pi-via-mavlink.html.

## Configure serial port on pi
We have to set up our Pi to allow the use of the serial ports we need, as the Raspberry Pi Linux uses the hardware serial pins GPIO 14 and GPIO 15 for a Linux console login shell, which blocks mavlink-router from reading the pins. To do that we use the command
```
sudo raspi-config
```
This will open the following window, where we will navigate to Interface Options 
<img width="1102" height="615" alt="image" src="https://github.com/user-attachments/assets/d1fe3319-5315-4ec0-86a4-ace3cb44eaa8" />

and then to Serial Port.
<img width="1106" height="615" alt="image" src="https://github.com/user-attachments/assets/3c0d0a54-bfd4-4ecb-abff-71fe94361b73" />

It will ask: "Would you like a login shell to be accessible over serial?", where we will select No
<img width="543" height="383" alt="image" src="https://github.com/user-attachments/assets/eeca7140-e8c5-43c1-8bf7-e7c3b3e460b0" />

and it ask: "Would you like the serial port hardware to be enabled?" directly after, where we will have to select Yes.

<img width="543" height="386" alt="image" src="https://github.com/user-attachments/assets/5bca581f-7987-42b1-8e14-43bbebd87ba2" />

We save our changes, exit and reboot the Pi, which allows us to use the hardware serial pins for our MAVLink protocol.

## Setup the flight controller
While we already set the needed options in the setup section of our drone, we will repeat the needed settings for our flight controller to be able to work with our board computer. 
We need to set the following parameters, do note that for our setup we need to set the options for serial port 4, this might be different for other configurations:
- `SERIAL4_PROTOCOL` = 2  to enable MAVLink 2 on the serial port.
- `SERIAL4_BAUD` = 921 to set the 921600 baud rate.
- `LOG_BACKEND_TYPE` = 3 We only need this option if we want to save logs onto our Raspberry Pi.

## Connect the flight controller with the board computer
To connect the flight controller and the board computer, we have to connect the Raspberry Pi's TX pin (GPIO 14/Pin 8) to the RX pin of the flight controllers, the RX pin (GPIO 15/Pin 10) of the Pi to the TX pin of the flight controller and make sure they have common ground by plugging setting the ground of the flight controller to the ground of the Pi. Make sure that you are only ever power the Pi using either the drones battery, or the usb-c port, as using both might damage the board. The GPIO serial port is called `/dev/serial0` on our Pi.
<img width="2064" height="1185" alt="image" src="https://github.com/user-attachments/assets/1521c14e-dfba-4fbf-9ba0-d6705322b6e0" />

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
To see an example of the config file we can look at the official github page https://github.com/mavlink-router/mavlink-router/blob/master/examples/config.sample where we can see all possible options. For now we will only look at the basic options we will need for communication via MAVLink to our flight controller, but it also allows for options that allow us to easily log data from our flight controller, if we wish to save the logs on our board computer. The File should contain the following:
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
We also want to create a systemd service that starts our mavlink-router at startup, so we create a service file in systemd
```
sudo nano /etc/systemd/system/mavlink-router.service
```
with the following content
```
[Unit]
Description=MAVLink Router Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/mavlink-routerd -c /etc/mavlink-router/main.conf
Restart=on-failure
User=root

[Install]
WantedBy=multi-user.target
```
and enable and start the service
```
sudo systemctl daemon-reload
sudo systemctl enable mavlink-router
sudo systemctl start mavlink-router
```

To see if the service is running we can use 
```
sudo systemctl status mavlink-router
```
Once mavlink-router is up and running, we can directly listen to the serial port to see if packets are arriving
```
sudo stty -F /dev/serial0 921600 raw
sudo cat /dev/serial0
```
We will see seemingly random characters scrolling on the screen, which tells us that the flight controller is actively broadcasting
<img width="613" height="45" alt="image" src="https://github.com/user-attachments/assets/38171ba0-e6b7-4aa6-9833-1a37c8fbd11d" />


## Pymavlink
[Pymavlink](https://github.com/ArduPilot/pymavlink) is a Python implementation of the MAVLink protocol, that we will use to send MAVLink commands to our flight controller.
First we need to install some packages:
```
sudo apt-get install libxml2-dev libxslt-dev
sudo python3 -m pip install --upgrade lxml
```
and we can install Pymavlink using:
```
sudo python3 -m pip install --upgrade pymavlink
```
Now we will have two example codes where we once receive data, namely the altitude, global position and airspeed, from the drone, that we will print in our console.
```
import time
from pymavlink import mavutil

# Connect
connection = mavutil.mavlink_connection('udpin:127.0.0.1:14550')

# Wait for the initial heartbeat
print("Waiting for heartbeat...")
connection.wait_heartbeat()
print(f"Connected to System {connection.target_system} Component {connection.target_component}")

# Request Data Streams
connection.mav.request_data_stream_send(
    connection.target_system,
    connection.target_component,
    mavutil.mavlink.MAV_DATA_STREAM_ALL,
    4, # 4 Hz
    1
)

# Read incoming data loop
last_heartbeat_sent = 0

try:
    while True:
        # Periodically send a heartbeat back to flight controller (1 second) 
        # to let ArduPilot know the script is still active
        if time.time() - last_heartbeat_sent > 1.0:
            connection.mav.heartbeat_send(
                mavutil.mavlink.MAV_TYPE_GCS,       # Tell FC you are acting as a GCS/Companion
                mavutil.mavlink.MAV_AUTOPILOT_INVALID,
                0, 0, 0
            )
            last_heartbeat_sent = time.time()

        # Try to receive a single message
        msg = connection.recv_match(blocking=True, timeout=0.1)

        if msg is None:
            continue

        # Filter and look for the specific data types
        msg_type = msg.get_type()

        if msg_type == 'ATTITUDE':
            print(f"Attitude -> Roll: {msg.roll:.2f}, Pitch: {msg.pitch:.2f}, Yaw: {msg.yaw:.2f}")

        elif msg_type == 'GLOBAL_POSITION_INT':
            print(f"GPS -> Lat: {msg.lat / 1.0e7}, Lon: {msg.lon / 1.0e7}, Alt: {msg.alt / 1000.0}m")

        elif msg_type == 'VFR_HUD':
            print(f"HUD -> Airspeed: {msg.airspeed} m/s, Throttle: {msg.throttle}%")

except KeyboardInterrupt:
    print("Script stopped by user.")
```
<img width="496" height="174" alt="image" src="https://github.com/user-attachments/assets/813d08b1-e0c5-4610-9f9d-3fd475423cbe" />

The next example we send a MAVLink packet to the drone that will change the mode of the drone
```
import time
from pymavlink import mavutil

# Connect via udpin
connection = mavutil.mavlink_connection('udpin:127.0.0.1:14550')

print("Waiting for heartbeat...")
connection.wait_heartbeat()
print(f"Connected to System {connection.target_system}")

target_sys = connection.target_system
target_comp = connection.target_component

# Target mode string
chosen_mode = 'STABILIZE'

if chosen_mode not in connection.mode_mapping():
    print(f"Error: Mode '{chosen_mode}' is not recognized.")
    exit(1)

mode_id = connection.mode_mapping()[chosen_mode]
print(f"Resolved mode '{chosen_mode}' to numeric ID: {mode_id}")

# Send an outbound heartbeat to establish a clear return path for ACKs
connection.mav.heartbeat_send(
    mavutil.mavlink.MAV_TYPE_GCS,
    mavutil.mavlink.MAV_AUTOPILOT_INVALID,
    0, 0, 0
)

# Clear out any backlogged text or messages sitting in the buffer
print("Draining queue...")
while connection.recv_match(blocking=False):
    pass

# Send mode change command using the long-form format
print(f"Sending MAV_CMD_DO_SET_MODE for mode ID {mode_id}...")
connection.mav.command_long_send(
    target_sys,
    target_comp,
    mavutil.mavlink.MAV_CMD_DO_SET_MODE,
    0,                                         # Confirmation index
    mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, # Param 1: Custom mode flag
    mode_id,                                   # Param 2: The actual mode numeric ID
    0, 0, 0, 0, 0                              # Params 3-7: Unused
)

# Listen specifically for the confirmation packet
print("Listening for COMMAND_ACK...")
timeout = time.time() + 3.0
ack_received = False

while time.time() < timeout:
    # Look for ANY command acknowledgment
    msg = connection.recv_match(type='COMMAND_ACK', blocking=True, timeout=0.1)
    if msg:
        print(f"Received ACK for Command {msg.command}. Result code: {msg.result}")
        if msg.command == mavutil.mavlink.MAV_CMD_DO_SET_MODE:
            if msg.result == 0:
                print("Success! Mode change confirmed by flight controller.")
            else:
                print(f"Rejected! Code {msg.result}")
            ack_received = True
            break

if not ack_received:
    print("No ACK received. Checking current vehicle status instead...")
    # Request a fresh heartbeat to verify if the mode actually changed anyway
    msg = connection.recv_match(type='HEARTBEAT', blocking=True, timeout=2.0)
    if msg:
        # Inverse lookup to find the text name of the custom mode currently running
        current_modes = [k for k, v in connection.mode_mapping().items() if v == msg.custom_mode]
        print(f"Current live vehicle mode is: {current_modes}")
```
We can use the Mission Planner to check the changes in the mode. For a list of commands look at https://ardupilot.org/dev/docs/mavlink-commands.html.
