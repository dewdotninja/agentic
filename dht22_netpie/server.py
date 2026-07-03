import paho.mqtt.client as mqtt
from fastmcp import FastMCP
from typing import Annotated
from pydantic import Field
import time

# 1. Initialize MCP Server
mcp = FastMCP("dht22_netpie_server")

# 2. MQTT Configuration
MQTT_BROKER = "broker.netpie.io"  # Replace with your actual broker IP or URL
MQTT_PORT = 1883
RESPONSE_TOPIC1 = "@msg/parms"      # response
RESPONSE_TOPIC2 = "@msg/parmval" 
CMD_TOPIC = "@msg/cmd"
rcvd_data = ""
rcvd_msg = ""

Client_ID = ""
User = ""
Password = ""
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                         client_id=Client_ID,
                         transport='tcp',
                         protocol=mqtt.MQTTv311,
                         clean_session=True)
client.username_pw_set(User,Password)


def on_message(client, userdata, message):
    global rcvd_msg, rcvd_topic
    rcvd_msg = str(message.payload.decode("utf-8"))
    rcvd_topic = message.topic
   
def on_connect(client, userdata, flags, rc, properties=None):
    """Callback when the client connects to the broker."""
    print(f"Connected to MQTT Broker with result code {rc}")
    # Subscribe to all device status topics
    client.subscribe(RESPONSE_TOPIC1)
    client.subscribe(RESPONSE_TOPIC2)



client.on_connect = on_connect
client.on_message = on_message
print(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}...")
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()  # Starts a background thread to handle networking

@mcp.tool

def query_temperature() -> str:
    """
    query the current temperature from DHT22 
    """
    try:
        result = client.publish(CMD_TOPIC,"temp")
        result.wait_for_publish()
        time.sleep(2)
        return f"temperature from DHT22 is {rcvd_msg} Celcius"
    except Exception as e:
        return f"Failed to query from DHT22"  

@mcp.tool
async def start_fan_timer(
    period=Field(30,description="period to turn the fan on",ge=5,le=1200)) -> str:
    """
    Turn fan on for user-specified seconds.
    Args:
    period : the duration that fan is turned on
    """
    try:
        cmd = "timer="+str(period)
        result = client.publish(CMD_TOPIC,cmd)
        result.wait_for_publish()
        time.sleep(2)
        result = client.publish(CMD_TOPIC,"starttimer")
        result.wait_for_publish()
        time.sleep(2)
        rcvd_data = rcvd_msg.split(",")
        if rcvd_data[0] == "1":
            return f"Fan is turned on for {period} secs"
        else:
            return "No response from the temperature control IoT device"
    except Exception as e:
        return f"Failed to start the fan timer" 

@mcp.tool
async def start_fan_auto(
    maxtemp=Field(40,
                  description="maximum temperature allowed before the fan is turned on",
                  ge=20,le=50)) -> str:
    """
    Compare the current temperature measured by DHT22 with maxtemp. 
    If it exceeds maxtemp, turn the fan on. Otherwise, turn the fan off.
    Args:
    maxtemp : the threshold temperature to turn the fan on/off
    """
    try:
        cmd = "maxtemp="+str(maxtemp)
        result = client.publish(CMD_TOPIC,cmd)
        result.wait_for_publish()
        time.sleep(2)
        result = client.publish(CMD_TOPIC,"startautofan")
        result.wait_for_publish()
        time.sleep(2)
        rcvd_data = rcvd_msg.split(",")
        if rcvd_data[0] == "2":
            return f"Fan is set to auto mode. It is turned on when temperature exceeds {maxtemp} celcius"
        else:
            return "No response from the temperature control IoT device"
    except Exception as e:
        return f"Failed to start the fan auto-mode" 


# ---------- general tools ------------------
@mcp.tool
async def send_device_command(command: str) -> str:
    """
    Send a command string to the IoT device.
    Args:
        command: The command to send (e.g., 'maxtemp', 'fan', 'temp')
    """

    try:
        # client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        
        result = client.publish(CMD_TOPIC, command)
        # Wait for transmission to complete
        result.wait_for_publish()
        time.sleep(2)
    
        return f"Successfully sent command '{command}' to device. Response is {rcvd_msg}"
    except Exception as e:
        return f"Failed to send command: {str(e)}"

@mcp.tool()
async def publish_command(payload: str) -> str:
    """
    Publish a command or message to a specific MQTT topic to control an IoT device.
    
    Args:
        payload: The command string(e.g., 'fan', 'starttimer', ).
    """
    result = client.publish(CMD_TOPIC, payload)
    # Wait for transmission to complete
    result.wait_for_publish()
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        return f"Successfully published command '{payload}'"
    return f"Failed to publish message. Error code: {result.rc}"

@mcp.tool()
def get_device_status() -> str:
    """
    Retrieve the latest cached state/telemetry for a specific IoT device.
    
    """
    # target_topic = f"device/{device_id}/status"
    data = rcvd_msg
    
    if data:
        return f"Last data is {data}"
    return f"No status data available"

if __name__ == "__main__":
    try:
        # Run the MCP server using stdin/stdout transport channel
        mcp.run(transport="stdio")
    finally:
        # Clean up MQTT threads upon server shutdown

        client.loop_stop()
        client.disconnect()
