# MAVlink
[MAVLink](https://mavlink.io/en/) is a serial protocol that defines a large set of message and is used to send data and commands between two devices, in our case a drone and either the ground control station or the companion computer. For this section we rely on the information given by [Ardupilot MAVLink](https://ardupilot.org/dev/docs/mavlink-commands.html), as well as official [MAVLink Website](https://mavlink.io/en/) and the official [PyMAVLink Github](https://github.com/ArduPilot/pymavlink?tab=readme-ov-file).

One of the big advatages of the MAVLink protocol is, that the messages can be sent using almost any serial connection, without depending on its underlying technology. They can be sent over serial connection, WiFi, radio or many other technologies.

The [packet format](https://mavlink.io/en/guide/serialization.html) of the MAVLink2 protocol is given as

![MAVLink_PacketFormat.png](../Images/MAVLink/MAVLink_PacketFormat.png)

and we will take a closer look at how the MAVLink messages are constructed.

| Byte Index   | Content                | Explanation                                                                                                                                                                                                                                        |
|--------------|------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 0            | Packet start marker    | The first bit in our message defines the beginning of a new packet. It specifies the used protocol, for MAVLink2 it woud be 0xFD, for MAVLink1 0xFE. If the target system does not know the given protocol byte, the whole packet will be skipped. |
| 1            | Payload length         | This byte defines the length of the payload and can be between 0 and 255.                                                                                                                                                                          |
| 2            | Incompatibility Flags  | The incompatibility flag indicates which features the MAVLink library has to support to be able to handle the packet. If the system does not understand the flag, the whole package is discarded                                                   |
| 3            | Compatibility Flags    | The compatibility flags indicate features that are not needed to process the package. The system can ignore the flag in case it does not understand it.                                                                                            |
| 4            | Packet sequence number | This byte signifies the packet sequence. Each sent packet increases the value and can be used to identify package loss.                                                                                                                            |
| 5            | System ID              | This byte defines the system ID of the device that is sending the message and can be used to differentiate different devices on the same network. can take values between 1 and 255. The broadcast address 0 cannot be used.                       |
| 6            | Component ID           | The component ID is used to differentiate different components inside a system that are sending the message. For example one component could be the autopilot, another the camera. While they share a system ID, they differ in the component ID.  |
| 7 to 9       | Message ID             | The Message ID defines the type of message that is send and allows the receiver to decode the data into the correct message object.                                                                                                                |
| 9 + n        | Payload                | The Message data. Can be up to n=255 Bytes.                                                                                                                                                                                                        |
| n+10 to n+11 | Checksum               | A CRC-16/MCRF4XX checksum used to verify that the message is not corrupted.                                                                                                                                                                        |
| n+12 to n+24 | Optional Signature     | A signature that ensures the link is tamper-proof.                                                                                                                                                                                                 |

Because we are using the MAVLink2 protocol, we want to only briefly take a look at MAVLink1. The packet format of MAVLink 2 is a expansion of MAVLink1, that introduced the incompatibility and compatibility flags and signature, and increased the size of the Message ID and the Payload. MAVLink2 is backwards compatible and understands each MAVLink1 message. MAVLink1 on the other hand can only see the original fields, without the added MAVLink2 functionality, meaning messages could be read, but it might lead to problems if MAVLink2 features are used.

The [High Level Message Flow](https://ardupilot.org/dev/docs/mavlink-basics.html), the image directly from Ardupilot, shows us how the communication between two devices work:

![MAVLink_MessageFlow.png](../Images/MAVLink/MAVLink_MessageFlow.png)

Here we see the communication between a Ground control station and a drone, but the same holds true for any two devices that communicate using the MAVLink protocol.

After a connection is opened, the systems send a HEARTBEAT message at a frequency of 1Hz, meaning one message each second, to each other to show that the other system is present and able to respond.

Then the ground control station or board computer, can request data and the rate at which the data should be sent, and the drone in return send the data back.

The ground control station can also send commands, which is what we are mostly interested in for the autonomous flight, where the drone send an acknowledgement back, that the command was received.

## MAVLink commands
In this section we will look at some MAVLink messages that are needed for our autonomous flight, but it is only a small subset of all possible Messages, which we can find under [Ardupilot MAVLink Messages](https://ardupilot.org/copter/docs/ArduCopter_MAVLink_Messages.html#arducopter-mavlink-messages).

### Heartbeat
The first message we will look at is the Hearbeat, where we will show how the full serialized message looks like, in further we will only concentrate on the important points, mainly the payloads.

The Heartbeat is defined in the [MAVLink Minimal Message Set](https://mavlink.io/en/messages/minimal.html#HEARTBEAT), that contains the minimal set of definitions needed for a viable MAVLink system, and is also included in the [Commons Set](https://mavlink.io/en/messages/common.html#HEARTBEAT), that includes standard definitions managed by the MAVLink project.

The message ID for the Heartbeat is defined as 0, and the payload contains the following information:

| Field Name      | Type       | Values                                                                    | Description                                                                                                                                                                                                                                                                          |
|-----------------|------------|---------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| type            | `uint8_t`  | [MAV_TYPE](https://mavlink.io/en/messages/common.html#MAV_TYPE)           | The first byte inside the payload defines the type of vehicle we use or the type of the component used. The linked [MAV_TYPE](https://mavlink.io/en/messages/common.html#MAV_TYPE) has the types and corresponding integer values liste. For example the quadcoptor has the value 2. |
| autopilot       | `uint8_t`  | [MAV_AUTOPILOT](https://mavlink.io/en/messages/common.html#MAV_AUTOPILOT) | This defines the autpilot class, for example it could be a form of ardupilot or PX4                                                                                                                                                                                                  |
| base_mode       | `uint8_t`  | [MAV_MODE_FLAG](https://mavlink.io/en/messages/common.html#MAV_MODE_FLAG) | This is a bitmask that encodes the MAV mode, it shows for example, that the vehicle has Stabilize mode or Guided mode enabled.                                                                                                                                                       |
| custom_mode     | `uint32_t` |                                                                           | These four byte are used for flags that are specific to the given autopilot                                                                                                                                                                                                          |
| system status   | `uint8_t`  | [MAV_STATE](https://mavlink.io/en/messages/common.html#MAV_STATE)         | This byte contains the system status flag and shows the current status, for example if the system is currently booting, or if it is calibrating, etc.                                                                                                                                |
| mavlink_version | `uint8_t`   |                                                                           | This byte is not wrieable by users,but gets added by the protocol and denotes the version.                                                                                                                                                                                           |

Now we can look at an actual example, where we have the following values:

| Field Name      | Example Value                                       |
|-----------------|-----------------------------------------------------|
| type            | MAV_TYPE_QUADROTOR (02)                             |
| autopilot       | MAV_AUTOPILOT_ARDUPILOTMEGA (03)                    |
| base_mode       | custom mode enabled + stabilize + manual input (51) |
| custom_mode     | Arducopter LOITER (05 00 00 00)                     |
| system_status   | MAV_STATE_STANDBY (03)                              |
| mavlink_version | 03                                                  |

These make up our payload, but the field reordering sorts by native size, where the largest is the first, meaning the custom_mode, that has 4 bytes, is set at the beginning, resulting in our payload:
```payload: 05 00 00 00 02 03 51 03 03```

The full MAVLink2 looks like this:

```FD 09 00 00 2A 01 01 00 00 00 05 00 00 00 02 03 51 03 03 AD 01```

Looking at each entry:

| Content               | Value                      | Note                                                                                       |
|-----------------------|----------------------------|--------------------------------------------------------------------------------------------|
| Start marker          | FD                         | Denotes MAVLink2                                                                           |
| Payload length        | 09                         | Payload has 9 bytes                                                                        |
| Incompatibility Flags | 00                         | No Incompatibility Flags                                                                   |
| Compatibility Flags   | 00                         | No Compatibility Flags                                                                     |
| Packet Sequence       | 2A                         | 42nd Message                                                                               |
| System ID             | 01                         | Generally ID 1 is used for the drone                                                       |
| Component ID          | 01                         | Component ID 1 is mostly used for the autopilot                                            |
| Message ID            | 00 00 00                   | The Message ID of the HEARTBEAT is 0. Do note that this fields byte-order is little endian |
| Payload               | 05 00 00 00 02 03 51 03 03 |                                                                                            |
| Checksum              | AD 01                      | CRC-16/MCRF4XX                                                                             |
| Signature             | -                          | Optional Signature was omitted                                                             |

With that we have created our first MAVLink message. As we have seen how MAVLink messages basically work, we will mainly look at the payload for our further commands.

### Command_Long


### Arm and Disarm
