import time
import re

import numpy as np
import simplejson as json
import matplotlib.pyplot as plt
import scipy.misc

LEFT = 25.469047
RIGHT = 26.711313
UP = 44.820570
DOWN = 44.113623
STEP_HOR = 0.000135 * 3 * 2.5
STEP_VER = 0.0001 * 3 * 2.5
LENGTH = int((RIGHT - LEFT) / STEP_HOR)
HEIGHT = int((UP - DOWN) / STEP_VER)


def coords_valid(lat, lng):
  return (DOWN <= lat < UP) and (LEFT <= lng < RIGHT)

def coord_to_index(lat, lng):
  i = int((lat - DOWN) / STEP_VER)
  j = int((lng - LEFT) / STEP_HOR)
  return (HEIGHT - i, j)


def index_ride(ride_dict):
  for p in range(len(ride_dict['latlng'])):
    lat, lng = ride_dict['latlng'][p]
    velocity = ride_dict['velocity_smooth'][p]

    if not coords_valid(lat, lng):
      continue
    if velocity < 2: # that's 7 kmph
      continue

    i, j = coord_to_index(lat, lng)
    if (i, j) not in point_buckets:
      point_buckets[(i, j)] = []
    point_buckets[(i, j)].append(velocity)


FREQ_MIN = 5.0
FREQ_MAX = 100.0
SPEED_RED = 25.0
SPEED_GREEN = 35.0
RED = np.array([255, 0, 0])
GREEN = np.array([0, 255, 0])
WHITE = np.array([255, 255, 255])

def list_to_color(speed_list):
  # few points, render as white
  if len(speed_list) < FREQ_MIN:
    return [255, 255, 255]

  speed = np.percentile(speed_list, 80)
  speed = speed * 3.6 # convert mps to kmph
  ratio = (max(SPEED_RED, min(speed, SPEED_GREEN)) - SPEED_RED) \
      / (SPEED_GREEN - SPEED_RED)

  # this is the color generated based on speed
  color = RED * (1 - ratio) + GREEN * ratio

  # alpha gradient
  gradient = min(len(speed_list), FREQ_MAX) / FREQ_MAX
  color = color + (WHITE - color) * (1 - gradient)
  color = color.astype(np.uint8)
  return color

point_buckets = {}
f = open('ride_data.json', 'r')
while True:
  row = f.readline()
  if not row:
    break

  try:
    ride = json.loads(row)
  except:
    continue

  ride = ride[1]
  if not ride or 'latlng' not in ride or 'velocity_smooth' not in ride:
    continue

  index_ride(ride)

f.close()


image = np.zeros((HEIGHT + 1, LENGTH + 1, 3), dtype=np.uint8)
image += 255

for k, v in point_buckets.iteritems():
  image[k[0], k[1], :] = list_to_color(v)

plt.imshow(image)
plt.show()

scipy.misc.imsave('chart.jpg', image)