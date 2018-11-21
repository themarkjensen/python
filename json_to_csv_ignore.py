import sys
import os
from optparse import OptionParser
import requests
import json
import pandas as pd
import datetime


######################################################
### Print the JSON file structure based on ###########
### traversal of the first item from top to bottom ###
######################################################

def traverse_obj(obj, level=0, indent_str='\t- ', names={}, parent='', first=True):

    # check if obj is container
    if isinstance(obj, (tuple, list, dict, set)):
        is_container = True
    else:
        is_container = False

    # Iterate over container
    if is_container == True:
        if isinstance(obj, dict):
            # iterate over keys, values
            for key, val in obj.items():

                # If key is already in names list
                # then stop traversing
                if key in names:
                    break

                # add key to names list
                names[key] = parent + '.' + key


                # print the key
                print(indent_str*level + key)


                if isinstance(val, (tuple, list, dict, set)):
                    first=False
                    traverse_obj(obj[key], level=level+1, names=names, parent=parent + '.' + key, first=first)

        if isinstance(obj, list):
            if first == True:
                sep = ''
                first = False
            else:
                sep = '.'
            # iterate over items
            for i, item in enumerate(obj):
                if isinstance(item, (tuple, list, dict, set)):
                    traverse_obj(item, level=level, names=names, parent=parent + sep + str(i), first=first)

    if is_container == False:
        print(indent_str*level + obj)

    return names

####################################################
### Function to remove unwanted key, value pairs ###
### from a dict; supports the ignore list ##########
####################################################

def remove_ignored(dict_obj, ignore_list=[]):
    for item in ignore_list:
        try:
            del(dict_obj[item])
        except:
            pass
    return dict_obj

######################################################
### Function to flatten a dictionary so that items ###
### therein can be represented in tabular format #####
######################################################

def flatten_dict(dict_obj, sep='_'):

    flat_obj = {}

    # Loop thru the object
    for key, val in dict_obj.items():

        # if it's a dict, then flatten it
        if isinstance(val, dict):
            for k,v in val.items():
                name = str(key) + sep + str(k)
                flat_obj[name] = v

        else:
            flat_obj[key] = val

    return flat_obj

################################
### Main Program Starts Here ###
################################

if __name__ == "__main__":
    def main():

        usage = """\n\n
        usage: python json_to_csv_ignore.py 'input_json_file_or_URL' 'output_file_name' [options]

        'input_json_file_or_URL' --> 	input JSON file or URL to be converted to CSV
        'output_file_name' -->		output CSV file name. A folder will be created with the same name to house the file

        Options:
        --tag='tag' -->			the JSON element that should be used as the basis of rows in the CSV
        --ignore='tag1,tag2,tag#'	the JSON element(s) that should be excluded from the CSV file output
        --sample=100 -->		an integer limiting the number of rows in the CSV file output
        --flatten -->           flattens nested items to the top layer (default=False)
        \n\n
        """

        print(usage)

        ###############
        ### Options ###
        ###############

        parser = OptionParser(usage, version='1')
        parser.add_option("-t", "--tag", action="store", type="string", dest="tag")
        parser.add_option("-i", "--ignore", action="store", type="string", dest="ignore")
        parser.add_option("-s", "--sample", action="store", type="int", dest="sample")
        parser.add_option("-f", "--flatten", action="store_true", dest="flatten", default=False)
        (options, args) = parser.parse_args()

        if len(args) == 0:
            input_file = str(input('\nURL or Path to JSON file: '))
            output_file = "output_file"
        elif len(args) == 1:
            input_file = args[0]
            output_file = "output_file"
        elif len(args) == 2:
            input_file = args[0]
            output_file = args[1]
        else:
            print("\njson_to_csv.py takes 2 arg. " + len(args) + " args provided.\n")
            sys.exit(1)

        ##############################
        ### Get JSON file and copy ###
        ### to local directory #######
        ##############################

        if input_file.find('http') != -1:
            print("\nDownloading file " + input_file + "\n")
            dtNow = datetime.datetime.now().strftime("%Y-%m-%d %I.%M.%S %p")
            if output_file == "output_file":
                local_dir = input_file[input_file.rfind('/')+1:input_file.rfind('.')]
            else:
                local_dir = output_file
            local_input_file = local_dir + ' - ' + dtNow + '.json'
            csv_file = local_dir + ' - ' + dtNow + '.csv'
            if not os.path.exists(local_dir):
                os.makedirs(local_dir)
            handle = open(local_dir + '/' + local_input_file, 'wb')
            response = requests.get(input_file, stream=True)
            if not response.ok:  # Something went wrong
                print("\nURL response error. Check the URL.\n")
                sys.exit(1)
            for block in response.iter_content(1024):
                if not block:
                    break
                handle.write(block)
            handle.close()
            # read the content
            with open(local_dir + '/' + local_input_file, 'rb') as in_file:
                input_file_content = in_file.read()

            print("\n" + local_input_file + " downloaded successfully!\n")
        elif input_file.find('/') != -1:
            dtNow = datetime.datetime.now().strftime("%Y-%m-%d %I.%M.%S %p")
            if output_file == "output_file":
                local_dir = input_file[input_file.rfind('/')+1:input_file.rfind('.')]
            else:
                local_dir = output_file
            local_input_file = local_dir + ' - ' + dtNow + '.json'
            csv_file = local_dir + ' - ' + dtNow + '.csv'
            print("Copying " + local_input_file + " to new directory")
            in_file = open(input_file, 'rb')
            input_file_content = in_file.read()
            if not os.path.exists(local_dir):
                os.makedirs(local_dir)
            out_file = open(local_dir + '/' + local_input_file, 'wb')
            out_file.write(input_file_content)
            in_file.close()
            out_file.close()
        else:
            dtNow = datetime.datetime.now().strftime("%Y-%m-%d %I.%M.%S %p")
            if output_file == "output_file":
                local_dir = input_file[:input_file.find('.json')]
            else:
                local_dir = output_file
            local_input_file = local_dir + ' - ' + dtNow + '.json'
            csv_file = local_dir + ' - ' + dtNow + '.csv'
            print("Copying " + local_input_file + " to new directory")
            in_file = open(input_file, 'rb')
            input_file_content = in_file.read()
            if not os.path.exists(local_dir):
                os.makedirs(local_dir)
            out_file = open(local_dir + '/' + local_input_file, 'wb')
            out_file.write(input_file_content)
            in_file.close()
            out_file.close()

        # Load the file content into a python object
        object = json.loads(input_file_content)

        #####################
        ### Parse options ###
        #####################

        if options.tag is None:
            print("\nGenerating preview of XML structure...\n")

            # traverse the obj and show the user the structure
            names = traverse_obj(object)

            # Get the input from the user
            target = input('\nSample of JSON structure above.\nWhich JSON element should be used as the basis for rows?\n\n')
        else:
            target = options.tag

        if options.ignore is None:
            exclusions = input('\nWhich JSON element(s) should be excluded from the CSV file output? List element(s) separated by commas (,).\n\n')
            exclusions = exclusions.split(',')
        else:
            exclusions = options.ignore.split(',')

        if options.sample is None:
            sample = input('\nIf only a sample is desired, enter the max number of rows. Leave blank for all rows.\n\n')
            if sample == '':
                sample = None
            else:
                sample = int(sample)
        else:
            sample = options.sample

        # Store the flatten flag
        flatten = options.flatten

        ###############################
        ### convert the JSON to csv ###
        ###############################

        # Isolate the target
        target_addr = [int(x) if x.isnumeric() else x for x in names[target].split('.')]

        def drill_to_target(obj, path_list):
            for item in path_list:
                obj = obj[item]
                _path_list_ = [x for x in path_list if x != item]
                drill_to_target(obj, _path_list_)
            return obj

        target_obj = drill_to_target(object, target_addr)

        # remove unwanted names
        if len(exclusions) > 0:
            target_obj = [remove_ignored(obj, ignore_list=exclusions) for obj in target_obj]

        # flatten
        if flatten == True:
            target_obj = [flatten_dict(obj) for obj in target_obj]

        # Convert to dataframe
        print("\nConverting " + local_input_file + " to " + csv_file + " based on '" + target + "' as row identifier...\n")

        df_target = pd.DataFrame.from_dict(target_obj, orient='columns')
        df_target.head(1).transpose()

        # If sample option provided, then get just those rows
        if sample is not None:
            df_target = df_target.iloc[0:sample,:].copy()

        # write the dataframe to the csv
        df_target.to_csv(os.path.join(local_dir, csv_file), index=False)

        print("\n" + local_input_file + " ---> " + csv_file + " -- Conversion Successful!\n")

    main()
