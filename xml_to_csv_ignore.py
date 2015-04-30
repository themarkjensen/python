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
        
        usage = "usage: %prog 'input xml file (URL ok)'"
        parser = OptionParser(usage, version='1')
        (options, args) = parser.parse_args()
        
        if len(args) == 0:
            xml_file = str(raw_input('\nURL or Path to XML file: '))          
        elif len(args) == 1:
            xml_file = args[0]
        else:
            print "\n%prog takes 1 arg. %d args provided.\n" % len(args)
            sys.exit(1)

        if xml_file.find('http') != -1:
            print "\nDownloading file %s\n" % xml_file
            dtNow = datetime.datetime.now().strftime("%m-%d-%Y %I.%M.%S %p")
            local_dir = xml_file[xml_file.rfind('/')+1:xml_file.rfind('.')]
            local_xml_file = local_dir + ' - ' + dtNow + xml_file[xml_file.rfind('.'):]
            csv_file = local_dir + ' - ' + dtNow + '.csv'
            if not os.path.exists(local_dir):
                os.makedirs(local_dir)
            handle = open(local_dir + '/' + local_xml_file, 'wb')
            response = requests.get(xml_file, stream=True)
            if not response.ok:  # Something went wrong
                print "\nURL response error. Check the URL.\n"
                sys.exit(1)
            for block in response.iter_content(1024):
                if not block:
                    break    
                handle.write(block)
            handle.close()
            print "\n%s downloaded successfully!\n" % local_xml_file
        elif xml_file.find('/') != -1:
            dtNow = datetime.datetime.now().strftime("%m-%d-%Y %I.%M.%S %p")
            local_dir = xml_file[xml_file.rfind('/')+1:xml_file.rfind('.')]
            local_xml_file = local_dir + ' - ' + dtNow + xml_file[xml_file.rfind('.'):]
            csv_file = local_dir + ' - ' + dtNow + '.csv'
            print "Copying %s to new directory" % local_xml_file
            in_file = open(xml_file, 'rb')
            xml_file_content = in_file.read()
            if not os.path.exists(local_dir):
                os.makedirs(local_dir)
            out_file = open(local_dir + '/' + local_xml_file, 'wb')
            out_file.write(xml_file_content)
            in_file.close()
            out_file.close()
        else:
            dtNow = datetime.datetime.now().strftime("%m-%d-%Y %I.%M.%S %p")
            
            local_dir = xml_file[:xml_file.find('.xml')]
            local_xml_file = local_dir + ' - ' + dtNow + xml_file[xml_file.rfind('.'):]
            csv_file = local_dir + ' - ' + dtNow + '.csv'
            print "\nCopying %s to new directory\n" % local_xml_file
            in_file = open(xml_file, 'rb')
            xml_file_content = in_file.read()
            if not os.path.exists(local_dir):
                os.makedirs(local_dir)
            out_file = open(local_dir + '/' + local_xml_file, 'wb')
            out_file.write(xml_file_content)
            in_file.close()
            out_file.close()
            
            
        print "\nGenerating preview of XML structure...\n"
        xml_row = iterTag(local_dir + '/' + local_xml_file)
        
        exclusions = raw_input('\nWhich XML element(s) should be excluded from the CSV file output? List element(s) separated by commas (,).\n\n')
        lsExclusions = string.split(exclusions, ',')
        
        print "\nConverting %s to %s based on '%s' as row identifier...\n" % (local_xml_file, csv_file, xml_row)
        converter = xml2csv(local_dir + '/' + local_xml_file, local_dir + '/' + csv_file, encoding="utf-8")
        converter.convert(tag=xml_row,ignore=lsExclusions)
        print "\n%s ---> %s -- Conversion Successful!\n" % (local_xml_file, csv_file)
    
    main()
