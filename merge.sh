#!/bin/bash
# Merge script for testssl.sh 2.9dev from https://testssl.sh/dev/
# (a178f3e 2018-03-18 23:38:23 -- )

TESTSSL_PATH="../testssl2xlsx_v2.py"
RAND=$(date +%Y%m%d_%H%M%S_SCAN)

echo "[!] Please store all your scan results as pretty json files in the scans directory."
echo "[!] The script will modify the files and generate a final Excel file :-)"
echo "[!] Your intial json files will be backuped in the backup_scans directory."
echo "[!] The final Excel file can be found in the scans directory."
echo "[!] Developed by Laurent Vetter"
echo "... - ... - ... - ... - ... -"

cd scans
mkdir backup_scans 2> /dev/null

# backup scans
echo "[+] Backup all scan files"
mkdir backup_scans/$RAND
cp *.json backup_scans/$RAND/.

# remove interrupted scans
echo "[+] Remove interrupted scan files"
grep -l '"scanTime"  : "Scan interrupted"' *.json > /tmp/ignored.log
find . -type f -exec grep -q '"scanTime"  : "Scan interrupted"' {} \; -delete 

# remove first x lines of each json file, may have to be adjusted for different testssl.sh versions
echo "[+] Remove preamble lines"
sed -i '/\[/,$!d' *.json
sed -i '1,1d' *.json

# remove last 4 lines of all scan json files
echo "[+] Remove epilog lines"
for filename in *.json; do
	# reverse json file
	tac $filename > /tmp/rev.json
	# remove everything before ],
	sed -e '/],/,$!d' /tmp/rev.json > /tmp/rev2.json
	# remove first line
	sed -i '1,1d' /tmp/rev2.json
	# reverse again
	tac /tmp/rev2.json > "New"_$filename
	#cp "New"_$filename debug/.
	# clean
	rm /tmp/*.json && rm $filename
done

# generate the final file with starting header
echo "[+] Generate file header"
cat ../template/header.json > ../summerized_scans.json

# append each json file to the scanresult section of our final json file
echo "[+] Append all json files"
for file in *.json; do
	cat $file >> ../summerized_scans.json && echo "," >> ../summerized_scans.json
done

# remove the last comma of the file
echo "[+] Establish well-formated file"
head -n -1 ../summerized_scans.json > /tmp/asd && mv /tmp/asd ../summerized_scans.json

# append footer to the final file
echo "[+] Append file footer"
cat ../template/footer.json >> ../summerized_scans.json

# clean up
echo "[+] Clean up"
rm *.json

# generate the Excel file
echo "[+] Generate final Excel file"
echo "... - ... - ... - ... - ... -"
python $TESTSSL_PATH -iJ ../summerized_scans.json || echo "The error 'ValueError: Expecting property name' means that one of your json files has a missing \"finding\":\"xxx\" property."

# show ignored files
if [ -s "/tmp/ignored.log" ] 
then
	echo ""
	echo "[!] The following files have been ignored due to interrupted testssl scan:"
	cat /tmp/ignored.log
fi

# comment this line to keep the final merged file
rm ../summerized_scans.json
