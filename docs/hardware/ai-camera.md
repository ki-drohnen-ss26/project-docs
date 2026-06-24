# Raspberry Pi AI Camera Module

## Connect the camera
To connect the camera to our Raspberry Pi unit, we will first have to power it off. Then we have to locate the camera connector. On the Pi zero, that we are using in this project, the camera connector is located on the short edge opposite the SD card tray. On a Raspberry Pi 4, there is the connector close to the USB ports, that is labeled as CAMERA and if we are using a Raspberry 5, we can use any port, as they are dual use for cameras and displays.

To connect the camera to our connector, we have to open the flap on the connector and insert the end of the cable with its contacts facing away from the flap. Make sure the cable is sitting safe in the connector and close the connector flap, where it should click. With these steps you have succesfully connected the camera to the Raspberry Pi.

Source: https://www.raspberrypi.com/documentation/accessories/camera.html#install-a-raspberry-pi-camera

## Setup the AI camera
For our AI camera to work on the Raspberry Pi we have to install the correct IMX500 firmware, which we can install using the following commands:
First we update the current software of our Raspberry using the command
```
sudo apt update && sudo apt full-upgrade
```
and afterwards we can install the firmware:
```
sudo apt install imx500-all
```
This installs the  `/lib/firmware/imx500_loader.fpk` and `/lib/firmware/imx500_firmware.fpk` files that are needed to run the IMX500 sensor, sets some neural netowrk model firmware files into `/usr/share/imx500-models/`, installs IMX500 post-processing software stages in rpicam-apps and installs the needed SOny network model packaging tools.

After we have installed all needed we reboot the Raspberry Pi and we can use the command 
```
rpicam-hello --list-cameras
```
to see all available cameras, where it should list our camera: 
<img width="677" height="107" alt="image" src="https://github.com/user-attachments/assets/2e56d2f6-fe67-481f-8605-d08e9484bf9d" />

To see if the camera is working, we can use the command
```
rpicam-hello -t 0
```
that will show the camera feed inside a window, if we want to start the window inside an ssh session, we have to manually send the window to the local monitor using:
```
DISPLAY=:0 rpicam-hello -t 0
```

The Raspberry Pi AI camera integrates fully with libcamera, rpicam-apps and Picamera 2.
We can run an object detection example using rpicam-apps with the following command:
```
rpicam-hello -t 0s --post-process-file /usr/share/rpi-camera-assets/imx500_mobilenet_ssd.json --viewfinder-width 1920 --viewfinder-height 1080 --framerate 30
```
For scripting and working with the data of the camera, Picamera2 seems to be the best choice.

Source: https://www.raspberrypi.com/documentation/accessories/ai-camera.html
