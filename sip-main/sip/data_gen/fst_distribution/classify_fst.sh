#!/bin/bash

# Directory containing the files (change this to your folder)
folder="/Users/abedqaddoumi/PycharmProjects/fst-projs/sip-main/sip/data_gen/fst_distribution"

# Loop through all files in the folder
for file in "$folder"/*; do
    # Check if it's a regular file
    if [[ -f "$file" ]]; then
        # Get the base name of the file (without the directory path)
        base_name=$(basename "$file")
        
	echo "File: $base_name"	

        # Run classify and capture the output
        output=$(classify -N -a SL SP < "$file")

        # Print the original file name and classify output
        echo "Classify Output: $output"
        echo "--------------------------------------"
    fi
done

