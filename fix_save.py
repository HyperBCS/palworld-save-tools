#!/usr/bin/env python3

import json
import os
import argparse
from pathlib import Path


from lib.gvas import GvasFile
from lib.noindent import CustomEncoder
from lib.palsav import compress_gvas_to_sav, decompress_sav_to_gvas
from lib.paltypes import PALWORLD_CUSTOM_PROPERTIES, PALWORLD_TYPE_HINTS

def create_new_directory_path(file_path):
    # Extract the filename from the file path
    filename = Path(file_path).name

    # Get the current working directory
    cwd = os.getcwd()

    # Create the new directory path
    new_directory_path = os.path.join(cwd, 'fixed', filename)

    return new_directory_path

def main():
    # Check whether the specified path exists or not
    path = "fixed"
    isExist = os.path.exists(path)
    if not isExist:
        # Create a new directory because it does not exist
        os.makedirs(path)
    
    parser = argparse.ArgumentParser(
        prog="palworld-save-tools",
        description="Converts Palworld save files to and from JSON",
    )
    parser.add_argument("filename")
    parser.add_argument(
        "--output",
        "-o",
        help="Output file (default: fixed/<filename>.sav)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.filename):
        print(f"{args.filename} does not exist")
        exit(1)
    if not os.path.isfile(args.filename):
        print(f"{args.filename} is not a file")
        exit(1)

    if args.filename.endswith(".sav"):
        if not args.output:
            output_path = create_new_directory_path(args.filename)
        else:
            output_path =  args.output
        convert_sav_to_json(args.filename, output_path)

def convert_json_to_sav(json_data, output_path):
    print(f"Converting data to SAV, saving to {output_path}")
    gvas_file = GvasFile.load(json_data)
    print(f"Compressing SAV file")
    if (
        "Pal.PalWorldSaveGame" in gvas_file.header.save_game_class_name
        or "Pal.PalLocalWorldSaveGame" in gvas_file.header.save_game_class_name
    ):
        save_type = 0x32
    else:
        save_type = 0x31
    sav_file = compress_gvas_to_sav(
        gvas_file.write(PALWORLD_CUSTOM_PROPERTIES), save_type
    )
    print(f"Writing SAV file to {output_path}")
    with open(output_path, "wb") as f:
        f.write(sav_file)





def parse_json(json_data, out_path):
    # Dictionary to hold InstanceId values and their counts
    instance_counts = {}
    fix_dict = {}

    # Scan for "InstanceId" and count occurrences
    def count_instance_ids(data):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "InstanceId" and isinstance(value, dict) and "value" in value:
                    instance_id = value["value"]
                    instance_counts[instance_id] = instance_counts.get(instance_id, 0) + 1
                    
                count_instance_ids(value)
        elif isinstance(data, list):
            for item in data:
                count_instance_ids(item)

    # Modify "RawData" entries in a nested structure
    def modify_raw_data(data):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "RawData" and isinstance(value, dict):
                    raw_data = value
                    if "value" in raw_data  and isinstance(raw_data["value"], dict) and  "individual_character_handle_ids" in raw_data["value"] and "group_type" in raw_data["value"]:
                        if raw_data["value"]["group_type"] == "EPalGroupType::Guild":
                            individual_ids = raw_data["value"]["individual_character_handle_ids"]
                            group_id = raw_data["value"]["group_id"]
                            guild_name = raw_data["value"]["guild_name"]
                            old_size = len(individual_ids)
                            raw_data["value"]["individual_character_handle_ids"] = [
                                entry for entry in individual_ids
                                if instance_counts.get(entry.get("instance_id"), 0)
                            ]
                            fix_dict[group_id] = {"name": guild_name, "old": old_size, "new": len(raw_data["value"]["individual_character_handle_ids"]) }
                            
                else:
                    modify_raw_data(value)
        elif isinstance(data, list):
            for item in data:
                modify_raw_data(item)

    # Initial scan to count InstanceIds
    print("Processing instance_ids...",end="", flush=True)
    count_instance_ids(json_data)
    print("done")

    # Modify "RawData" entries
    print("Processing raw data...",end="", flush=True)
    modify_raw_data(json_data)
    print("done")
    
    print("Fix Results:")
    for g in fix_dict:
        print(f"\tGuild: {fix_dict[g]['name']}\n\t\tOld: {fix_dict[g]['old']}\n\t\tNew: {fix_dict[g]['new']}")

    return convert_json_to_sav(json_data, out_path)

def convert_sav_to_json(filename, output_path):
    print(f"Converting {filename} to JSON")
    print(f"Decompressing sav file")
    with open(filename, "rb") as f:
        data = f.read()
        raw_gvas, _ = decompress_sav_to_gvas(data)
    print(f"Loading GVAS file")
    gvas_file = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, PALWORLD_CUSTOM_PROPERTIES)
    parse_json(gvas_file.dump(), output_path)
    
if __name__ == "__main__":
    main()
