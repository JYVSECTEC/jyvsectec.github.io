#!/usr/bin/env python3
'''
PHR-model awesome link scraper
'''

import os
import json
import argparse
import logging

def scrape(options):

  def folder_start_with(folder_name):
    for x in blacklist_folders:
      if folder_name.startswith(x):
        return False
      else:
        return True

  i = 0
  j = 0
  markdown_array = []
  blacklist_files = ['README.md', '.gitignore', '.gitkeep']
  blacklist_folders = ['.git']

  try:
      for root, directories, files in os.walk(options.source, topdown=True):
        temp_root = root.split(options.source)
        temp_root[1] = (temp_root[1].lstrip('/'))

        if (folder_start_with(temp_root[1]) and root != options.source):
          markdown_array.append({'id': '{}'.format(i+1), 'name': temp_root[1], 'children': [] })

          for name in files:
            if (not name in str(blacklist_files)):
              temp_file = name.split('.')
              temp_url = ('{}/{}/{}'.format(options.md_base,temp_root[1], name))
              markdown_array[i]['children'].append({'id': '{}-{}'.format(i+1,j+1), 'name': temp_file[0].capitalize(), 'title': temp_root[1], 'raw_url': temp_url })
              j += 1
          i += 1

      logging.info('Found {} folders'.format(len(markdown_array)))

      return markdown_array

  except ( ValueError, IndexError, KeyError, OSError ) as error:
    raise error


def inject(markdown_array, options):

  with open(options.phr_file, 'r+') as in_f:
    template = in_f.read()
    template = template.replace('[JSON_LINKS_PLACEHOLDER]', json.dumps(markdown_array))

    if (options.output):
      # Create a new HTML file
      logging.info('Output file: {}'.format(options.output.name))
      print(template, file=options.output)
    else:
      # Write to current HTML file
      logging.info('Injecting JSON to {} file'.format(options.phr_file))
      in_f.seek(0)
      in_f.write(template)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('phr_file', help='phr.html file location')
  parser.add_argument('-s', '--source', default='.', help='Awesome links source folder location')
  parser.add_argument('-p', '--print', action='store_true', help='Print JSON to console')
  parser.add_argument('-l', '--logging', action='store_true', help='Set logging level to INFO')
  parser.add_argument('-m', '--md-base', default='https://raw.githubusercontent.com/JYVSECTEC/PHR-model-links/main', help='PHR-model links list markdown base url')
  parser.add_argument('-o', '--output', type=argparse.FileType('w'), help='Output file name')
  options = parser.parse_args()

  if (options.logging):
    logging.basicConfig(level=logging.INFO)

  logging.info('PHR-model file: {}'.format(options.phr_file))
  logging.info('Links folder location: {}'.format(options.source))
  logging.info('Markdown base url: {}'.format(options.md_base))
  
  try:
    if (options.print):
      # Print JSON to console
      print(json.dumps(scrape(options), indent=4))

    else:
      # Inject JSON to phr model html
      inject(scrape(options), options)

  except Exception as error:
    logging.error(error)
    

if __name__ == '__main__':
  main()