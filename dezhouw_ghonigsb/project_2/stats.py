# stats.py
# created on April 17, 2019

import urllib.request
import json
import dml
import prov.model
import datetime
import uuid
import ssl
import sys
import traceback
import csv
import xmltodict
import io
import scipy

class stats(dml.Algorithm):
	contributor = "dezhouw_ghonigsb"
	reads       = ["flood","transportation"]
	writes      = ["stats"]


	@staticmethod
	def execute(trial = False):
		startTime = datetime.datetime.now()

		# Set up the database connection.
		client = dml.pymongo.MongoClient()
		repo   = client.repo
		repo.authenticate("dezhouw_ghonigsb", "dezhouw_ghonigsb")

		# Drop all collections
		collection_names = repo.list_collection_names()
		for collection_name in collection_names:
			repo.dropCollection(collection_name)

		repo["dezhouw_ghonigsb.transportation"]

    #get transportion and flood data from db
		trans = []
		flood = ...
    
    #list to be built 
		vals = [] #({1,0} for in flood, num of traffic)

		for i in range(len(trans)):
			if trans[i].loc in flood:
				vals.append(1,trans[i].daily)
			else:
				vals.append(0, trans[i].daily)

		x = [xi for (xi, yi) in vals]
		y = [yi for (xi, yi) in vals]
    
    #correlation
		corr = scipy.stats.pearsonr(x, y)


######



	@staticmethod
	def provenance(doc = prov.model.ProvDocument(), startTime = None, endTime = None):
		client = dml.pymongo.MongoClient()
		repo   = client.repo
		repo.authenticate("dezhouw_ghonigsb", "dezhouw_ghonigsb")


		repo.logout()

		return doc




########



if __name__ == '__main__':
	try:
		print(stats.execute())
		doc = stats.provenance()
		print(doc.get_provn())
		print(json.dumps(json.loads(doc.serialize()), indent=4))
	except Exception as e:
		traceback.print_exc(file = sys.stdout)
	finally:
		print("Safely close")
