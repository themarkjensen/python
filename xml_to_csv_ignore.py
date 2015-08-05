import sys
import requests
from optparse import OptionParser
from xmlutils.xml2csv import xml2csv
import xml.etree.ElementTree as ET
import os
import datetime
import string


def perf_func(elem, func, level=0, elems=[]):
    stop = func(elem,level,elems)
    for child in elem.getchildren():
        if stop == 1:
            break
        perf_func(child, func, level+1, elems)


def print_level(elem,level,elems):
    if elem.tag in elems:
        tf = 1
        return tf
    print '-\t'*level+elem.tag
    elems.append(elem.tag)


def iterTag(path_to_file):
    tree = ET.parse(path_to_file)
    root = tree.getroot()

    perf_func(root, print_level)

    tag = raw_input('\nSample of XML structure above.\nWhich XML element should be used as the basis for rows?\n\n')
    return tag


if __name__ == "__main__":
    def main():

        usage = """\n\n
        usage: python xml_to_csv_ignore.py 'input_xml_file_or_URL' 'output_file_name' [options]

        'input_xml_file_or_URL' --> 	input XML file or URL to be converted to CSV
        'output_file_name' -->		output CSV file name. A folder will be created with the same name to house the file

        Options:
        --tag='tag' -->			the xml element that should be used as the basis of rows in the CSV
        --ignore='tag1,tag2,tag#'	the xml element(s) that should be excluded from the CSV file output
        --sample=100 -->		an integer limiting the number of rows in the CSV file output
        \n\n
        """

        print usage

        parser = OptionParser(usage, version='1')
        parser.add_option("-t", "--tag", action="store", type="string", dest="tag")
        parser.add_option("-i", "--ignore", action="store", type="string", dest="ignore")
        parser.add_option("-s", "--sample", action="store", type="int", dest="sample")
        (options, args) = parser.parse_args()

        if len(args) == 0:
            input_file = str(raw_input('\nURL or Path to XML file: '))
            output_file = "output_file"
        elif len(args) == 1:
            input_file = args[0]
            output_file = "output_file"
        elif len(args) == 2:
            input_file = args[0]
            output_file = args[1]
        else:
            print "\n%prog takes 2 arg. %d args provided.\n" % len(args)
            sys.exit(1)

        if input_file.find('http') != -1:
            print "\nDownloading file %s\n" % input_file
            dtNow = datetime.datetime.now().strftime("%m-%d-%Y %I.%M.%S %p")
            if output_file == "output_file":
                local_dir = input_file[input_file.rfind('/')+1:input_file.rfind('.')]
            else:
                local_dir = output_file
            local_input_file = local_dir + ' - ' + dtNow + '.xml'
            csv_file = local_dir + ' - ' + dtNow + '.csv'
            if not os.path.exists(local_dir):
                os.makedirs(local_dir)
            handle = open(local_dir + '/' + local_input_file, 'wb')
            response = requests.get(input_file, stream=True)
            if not response.ok:  # Something went wrong
                print "\nURL response error. Check the URL.\n"
                sys.exit(1)
            for block in response.iter_content(1024):
                if not block:
                    break
                handle.write(block)
            handle.close()
            print "\n%s downloaded successfully!\n" % local_input_file
        elif input_file.find('/') != -1:
            dtNow = datetime.datetime.now().strftime("%m-%d-%Y %I.%M.%S %p")
            if output_file == "output_file":
                local_dir = input_file[input_file.rfind('/')+1:input_file.rfind('.')]
            else:
                local_dir = output_file
            local_input_file = local_dir + ' - ' + dtNow + '.xml'
            csv_file = local_dir + ' - ' + dtNow + '.csv'
            print "Copying %s to new directory" % local_input_file
            in_file = open(input_file, 'rb')
            input_file_content = in_file.read()
            if not os.path.exists(local_dir):
                os.makedirs(local_dir)
            out_file = open(local_dir + '/' + local_input_file, 'wb')
            out_file.write(input_file_content)
            in_file.close()
            out_file.close()
        else:
            dtNow = datetime.datetime.now().strftime("%m-%d-%Y %I.%M.%S %p")
            if output_file == "output_file":
                local_dir = input_file[:input_file.find('.xml')]
            else:
                local_dir = output_file
            local_input_file = local_dir + ' - ' + dtNow + '.xml'
            csv_file = local_dir + ' - ' + dtNow + '.csv'
            print "\nCopying %s to new directory\n" % local_input_file
            in_file = open(input_file, 'rb')
            input_file_content = in_file.read()
            if not os.path.exists(local_dir):
                os.makedirs(local_dir)
            out_file = open(local_dir + '/' + local_input_file, 'wb')
            out_file.write(input_file_content)
            in_file.close()
            out_file.close()

        if options.tag is None:
            print "\nGenerating preview of XML structure...\n"
            xml_row = iterTag(local_dir + '/' + local_input_file)
        else:
            xml_row = options.tag

        if options.ignore is None:
            exclusions = raw_input('\nWhich XML element(s) should be excluded from the CSV file output? List element(s) separated by commas (,).\n\n')
            lsExclusions = string.split(exclusions, ',')
        else:
            lsExclusions = string.split(options.ignore, ',')

        if options.sample is None:
            sample = raw_input('\nIf only a sample is desired, enter the max number of rows. Leave blank for all rows.\n\n')
            if sample == '':
                sample = None
            else:
                sample = int(sample)
        else:
            sample = options.sample


        print "\nConverting %s to %s based on '%s' as row identifier...\n" % (local_input_file, csv_file, xml_row)
        converter = xml2csv(local_dir + '/' + local_input_file, local_dir + '/' + csv_file, encoding="utf-8")
        converter.convert(tag=xml_row, ignore=lsExclusions, limit=sample)
        print "\n%s ---> %s -- Conversion Successful!\n" % (local_input_file, csv_file)

    main()
