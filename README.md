# Testssl.sh-JSON-Merger
This shell script merges several individual [testssl.sh](https://github.com/drwetter/testssl.sh) JSON-pretty files to one single JSON file. Useful if utilizing the [testssl2xlsx.py](https://github.com/AresS31/testssl2xlsx) parser for generating a spread sheet, which currently only supports parsing of one single JSON file.

The `testssl.sh` script by drwetter only accepts a single host or IP to scan. Specifying several hosts immediately, with one final export file is not supported. Nevertheless, using some parallelization, one can start the `testssl.sh` script several times and scan multiple hosts. Each output should be stored in the pretty-JSON format if you plan to use the `testssl2xlsx.py` parser.

For each host, you should execute the following command to get all your json files:\
`./testssl.sh --json-pretty -U -p -P -h -S -h --openssl-timeout=15 <IP>:<PORT>`

If you then want to use the parser [testssl2xlsx.py](https://github.com/AresS31/testssl2xlsx) to generate a nicely formatted spread sheet with all your observations, you'll notice that it only accepts one single JSON file. However, we've got a JSON file for each host we scanned :(

Therefore, we first have to merge all JSON files to a single file that works with the parser! 

Just use my `merge.sh` script :-)

Note: The **/scan** directory contains example *.json files. Replace them with your files.

## Installation:
````
git clone https://github.com/drwetter/testssl.sh.git -b 3.1dev
git clone https://github.com/l4rm4nd/Testssl.sh-JSON-Merger
cd Testssl.sh-JSON-Merger
python2.7 -m pip -r install requirements.txt
sudo apt-get install aha parallel
````

## Usage:
1. Place all your testssl.sh --pretty-json output files into the **/scan** directory
2. Check the path variable of `testssl2xlsx.py` in the `merge.sh` script
3. Execute with `sh merge.sh`
4. You'll find your spread sheet in the **/scan** directory.

Note: All your JSON files are moved into the **/backup_scans** folder after starting the script.


## Update:
I've added some additional parsing features for the `testssl2xlsx.py` parser. If you use my `testssl2xlsx_v2.py` script, you will get the following additional information in your spread sheet:

- Host vs. Ciphers
- Host vs. CipherTests (currently lists ciphers with < 129 bits, which may be weak)

Note: You may need to adjust the spread sheet cell's height in order to display data correctly.

## Note for scanning several hosts:
You can create a new text file and specify in each line the command to execute for an IP address and port.
This should look something like this, e.g. `hosts.txt`:
```
/bin/bash /<your_path_to_testssl>/testssl.sh --json-pretty -U -p -P -S -s -E -e -f --openssl-timeout=15 <ip1>:<port> | aha > <ip1>.html
/bin/bash /<your_path_to_testssl>/testssl.sh --json-pretty -U -p -P -S -s -E -e -f --openssl-timeout=15 <ip2>:<port> | aha > <ip2>.html
/bin/bash /<your_path_to_testssl>/testssl.sh --json-pretty -U -p -P -S -s -E -e -f --openssl-timeout=15 <ip3>:<port> | aha > <ip3>.html
```

After that, you can use `parallel` to start all the scans simultaneously:

`parallel < host.txt`
