# Try to find an optimization to cut flood area

import pymongo
from pymongo import MongoClient

from shapely.geometry import shape
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon

import z3
from itertools import product


class Flood_Cut:

	def __init__(self):
		self.client = MongoClient()
		self.db = self.client['repo']

		self.flood = None
		self.zones = None

		self.overlapping_zones = {}

		self.area_threshold = None
		self.wall_threshold = None

	def start(self):
		self.area_threshold = 0.8
		self.wall_threshold = 0.3

		self._generate_overlapping_zones()
		# answer = self._find_match_result()

	######## private functions ########

	def _get_36_flood(self) -> None:
		# flood area is a multipolygon consisting 217 polygons
		# list of <class 'shapely.geometry.polygon.Polygon'>
		flood_collection = self.db['dezhouw_ghonigsb.sea_level']
		flood_geometry = flood_collection.find()[3]\
										 ['thirty_six_inch_sea_level_rise_10_pct_annual_flood']\
										 ['features'][0]['geometry']
		flood = [x.buffer(0) for x in shape(flood_geometry).buffer(0).geoms]
		self.flood = MultiPolygon(flood)

	def _get_zones(self) -> None:
		# 1649 different zones, but they don't have names
		# Inside the 1649 zones, 12 zones' shapes are multipolygon
		zones_collection = self.db['dezhouw_ghonigsb.zoning_subdistricts']
		zones_info = zones_collection.find()[0]['neighborhood']['features']
		self.zones = []
		for each_zone in zones_info:
			if each_zone['geometry']['type'] == 'MultiPolygon':
				zone = [x.buffer(0) for x in shape(each_zone['geometry']).buffer(0).geoms]
				self.zones.append(MultiPolygon(zone))
			elif each_zone['geometry']['type'] == 'Polygon':
				self.zones.append(shape(each_zone['geometry']))

	def _generate_overlapping_zones(self) -> None:
		# 408 different zones overlapping with the flood area
		# Insert these result data into MongoDB
		# overlapping_zones = self.db['overlapping_zones']
		# overlapping_zones.delete_many({})
		self._get_36_flood()
		self._get_zones()
		self.overlapping_zones = {}
		count = 0
		for z in self.zones:
			try:
				if z.intersects(self.flood):

					overlapping, length = _get_overlapping_and_length(z, self.flood)

					# overlapping_list = []
					# for a in overlapping:
					# 	x, y = a.exterior.coords.xy
					# 	overlapping_list.append(list(zip(x, y)))

					# insertData = {
					# 	"id": count,
					# 	"overlapping zones": overlapping_list,
					# 	"flood intersect length": length
					# }
					# overlapping_zones.insert_one(insertData)

					self.overlapping_zones[count] = {
						"id": count,
						"overlapping zones": overlapping,
						"flood intersect length": length
					}

					count += 1
					print(count)
			except:
				pass

	def _find_match_result(self):
		self._generate_overlapping_zones()
		count = len(self.overlapping_zones.keys())
		S = list(product(*[{0,1}]*count))
		answer = []
		for s in S:
			zone = None
			intersect_length = 0
			for x in range(count):
				if s[x] == 1:
					if zone == None:
						zone = self.overlapping_zones[x]["overlapping zones"]
					else:
						zone = _sum_two_multipolygons(zone,\
								 self.overlapping_zones[x]["overlapping zones"])
					intersect_length += self.overlapping_zones[x]["flood intersect length"]
			total_length = _get_perimeter_of_multipolygon(zone)
			wall_length = total_length - intersect_length
			area = _get_area_of_multipolygon(zone)

			if (area >= self.area_threshold) and (wall_length <= self.wall_threshold):
				answer.append(s)

		return answer


######## Static Methods #######

def _subtract_multipolygon_from_multipolygon(xs, ys) -> MultiPolygon:
	outmulti = []
	for p1 in xs:
		for p2 in ys:
			if p1.intersects(p2) == True:
				nonoverlap = (p1.symmetric_difference(p2)).difference(p2)
				outmulti.append(nonoverlap)
			else:
				outmulti.append(p1)
	return MultiPolygon(outmulti)

def _subtract_multipolygon_from_polygon(x, ys) -> MultiPolygon:
	outmulti = []
	for p in ys:
		if x.intersects(p) == True:
			nonoverlap = (x.symmetric_difference(p)).difference(p)
			outmulti.append(nonoverlap)
		else:
			outmulti.append(x)
	return MultiPolygon(outmulti)

def _subtract_multipolygon(a, ys) -> MultiPolygon:
	if type(a) == Polygon:
		return _subtract_multipolygon_from_polygon(a, ys)
	else:
		return _subtract_multipolygon_from_multipolygon(a, ys)

def _sum_two_multipolygons(x, y):
	return x.union(y)

def _sum_list_multipolygons(xs):
	if len(xs) == 0:
		return None
	outmulti = xs[0]
	for x in xs[1:]:
		outmulti = outmulti.union(x)
	return outmulti

def _get_perimeter_of_multipolygon(x) -> float:
	if x == None:
		return 0.0
	return x.length

def _get_overlapping_and_length(xs, ys):
	part1 = _subtract_multipolygon(xs, ys)
	part2 = _subtract_multipolygon(xs, part1)
	perimeter = _get_perimeter_of_multipolygon(xs)
	perimeter1 = _get_perimeter_of_multipolygon(part1)
	perimeter2 = _get_perimeter_of_multipolygon(part2)
	length = (perimeter1 + perimeter2 - perimeter) / 2
	return (part2, length)

def _get_area_of_multipolygon(x) -> float:
	if x == None:
		return 0.0
	return x.area

if __name__ == '__main__':
	f = Flood_Cut()
	f.start()