# MTF-01P Configuration

First we need to use MicoAssistant to set the output protocol as "mav-apm", namely the MavLink protocol. 

Since we are using UART5 as the communication port for optical flow, we need to set up the following parameters in Ardupilot Mission Planner:

- SERIAL5_BAUD 115
- SERIAL5_OPTIONS 1024
- SERIAL5_PROTOCOL 1
- FLOW_TYPE 5
- RNGFND1_TYPE 10

After that, we need to refresh the paremeters in the Mission Planner and set up the following parameters:

- RNGFND1_MAX_CM 800
- RNGFND1_MIN_CM 1
- RNGFND1_ORIENT 25

Next, we need to set up the EKF fusion. Since GPS navigation is not introduced in this project, we only need to change the EK3_SRC1 data:

- AHRS_EKF_TYPE 3
- EK3_SRC_OPTIONS 0
- EK3_SRC1_POSXY 0
- EK3_SRC1_POSZ 2
- EK3_SRC1_VELXY 5
- EK3_SRC1_VELZ 0
- EK3_SRC1_YAW 1

The final step is to place the sensor properly on the frame. We use hot melt glue to stick it on the front half of the underside of the frame.