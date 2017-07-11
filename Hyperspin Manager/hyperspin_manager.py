#!/usr/bin/python

"""
Hyperspin Manager

This is a light weight program designed to help me not waste 100's of hours renaming things.
This is very much a beta program, USE AT YOUR OWN RISK. I have built this to be a somewhat safe
tool, so if you actually inspect the data you should be fine. I also included rollback
functionality to ensure you can go back.

I currently don't allow for different output paths as this is meant to run against multiple dirs.
This is meant to handle the little things that annoy me most and provide a bit of insight
into the state of each of the systems without me having to dig through tons of dirs.

Version: 0.01
"""

__author__ = 'Sunrise Cobb <sunrisedangercobb@gmail.com>'


import os
import re
import sys
import zlib
import getopt
import fnmatch

import xml.etree.ElementTree


# static/support paths
PATH_DATABASE = 'data/database/'
PATH_ROLLBACK = 'data/rollback/'
PATH_CATALOG = 'data/catalog/'
PATH_MISSING = 'data/missing/'
PATH_EXCLUDE = 'data/exclude/'

# Stupid shit cause I needed to determine which of the files found was a rom.  This was the easiest.
ROM_PATHING_CHECKS = ['roms', 'Roms', 'rom', 'Rom', 'ROM']


############# support #############
def XmlToListOfDicts(xml_file):
  """
  Takes xml_file and returns a list of dicts

  Args: xml_file(file)
  Returns: list[dicts]
  """

  # Set up our tree
  xml_tree = xml.etree.ElementTree.parse(xml_file).getroot()

  # Create a list to put our game dictionaries into.
  game_list = []

  # Now let's loop over and stuff all our games into dictionaries and put em in our list
  for game in xml_tree.findall('game'):

    # Ok so let's build a dictionary and stuff it all in there
    game_dict = {}

    game_dict['name'] = game.get('name')
    game_dict['description'] = game.find('description').text
    game_dict['cloneof'] = game.find('cloneof').text
    game_dict['crc'] = game.find('crc').text
    game_dict['manufacturer'] = game.find('manufacturer').text
    game_dict['year'] = game.find('year').text
    game_dict['genre'] = game.find('genre').text
    game_dict['rating'] = game.find('rating').text
    game_dict['enabled'] = game.find('enabled').text

    # Now let's add it to our list, cause lists of dictionaries are easy to work with
    game_list.append(game_dict)

  return game_list


def FileFinder(pattern, input_path):
  """
  Recursively searches directories and finds matches the pattern provided, case insensitive.

  Args: pattern(str), input_path(str)
  Returns: list[str]
  """

  # set up the result
  result = []

  for root, dirs, files in os.walk(input_path):
    for name in files:
      if (fnmatch.fnmatch(str.lower(name), str.lower(pattern)) or fnmatch.fnmatch(name, pattern)):
        if not name.startswith('.'):
          result.append(os.path.join(root, name))

  return result


def ReturnFileNameExtensionBasePath(file_match):
  """
  Breaks apart a path into its parts and returns a dictionary.

  Args: file_match(file)
  Returns: dict
  """
  # we are actually going to return a dict here
  file_parts = {}

  # lets split it up
  filename, file_extension = os.path.splitext(file_match)
  file_base_path = os.path.dirname(file_match)
  file_name = os.path.basename(filename)

  file_parts['file_name'] = file_name
  file_parts['file_base_path'] = file_base_path + '/'
  file_parts['file_extension'] = file_extension

  return file_parts


def GetSearchName(name):
  """
  Does some parsing and returns a string set up for globbing searches.

  Args: name(string)
  Returns: name(string)
  """
  # remove any special chars and replace em with spaces
  name = re.sub('[?|$|.|!|,|:|;|%|@|#|&|*|<|>|_| - |-|+|=|\']', ' ', name)

  # now split and join on with spaces to get single spaces
  name = ' '.join(name.split())

  # strip things down
  name = re.sub('\(.*?\)', '', name)
  name = re.sub('[.*?]', '', name)
  name = re.sub('\W+',' ', name)
  name = name.rstrip()

  name = '*' + name.replace(' ', '*') + '*'

  return name


def GetMatchName(name):
  """
  Does some parsing and returns a string set up for matching.

  Args: name(string)
  Returns: name(string)
  """

  # here is where we handle misc issues
  name = str.lower(name)

  name = name.replace('\'s', 's')

  # remove any special chars and replace em with spaces
  name = re.sub('[?|$|.|!|,|:|;|%|@|#|&|*|<|>|_| - |-|+|=|\']', ' ', name)

  # now split and join on with spaces to get single spaces
  name = ' '.join(name.split())

  # strip things down
  name = re.sub('\(.*?\)', '', name)
  name = re.sub('[.*?]', '', name)
  name = re.sub('\W+',' ', name)
  name = name.rstrip()

  return name


def GetMatchingFiles(game, input_path, system_name):
  """
  Actually does some matching on all the files found. Could be better but does pretty well.

   - matches system_name to file_base_path
   - matches the len of match name
   - matches the parts of match name

  Args: game(dict), input_path(string), system_name(string)
  Returns: dict (with files added to game_dict as well)
  """

  # So lets put these into a list of dicts as well...then stuff em into our original dict!
  matching_file_list = []

  # lets go get our search name
  game_search_name = GetSearchName(game['name'])

  # now lets go see what we find
  file_matches_found = FileFinder(game_search_name, input_path)

  # print it
  if file_matches_found:

    # Go get our match name.
    game_match_name = GetMatchName(game['name'])

    # We are going to use these to actually do the matching for now, simple but pretty effective
    game_match_name_parts = game_match_name.split()
    game_match_name_parts_count = len(game_match_name.split())

    for file_match in file_matches_found:

      # Go and split up the full path into the parts we require, then grab our match name as well.
      file_match_dict = ReturnFileNameExtensionBasePath(file_match)
      file_match_name = GetMatchName(file_match_dict['file_name'])

      # We are going to use these to actually do the matching for now, simple but pretty effective
      file_match_name_parts = file_match_name.split()
      file_match_name_parts_count = len(file_match_name.split())


      if (game_match_name_parts_count == file_match_name_parts_count and game_match_name_parts == file_match_name_parts and system_name in file_match_dict['file_base_path']):
        matching_file_list.append(file_match_dict)

    # now lets put em in the dict
    game['files'] = matching_file_list

  return game


def GetDatabaseAndFileInfo(database, input_path):
  """
  Checks to ensure we have a actual file and an actual input_path.
  Reads the database and returns the game_list.

  Args: database(string/file), input_path(string)
  Returns: game_list
  """
  print '\nparsing database and retrieving files...'
  # Let's make sure we have valid files and directories
  if not os.path.isfile(database):
    Usage('invalid file: %s' % database)

  if not os.path.isdir(input_path):
    Usage('invalid directory: %s' % input_path)

  # Let's figure out what system we are dealing with and get all the games in the database.
  system_name = os.path.splitext(os.path.basename(database))[0]
  game_list = XmlToListOfDicts(database)

  # if we are able to extract both of these items lets move forward
  if (system_name and game_list):

    for game in game_list:

      game_index = game_list.index(game)
      game_with_file_matches = GetMatchingFiles(game, input_path, system_name)
      game_list[game_index] = game_with_file_matches

  return game_list


def ComputeCrc(game_rom):
  """
  Computes the CRC hash (not currently used).

  Args: game_rom(string/file)
  Returns: crc(string/hash)
  """
  prev = 0

  for line in open(game_rom,"rb"):
      prev = zlib.crc32(line, prev)

  crc = "%X"%(prev & 0xFFFFFFFF)
  print len(crc)
  if (len(crc) == 7):
    crc = '0' + crc

  return crc

  # this is faster
  # return "%X"%(zlib.crc32(open(game_rom,"rb").read()) & 0xFFFFFFFF)


############# actions #############
def CreateCatalog(database, game_list, mandatory_options):
  """
  Creates a media catalog.  This is a simple yaml file that shows what files you have
  with each and every game in your database.  The idea is to have a view into what is
  still needed to complete each collection.

  Args: database(string/file), game_list(list[dicts]), mandatory_options(list[str])
  Outputs: yaml formatted data
  Returns: None
  """

  global PATH_CATALOG

  # Let's get the system name again so we can use that as our output name
  system_name = os.path.splitext(os.path.basename(database))[0]

  final_output_path = PATH_CATALOG + system_name + '.yaml'

  # ghetto way of templating but doesn't require external libraries
  catalog = ''

  for game in game_list:

    if 'files' in game:

      catalog += '%s:\n' % game['name']

      for f in game['files']:
        catalog += '  - %s: %s%s\n' % (f['file_base_path'].split('/')[-2], f['file_name'], f['file_extension'])

    catalog += '\n'

  if ('-c' in mandatory_options):
    print 'generating media catalog...'
    open(final_output_path , 'w').write(catalog)
    print 'file created: %s' % final_output_path
  else:
    print catalog


def CreateMissing(database, game_list, mandatory_options):
  """
  Creates a missing list.  This is a simple yaml file that shows what rom files you have
  with each and every game in your database.  The idea is to have a view into what is
  still needed to complete each collection.

  Args: database(string/file), game_list(list[dicts]), mandatory_options(list[str])
  Outputs: yaml formatted data
  Returns: None
  """

  global PATH_MISSING
  global ROM_PATHING_CHECKS

  # Let's get the system name again so we can use that as our output name
  system_name = os.path.splitext(os.path.basename(database))[0]

  final_output_path = PATH_MISSING + system_name + '.yaml'

  # ghetto way of templating but doesn't require external libraries
  missing = ''
  missing = '%s:\n' % system_name

  for game in game_list:

    if 'files' in game:
      game_found = False

      for f in game['files']:
        for check in ROM_PATHING_CHECKS:
          if check in f['file_base_path']:
            game_found = True
            break

      if not game_found:
        missing += '  - %s\n' % game['name']
    else:
      missing += '  - %s\n' % game['name']


  if ('-c' in mandatory_options):
    print 'generating missing list...'
    open(final_output_path , 'w').write(missing)
    print 'file created: %s' % final_output_path

  else:
    print missing


def RenameFiles(database, game_list, mandatory_options):
  """
  Runs a mass rename accross all your files, matching...somewhat intelligently. This
  is meant to be run when your ready to rock n roll and have visually inspected the
  stdout. Just in case with each run a rollback file is created to ensure that you don't
  completely destroy things

  Args: database(string/file), game_list(list[dicts]), mandatory_options(list[str])
  Outputs: yaml formatted data
  Returns: None
  """

  global PATH_ROLLBACK

  # Let's get the system name again so we can use that as our output name
  system_name = os.path.splitext(os.path.basename(database))[0]
  final_output_path = PATH_ROLLBACK + system_name + '.yaml'

  # If we commit let's rename some files
  if ('-c' in mandatory_options):
    print 'renaming files...\n'
    # Set up our rollback file.
    rollback = ''

    for game in game_list:
      if 'files' in game:
        for f in game['files']:
          if (game['name'] != f['file_name']):
            src = '%s%s%s' % (f['file_base_path'], f['file_name'], f['file_extension'])
            dst = '%s%s%s' % (f['file_base_path'], game['name'], f['file_extension'])
            print 'path: %s' % (f['file_base_path'])
            print 'src: %s\ndst: %s\n' % (f['file_name'], game['name'])

            os.rename(src, dst)

            # Let's add everything to the rollback
            rollback += '%s%s%s:\n' % (f['file_base_path'], f['file_name'], f['file_extension'])
            rollback += '  - src: %s\n' % dst
            rollback += '  - dst: %s\n\n' % src

    open(final_output_path , 'w').write(rollback)
    print 'file created: %s' % final_output_path

  else:

    for game in game_list:
      if 'files' in game:
        for f in game['files']:
          if (game['name'] != f['file_name']):
            src = '%s%s%s' % (f['file_base_path'], f['file_name'], f['file_extension'])
            dst = '%s%s%s' % (f['file_base_path'], game['name'], f['file_extension'])
            print 'path: %s' % (f['file_base_path'])
            print 'src: %s\ndst: %s\n' % (f['file_name'], game['name'])


def Usage(error=None, perform_sys_exit=True):
  """ Basic usage """

  # If we are going to print usage and (maybe) exit...
  if error:
    print '\nERROR: %s' % error
    status_code = 1
  else:
    status_code = 0

  # the nicely formatted usage message
  print ''
  print 'USAGE: %s  -d </path/to/database.xml> -i </path/to/media/> -g ' % sys.argv[0]
  print '  -c, --commit          Will commit any action.'
  print '  -d, --database        The database file (must be xml). </path/to/file.xml>'
  print '  -g, --generate        Set to trigger file generation. < missing | catalog >'
  print '  -i, --input           The search path.'
  print '  -r, --rename          Set this to trigger the rename action.'
  print '  -?, --help            Usage\n'

  # If we want to exit, do so
  if perform_sys_exit:
    sys.exit(status_code)



def Main(args=None):


  # Variables
  mandatory_options = ''
  options= {}

  # get options
  long_options = ['help', 'commit', 'database=', 'generate=', 'input=', 'rename']

  try:
    (options, args) = getopt.getopt(args, '?cd:g:i:r', long_options)
  except getopt.GetoptError, err:
    Usage(err)


  # Process out CLI options
  for (option, value) in options:
    # Help
    if option in ('-?', '--help'):
      Usage()

    # Actually commit the rename.
    elif option in ('-c', '--commit'):
      mandatory_options += '-c'

    # Define which database to read in
    elif option in ('-d', '--database'):
      if (value != '' and not value.startswith('-')):
        database = value
        mandatory_options += '-d'

    # Define which file to generate
    elif option in ('-g', '--generate'):
      if (value != '' and not value.startswith('-')):
        generate = value
        mandatory_options += '-g'

    # Define the path to data
    elif option in ('-i', '--input'):
      if (value != '' and not value.startswith('-')):
        input_path = value
        mandatory_options += '-i'

    # Define the path to data
    elif option in ('-r', '--rename'):
      mandatory_options += '-r'


  if ('-c' not in mandatory_options):
    print
    print '###########################################################'
    print '####################   DRY RUN   ##########################'
    print '###########################################################'
  else:
    print
    print '###########################################################'
    print '####################   GO TIME   ##########################'
    print '###########################################################'

  # All the options that are going to require a database, path, files on disk.
  if ('-d' in mandatory_options and '-i' in mandatory_options):

    # gets all games in database and finds the files on disk
    game_list = GetDatabaseAndFileInfo(database, input_path)


    if ('-g' in mandatory_options and (generate == 'catalog')):

      CreateCatalog(database, game_list, mandatory_options)

    if ('-g' in mandatory_options and (generate == 'missing')):

      CreateMissing(database, game_list, mandatory_options)

    if ('-r' in mandatory_options):

      RenameFiles(database, game_list, mandatory_options)

  print '\n\n'

if __name__ == '__main__':
  Main(sys.argv[1:])

