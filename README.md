# Network-Analysis-Dashboard
Python script that links Wireshark to ELK Stack to provide a real-time visualization of network traffic on Windows bases systems.

# Description
This python code assumes that you already have Wireshark and ELK Stack installed and set up. Commands to set up the Index Mapping and Ingest Pipeline in the dev console of ELK Stack can be found in this repository. Before running the program, create 2 directories. One will contain packet files from Wireshark, and the other will contain files ready to send to ELK Stack. At the beginning of run time, the program will prompt the user and run checks to see if all of the directories and installations exist and are correct.
After checking all paths, the program will automatically start ELK Stack functionalities and begin a continuous Wireshark packet capture.
The program multithreads into 2 directory monitoring functions. The first will determine when a new packet capture file is saved and no longer growing in size while the second removes fields not accepted by ELK Stack and sends the file through Logstash.
The options of the packet capture are customizable, however, for the small home network this was created for, 250 packets per file was sufficient.
Once the packet files have been uploaded to ELK Stack through a created pipeline, it is indexed into the following queryably fields: IP Source, IP Destination, Protocol and Port.
These fields can be placed into a visualization dashboard as the user needs.

# Functions
Description of all functions and necessary user specific fields.

## main()
Checks all user specific instillations and paths before starting the continuous tshark packet capture and the two directory monitoring threads.

User specific fields:
- elasticsearch_path: The local path to the bin directory of Elasticsearch used to check the version of Elasticsearch as well as start the functionality.
- kibana_path: The local path to the bin directory of Kibana used to check the version of Kibana as well as start the functionality.
- logstash_path: The local path to the bin directory of Logstash used to check the version of Logstash as well as start the functionality.
- raw_data_path: The local path to the directory where the raw .pcapng packet capture files will be placed.
- cleaned_data_path: The local path to the directory where the .pcapng packet files are placed when they have been converted to .json and ELK Stack compatible.
- tshark_path: The local path to the directory where Wireshark is installed as tshark is used to run the continuous packet capture.
- elastic_user: The username for authentication with ELK Stack as this is needed to send data through the Logstash pipeline.
- elastic_pass: The password for the above username.
- pipeline: The ingest pipeline name created by the user in ELK Stack

## monitor_data_directory
Monitors the "Raw Data" directory for any new packet capture files. As the capture is a continuous capture, data is appended to files until they reach the limit determined in the initial packet capture command in main(). This function will check the file sizes as they grow until the file is no longer growing in size. Once this happens, the function will send the file to be converted to .json and cleaned of any unnecessary fields that ELK Stack does not accept.

## clean_packet_data
Takes in the path to the .pcapng file that needs to be converted, then runs a tshark command to convert the file into .json format and saves this file in the cleaned_data directory. Once the file is in .json format, the function removes the "_type":"doc" field from each packet. This field is deprecated in ELK Stack and will cause an error if files are sent to ELK Stack before it is removed. After the file has been cleaned, it sends the path to the cleaned file to the monitor_cleaned_directory function.

## monitor_cleaned_directory
Monitors the cleaned data directory of any new files placed by the clean_pactek_data. This function takes in the user defined cleaned_path, elastic_user and elastic_path from main. When the function detects a new file placed in this directory, it runs a curl command that sends the cleaned .json packet file to ELK Stack. Once the file is sent, the function will delete the file in order to save space.
