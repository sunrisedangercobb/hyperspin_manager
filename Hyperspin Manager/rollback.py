#!/usr/bin/python

import os
import sys
import yaml


def Main(args=None):

  rollback_file = args[0]

  print rollback_file

  with open(rollback_file) as info:
    info_dict = yaml.load(info)


  #print top level keys and the values (in a readable way)
  for k,v in info_dict.iteritems():

    src = v[0]['src']
    dst = v[1]['dst']

    print 'src: %s' % src
    print 'dst: %s' % dst
    print

    os.rename(src, dst)


if __name__ == '__main__':
  Main(sys.argv[1:])