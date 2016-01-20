#! /usr/bin/python
#-------------------------------------------------------------------------------
# Name:     make_thumbnails.py
# Purpose:  LandsatFACT application script that builds thumbnails
#           for landsat scenes and saves them to Amazon S3
# Author:   LandsatFACT Project Team
#           support@landsatfact.com
'''This code was developed in the public domain.  This code is provided as is, without warranty of any kind,
 express or implied, including but not limited to the warranties of
 merchantability, fitness for a particular purpose and noninfringement.
 In no event shall the authors be liable for any claim, damages or
 other liability, whether in an action of contract, tort or otherwise,
 arising from, out of or in connection with the software or the use or
 other dealings in the software.'''
#-----------------------------------------------------------------------------

from PIL import Image
import io
import os
import json
import urllib2
import boto3
import botocore
import psycopg2

thumb_size = 400, 400
# low-level AWS client
s3_client = boto3.client('s3')
# high-level AWS client
s3 = boto3.resource('s3')
thumbnail_bucket = s3.Bucket('landsat-thumbnails')
config_path = '../../make_thumbnails_config.json'
with open(config_path) as config_file:
    data = json.load(config_file)
db_config = data['db']
conn = psycopg2.connect(**db_config)
cur = conn.cursor()

# get all scene ids with browse urls from db
cur.execute(
    "SELECT metadata.scene_id, metadata.browse_url "+
        "FROM landsat_metadata AS metadata, wrs2_codes AS wrs "+
        "WHERE substring(metadata.scene_id, 4, 6) = wrs.wrs2_code;"
)
# keys are scene ids, values are browse urls
scene_urls = dict(cur.fetchall())
cur.close()
conn.close()

scene_ids_db = scene_urls.keys()
# strip '.jpg' from s3 scene ids
scene_ids_s3 = [ Key.key.split('.')[0] for Key in thumbnail_bucket.objects.all() ]
# make a list of all scene ids that don't already have thumbnails
missing_thumbs = [ scene_id for scene_id in scene_ids_db if scene_id not in scene_ids_s3 ]

for scene_id in missing_thumbs:
    make_thumbnail(scene_id, scene_urls[scene_id])

"""
# Generate a thumbnail for a landsat scene and upload it to s3.
# @param the scene ID of the image
# @param the URL of the image on USGS
"""
def make_thumbnail(scene_id, browse_url):
    im_stream = urllib2.urlopen(browse_url)
    # image data must be wrapped in a file object so PIL can open it
    im = Image.open(io.BytesIO(im_stream.read()))
    # resize the image in place, retaining the aspect ratio
    im.thumbnail(thumb_size)
    im.save(scene_id +'.jpg')
    # high-level s3 client is object-based, use low-level client instead for file-based upload
    s3_client.upload_file(Filename=scene_id+'.jpg', Bucket='landsat-thumbnails', Key=scene_id+'.jpg')
    os.remove(scene_id+'.jpg')

