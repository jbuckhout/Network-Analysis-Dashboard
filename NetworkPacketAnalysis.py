"""
Author: Jonathan Buckhout
Version: 1.0
Date: 6/18/2024
Description: This is a projects to show proficiency in data management and display using Network Packet Analysis through
ELK Stack and Wireshark. Each of the following steps set up the ELK Stack server and link to a file that contains
Wireshark packet files. Through the file system, Wireskark adds new files as the packet capture continuously runs and
automatically send them to ELK Stack to be processed for search and display. This program runs multiple commands through
the CMD in order to reach all necessary file paths and run the Wireshark packet capture.
"""

import os
import time
import subprocess
import threading
import requests


"""
monitor_data_directory takes in the user specified raw data directory and monitors it for an new files placed there.
If there is a new file, it will clean the data and save the cleaned file in the cleaned data directory.
"""


def monitor_data_directory(directory):
    print(f"Monitoring directory: {directory}")
    already_seen = set(os.listdir(directory))
    file_sizes = {}
    counter = 1

    while True:
        # check for new files
        current_files = set(os.listdir(directory))
        new_files = current_files - already_seen

        for file in new_files:
            if file.endswith('.pcapng'):
                filepath = os.path.join(directory, file)
                print(f"New File Detected: {filepath}")
                file_sizes[file] = os.path.getsize(filepath)

        # check if existing files have stopped growing:
        for file in list(file_sizes.keys()):
            filepath = os.path.join(directory, file)
            if file in current_files:
                time.sleep(2)
                current_size = os.path.getsize(filepath)
                if current_size > file_sizes[file]:
                    file_sizes[file] = current_size
                else:
                    # file size has not changed, clean and remove it from tracking
                    clean_packet_data(filepath, counter)
                    counter += 1
                    del file_sizes[file]

        already_seen = current_files


"""
clean_packet_data: Takes in the file path to the file that needs to be cleaned the file name and a counter (for file naming)
It first changes the .pcapng file to an ELKStack compatible .json file, then removes the deprecated _type field
It then sends the newly cleaned packet file through Logstash.
"""


def clean_packet_data(filepath, counter):
    tshark_path = 'C:\\Program Files\\Wireshark\\tshark.exe'
    file_type = '.pcapng'
    json_file_path = filepath.replace(file_type, '.json')
    # run tshark to convert .pcapng to .json
    try:
        subprocess.run([tshark_path, '-r', filepath, '-T', 'ek'], stdout=open(json_file_path, 'w'), check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to convert .pcapng file: {e}")

    # set naming convention for clean packet files
    filename = f"cleaned_packets_{counter:04d}.json"
    # file path for cleaned packet files
    cleaned_path = 'C:\\ELKStack\\InputData\\CleanedData'
    cleaned_file_path = os.path.join(cleaned_path, filename)
    # substring to match the deprecated _type parameter from the packet file
    substring = ",\"_type\":\"doc\""

    # open the original file for reading
    with open(json_file_path, 'r') as infile:
        # open/create the cleaned data file that will be sent through logstash
        with open(cleaned_file_path, 'w') as outfile:
            # iterate through the lines to find the substring and replace it with an empty string
            for line in infile:
                modified_line = line.replace(substring, '')
                # write the modified line to the outfile
                outfile.write(modified_line)

    # delete the non-cleaned .json file in raw data to keep it clean
    os.remove(json_file_path)


"""
monitor_cleaned_directory is the second threaded function that monitors the cleaned packet data directory for any new
files. When it detects a new file it will send it through the user specified ingest pipeline to be indexed in ELK Stack.
"""


def monitor_cleaned_directory(cleaned_path, elastic_user, elastic_pass, pipeline):
    print(f"Monitoring Cleaned Data Directory: {cleaned_path}")
    already_seen = set(os.listdir(cleaned_path))

    while True:
        # check for new files
        current_files = set(os.listdir(cleaned_path))
        new_files = current_files - already_seen

        for file in new_files:
            print(f"{file} added to cleaned directory. Sending it through Logstash")
            # create the correct path to the data
            send_path = os.path.join(cleaned_path, file)
            # run the curl command here to send the packet data through logstash
            command = ["curl", "-s", "-H", "Content-Type: application/x-ndjson", "-XPOST", f"http://localhost:9200/_bulk?pipeline={pipeline}",
                       "-u", f"{elastic_user}:{elastic_pass}", "--data-binary", f"@{send_path}"]

            subprocess.run(command, capture_output=True, text=True)
        # update already_seen for the next check.
        already_seen = current_files
        # delete the file from the directory to save space.
        # os.remove(send_path)
        # pause for 2 seconds to reduce the number of times this loop runs the check
        time.sleep(2)


def main():
    # user specific paths

    # path to the bin directory within elasticsearch
    elasticsearch_path = "C:/ELKStack/elasticsearch/elasticsearch-8.14.1/bin/"
    # path to the bin directory within kibana
    kibana_path = "C:/ELKStack/kibana/kibana-8.14.1/bin/"
    # path to the bin directory within logstash
    logstash_path = "C:/ELKStack/logstash/bin/"
    # path to raw packet .pcapng files
    raw_data_path = "C:/ELKStack/InputData/RawData/"
    # path to cleaned .json files
    cleaned_data_path = "C:/ELKStack/InputData/CleanedData"
    # path to tshark.exe
    tshark_path = "C:/\"Program Files\"/Wireshark/tshark.exe"
    # username to the elk stack login
    elastic_user = "elastic"
    # password to the username above
    elastic_pass = "@NinjaKiwi66"
    # ingest pipeline name created in ELK Stack
    pipeline = "packets"

    # checks to make sure that all necessary programs/directories are installed/created
    user_check = input("Do you need to check the paths or installations? (Y/N): ")
    if user_check == 'Y' or user_check == 'y':
        print(f"Checking installations and paths")
        # checks to make sure all dependent programs are installed and if the data paths are valid
        try:
            command = f'powershell -Command "Start-Process cmd -ArgumentList \'/c {elasticsearch_path} elasticsearch --version\' -Verb RunAs"'
            subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Elasticsearch is installed and accessible")
        except subprocess.CalledProcessError as e:
            print(f"Failed to find Elasticsearch: {e}")
            print(f"Make sure Elasticsearch is installed and the correct path to '/bin' is placed above")
            exit(1)

        try:
            command = f'powershell -Command "Start-Process cmd -ArgumentList \'/c {kibana_path} kibana --version\' -Verb RunAs"'
            subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Kibana is installed and accessible")
        except subprocess.CalledProcessError as e:
            print(f"Failed to find Kibana: {e}")
            print(f"Make sure Kibana is installed and the correct path to '/bin' is placed above")
            exit(1)

        try:
            command = f'powershell -Command "Start-Process cmd -ArgumentList \'/c {logstash_path} logstash --version\' -Verb RunAs"'
            subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Logstash is installed and accessible")
        except subprocess.CalledProcessError as e:
            print(f"Failed to find Logstash: {e}")
            print(f"Make sure Logstash is installed and the correct path to '/bin' is placed above")
            exit(1)

        try:
            command = f'powershell -Command "Start-Process cmd -ArgumentList \'/c {tshark_path} tshark --version\' -Verb RunAs"'
            subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"tshark is installed and accessible")
        except subprocess.CalledProcessError as e:
            print(f"Failed to find tshark: {e}")
            print(f"Make sure Wireshark is installed and the correct path to 'tshark.exe' is placed above")
            exit(1)

        if not os.path.exists(raw_data_path):
            print(f"The path to the raw data does not exist.")
            exit(1)
        else:
            print(f"Path to raw data confirmed.")

        if not os.path.exists(cleaned_data_path):
            print(f"The path to the cleaned data does not exist.")
            exit(1)
        else:
            print(f"Path to cleaned data confirmed.")

    # start up Elasticsearch
    print(f"Starting Elasticsearch...")
    os.system("start cmd /k cd /ELKStack/elasticsearch/elasticsearch-8.14.1/bin ^&^& elasticsearch.bat")

    start = 0
    while start != 1:
        try:
            response = requests.get('http://localhost:9200')
            if response.status_code == 200 or response.status_code == 401:
                print(f"Elasticsearch successfully started.")
                start = 1
            else:
                print(f"Elasticsearch is not yet available. {response.status_code} Waiting...")
                time.sleep(5)
        except requests.exceptions.RequestException:
            print(f"Elasticsearch is not yet available. Waiting...")

    # start up kibana after elasticsearch has fully started
    print(f"Starking Kibana...")
    os.system("start cmd /k cd /ELKStack/kibana/kibana-8.14.1/bin ^&^& kibana.bat")

    # wait until the system has fully started up
    start = 0
    while start != 1:
        try:
            response = requests.get('http://localhost:5601')
            if response.status_code == 200:
                start = 1
                print(f"Kibana has started.")
            else:
                time.sleep(10)
        except requests.exceptions.RequestException:
            print(f"Kibana has not yet started...")

    # start up logstash after elasticsearch and kibana have started
    print(f"Starting Logstash...")
    os.system("start cmd /k cd /ELKStack/logstash/logstash-8.14.1/bin ^&^& logstash -f logstash.conf")

    # wait until the system has fully started up
    start = 0
    while start != 1:
        try:
            response = requests.get('http://localhost:9600')

            if response.status_code == 200:
                start = 1
                print(f"Logstash has started.")
            else:
                time.sleep(5)
        except requests.exceptions.RequestException:
            print(f"Logstash has not yet started...")

    # start up wireshark and begin the continuous packet capture, saving the files to be cleaned
    print(f"Beginning packet capture...")
    os.system("start cmd /k cd /\"Program Files\"/Wireshark ^&^& tshark -i 4 -b packets:250 -w " + raw_data_path + "packets_.pcapng")

    # create a new thread to watch the directory path for new raw data files and then clean them
    monitor_raw_thread = threading.Thread(target=monitor_data_directory, args=[raw_data_path])
    # create a new thread to watch the directory path for new cleaned data to send through logstash
    monitor_cleaned_thread = threading.Thread(target=monitor_cleaned_directory, args=[cleaned_data_path, elastic_user, elastic_pass, pipeline])

    # start the two threads
    monitor_raw_thread.start()
    monitor_cleaned_thread.start()

    monitor_raw_thread.join()
    monitor_cleaned_thread.join()


if __name__ == "__main__":
    main()
