import sys
import requests
from optparse import OptionParser
#from xmlutils.xml2csv import xml2csv
import xml.etree.ElementTree as ET
import os
import datetime
import string
import pyprind
import progressbar as pb
import time
import codecs


## modified XML to CSV class
"""
	xml2csv.py
	Kailash Nadh, http://nadh.in
	October 2011
	License:		MIT License
	Documentation:	http://nadh.in/code/xmlutils.py
"""

class xml2csv_symmetrize:

	def __init__(self, input_file, output_file, encoding='utf-8'):
		"""Initialize the class with the paths to the input xml file
		and the output csv file
		Keyword arguments:
		input_file -- input xml filename
		output_file -- output csv filename
		encoding -- character encoding
		"""

		self.output_buffer = []
		self.output = None

		# open the xml file for iteration
		self.context = ET.iterparse(input_file, events=("start", "end"))

		# output file handle
		try:
			self.output = codecs.open(output_file, "w", encoding=encoding)
		except:
			print("Failed to open the output file")
			raise

	def convert(self, tag="item", delimiter=",", ignore=[], noheader=False,
				limit=-1, buffer_size=1000, headers_list=[], row_count=0):

		"""Convert the XML file to SQL file
			Keyword arguments:
			tag -- the record tag. eg: item
			delimiter -- csv field delimiter
			ignore -- list of tags to ignore
			limit -- maximum number of records to process
			buffer -- number of records to keep in buffer before writing to disk
			Returns:
			number of records converted,
		"""

		# get to the root
		event, root = self.context.next()

		items = []
		header_line = []
		field_name = ''

		tagged = False
		started = False
		n = 0

		if len(headers_list) != 0:
			symmetrize = True
		else:
			symmetrize = False

		# If size is known, use % complete Progress Bar, else use animated indicator
		if row_count == 0:
			pInd = ProgressIndicator(label='Converted %(value)d rows - ',maxval=1000000)
		else:
			pBar = pyProgressBar(duration=row_count,indicator='.',monitor=True,width=50,title='Converting XML to CSV')


		# iterate through the xml
		for event, elem in self.context:
			#print "------ %d ------" % n
			#print "event = %s" % str(event)
			#print "tag = %s" % str(elem.tag)
			# if elem is an unignored child node of the record tag, it should be written to buffer
			should_write = elem.tag != tag and started and elem.tag not in ignore
			#print "should_write = %s" % str(should_write)
			# and if a header is required and if there isn't one
			should_tag = not tagged and should_write and not noheader
			#print "should_tag = %s" % str(should_tag)

			if event == 'start':
				if elem.tag == tag and not started:
					started = True
					#print "started = %s" % str(started)
				elif should_tag:
					# if elem is nested inside a "parent", field name becomes parent_elem
					field_name = '_'.join((field_name, elem.tag)) if field_name else elem.tag
					#print "field_name = %s" % str(field_name)

			else:
				if should_write:
					if should_tag:
						if symmetrize and len(header_line) == 0:
							header_line = headers_list
						elif not symmetrize:
							header_line.append(field_name)  # add field name to csv header
						#print "header_line = %s" % str(header_line)
						# remove current tag from the tag name chain
						field_name = field_name.rpartition('_' + elem.tag)[0]
					if symmetrize:
						if len(items) == 0:
							for i in range(len(headers_list)):
								items.append('')
						try:
							#print "index = %d" % headers_list.index(elem.tag)
							if items[headers_list.index(elem.tag)] == '':
								items[headers_list.index(elem.tag)] = str('' if elem.text is None else elem.text.strip().replace('"', r'""'))
							else:
								items[headers_list.index(elem.tag)] = ';'.join((items[headers_list.index(elem.tag)],str('' if elem.text is None else elem.text.strip().replace('"', r'""'))))
						except:
							#print "''%s' is not part of the row" % elem.tag
							pass
					else:
						items.append('' if elem.text is None else elem.text.strip().replace('"', r'""'))
					#print "items = %s" % str(items)
					#a = raw_input()


				# end of traversing the record tag
				elif elem.tag == tag and len(items) > 0:
					# csv header (element tag names)
					if header_line and not tagged:
						self.output.write(delimiter.join(header_line) + '\n')
					tagged = True

					# send the csv to buffer
					self.output_buffer.append(r'"' + (r'"' + delimiter + r'"').join(items) + r'"')
					items = []
					n += 1
					if row_count == 0:
						pInd.update(n)
					else:
						pBar.update()

					# halt if the specified limit has been hit
					if n == limit:
						if row_count == 0:
							pInd.maxval = n
							pInd.finish()
						else:
							pBar.stop()
						break

					# flush buffer to disk
					if len(self.output_buffer) > buffer_size:
						self._write_buffer()

				elem.clear()  # discard element and recover memory

		self._write_buffer()  # write rest of the buffer to file
		self.output.close()

		# stop the progress indicator or bar
		if row_count == 0:
			pInd.maxval = n
			pInd.finish()
		else:
			pBar.stop()

		return n


	def _write_buffer(self):
		"""Write records from buffer to the output file"""

		self.output.write('\n'.join(self.output_buffer) + '\n')
		self.output_buffer = []


## Function to display a progress bar. Set a variable to the function and
## get a bar on which you can call .update() to show progress
def pyProgressBar(duration=0, indicator='.', monitor=False, width=50, title='Progress...'):
	bar = pyprind.ProgBar(duration, bar_char=indicator, monitor=monitor, width=width, title=title)
	return bar

def ProgressIndicator(label, maxval=1000000):
	widgets = [pb.FormatLabel(label), pb.BouncingBar(marker=pb.RotatingMarker())]
	pind = pb.ProgressBar(widgets=widgets,maxval=maxval).start()
	return pind


## Functions for printing the XML structure and for the Symmetrize operation

def perf_func(elem, func, level=0, xml_struct=[], dict_tags={}):
	stop = func(elem,level,xml_struct,dict_tags)
	for child in elem:
		#if stop == 1:
		#	break
		perf_func(child, func, level+1, xml_struct, dict_tags)
	return xml_struct, dict_tags


def print_level(elem,level,xml_struct,dict_tags):
	if elem.tag not in dict_tags:
		print '-\t'*level+elem.tag
		dict_tags[elem.tag] = level
	xml_struct.append([level,elem.tag])


def iterTag(path_to_file):
	tree = ET.parse(path_to_file)
	root = tree.getroot()
	xml_struct, dict_tags = perf_func(root, print_level)
	return xml_struct, dict_tags


## Function for executing the Symmetrize operation and for generating an XML preview
def symmetrize(xml_file):
	print "\nGenerating preview of XML structure...\n"
	xml_struct, dictionary_tags = iterTag(xml_file)
	return xml_struct, dictionary_tags


## Function for retrieving arguments from the user

def get_user_input(prompt_message):
	ri = raw_input("\n" + prompt_message + "\n\n")
	return ri


##### Begin the main program  #####

if __name__ == "__main__":
	def main():

		usage = """\n\n
		usage: python xml_to_csv_ignore.py 'input_xml_file_or_URL' 'output_file_name' [options]

		'input_xml_file_or_URL' --> 	input XML file or URL to be converted to CSV
		'output_file_name' -->		output CSV file name. A folder will be created with the same name to house the file

		Options:
		--tag='tag' -->			the xml element that should be used as the basis of rows in the CSV
		--ignore='tag1,tag2,tag#'	the xml element(s) that should be excluded from the CSV file output
		--sample='100' -->		an integer limiting the number of rows in the CSV file output, or 'n' for all rows
		-y -->		  True/False option to symmetrize the XML if records are asymmetrical
		\n\n
		"""

		print usage

		parser = OptionParser(usage, version='1')
		parser.add_option("-t", "--tag", action="store", type="string", dest="tag")
		parser.add_option("-i", "--ignore", action="store", type="string", dest="ignore")
		parser.add_option("-s", "--sample", action="store", type="string", dest="sample")
		parser.add_option("-y", "--symmetrize", action="store_true", dest="symmetrize")
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
			print "\nThis script takes 2 arg. %d args provided.\n" % len(args)
			print usage
			sys.exit(1)

## Get the XML content and move it to the output directory
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
			pInd = ProgressIndicator(label="Downloading file: %(value)dKB - ")
			szb = 0
			for block in response.iter_content(1024):
				if not block:
					break
				handle.write(block)
				szb += 1024
				szk = szb / (1024**2)
				pInd.update(szk)
			handle.close()
			pInd.maxval = szk
			pInd.finish()
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

## Evaluate options and obtain values
		do_symmetrize = False
		xml_struct = []
		dictionary_tags = {}
		headers_list = []

		if options.tag is None:
			xml_struct, dictionary_tags = symmetrize(local_dir + '/' + local_input_file)
			tag_prompt = "Sample of XML structure above.\nWhich XML element should be used as the basis for rows?"
			xml_row = get_user_input(tag_prompt)
		else:
			xml_row = options.tag


		if options.ignore is None:
			ignore_prompt = "Which XML element(s) should be excluded from the CSV file output? List element(s) separated by commas (,)."
			exclusions = get_user_input(ignore_prompt)
			lsExclusions = string.split(exclusions, ',')
		else:
			lsExclusions = string.split(options.ignore, ',')

		if options.sample is None:
			sample_prompt = "If only a sample is desired, enter the max number of rows. For all rows, enter 'n'."
			sample = get_user_input(sample_prompt)
			if sample == 'n':
				sample = None
			else:
				try:
					sample = int(sample)
				except:
					print "Please provide only an integer or 'n' for the sample size."
					sys.exit(1)
		elif options.sample == 'n':
			sample = None
		else:
			try:
				sample = int(options.sample)
			except:
				print "Please provide only an integer or 'n' for the sample size."
				sys.exit(1)

		if options.symmetrize:
			if len(xml_struct) == 0:
				xml_struct, dictionary_tags = symmetrize(local_dir + '/' + local_input_file)
			do_symmetrize = True

		## If Symmetrize option is true, then get things ready for the operation
		if not do_symmetrize:
			xml_struct = []
			dictionary_tags = {}
			headers_list = []
		else:
			try:
				row_level = dictionary_tags[xml_row]
			except:
				row_level = 0

			for hdr in xml_struct:
				if hdr[0] >= row_level+1 and hdr[1] not in headers_list:
					headers_list.append(hdr[1])

			## Number of rows
			all_tags = [item[1] for item in xml_struct]
			row_count = sum(1 for rt in all_tags if rt == xml_row)
			all_tags = []

		if sample is not None:
			row_count = sample
		else:
			try:
				row_count = row_count
			except:
				row_count = 0

		#### Do the conversion from XML to CSV

		print "\nConverting %s to %s based on '%s' as row identifier...\n" % (local_input_file, csv_file, xml_row)

		## Enter status bar
		converter = xml2csv_symmetrize(local_dir + '/' + local_input_file, local_dir + '/' + csv_file, encoding="utf-8")
		converter.convert(tag=xml_row, ignore=lsExclusions, limit=sample, headers_list=headers_list, row_count=row_count)
		print "\n%s ---> %s -- Conversion Successful!\n" % (local_input_file, csv_file)

	main()
