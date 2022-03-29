import json
import csv
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import pyrebase
import os
from natsort import natsorted
from uuid import uuid4
import datetime


class firebase:

    def metadata(self, collectionName, imagesFilePath, csvFilePath, metadataFilePath):

        config = {
            "apiKey": "AIzaSyA1LmnKbBNylMRoAl8A9-dkEGItp3P_tE0",
            "authDomain": "deatris-e42b7.firebaseapp.com",
            "databaseURL": "https://deatris-e42b7-default-rtdb.firebaseio.com",
            "projectId": "deatris-e42b7",
            "storageBucket": "deatris-e42b7.appspot.com",
            "messagingSenderId": "664398826536",
            "appId": "1:664398826536:web:ff0dd1fa3f6a3ac25b391d",
            "measurementId": "G-97N9ZH38F2"
        }
        firebase = pyrebase.initialize_app(config)
        storage = firebase.storage()

        def csv_to_json(csvFilePath, metadataFilePath):

            jsonArray = []

            with open(csvFilePath, encoding='utf-8') as csvf:
                csvReader = csv.DictReader(csvf)
                for row in csvReader:
                    edition = {"edition": row["edition"]}
                    reduced_row = row
                    del reduced_row['edition']
                    keys = list(reduced_row.keys())
                    vals = list(reduced_row.values())
                    key_value = []
                    for i in range(len(keys)):
                        key_value.append({"key": keys[i], "value": vals[i]})
                    atr = {"attributes": key_value}
                    combined_row = {}
                    combined_row.update(edition)
                    combined_row.update(atr)
                    jsonArray.append(combined_row)

            with open(metadataFilePath, 'w', encoding='utf-8') as jsonf:
                jsonString = json.dumps(jsonArray, indent=4)
                jsonf.write(jsonString)

        csv_to_json(csvFilePath, metadataFilePath)

        image_list = natsorted(os.listdir(imagesFilePath))
        j = len(image_list)
        i = 0
        print(str(j) + " images to upload")

        with(open(metadataFilePath, "r+")) as f:
            metadata = json.load(f)
            for k in metadata:
                for g in range(len(metadata)):
                    path_on_cloud = "collections/" + collectionName + "/" + image_list[i]
                    path_local = imagesFilePath + "/" + image_list[i]
                    image_data = storage.child(path_on_cloud).put(path_local)
                    download_url = storage.child("collections/" + collectionName + "/" + image_list[i]).get_url(image_data["downloadTokens"])
                    url = {"downloadUrl": download_url}
                    k.update(url)
                    uuid = {"nftUUID": uuid4().hex}
                    k.update(uuid)
                    i += 1
                    t = j - i
                    print(str(i) + " done, " + str(t) + " left")
            f.seek(0)
            json.dump(metadata, f, indent=5)

    def keyword(self, keywordsFilePath, metadataFilePath):

        keywords_file = open(keywordsFilePath, "r")
        keywords_file_list = keywords_file.readlines()
        keywords_file.close()

        metadata_file = open(metadataFilePath, "r")
        metadata = json.load(metadata_file)
        metadata_file.close()

        core_list = []
        if keywords_file_list[0][1:5] == "core":
            if keywords_file_list[0][7] != " ":
                core_string = keywords_file_list[0][7:-1]
                core_list = core_string.split(", ")

        attributes = []
        key_list = []
        value_list = []
        key_value = {}
        key_value_list = []
        x = 0

        for i in range(len(keywords_file_list)):
            if keywords_file_list[i][0] == "*":
                y = i
                attributes.append(keywords_file_list[i][1:-2])
                for j in range(len(keywords_file_list) - i):
                    if keywords_file_list[y][0] == "-":
                        key_list.append(keywords_file_list[y][1:].split(":")[0])
                        value_list.append(keywords_file_list[y].split(":")[1][1:-1])
                    elif keywords_file_list[y][0] == "\n":
                        break
                    y += 1
                key_value["key"] = attributes[x]
                for key, val in zip(key_list, value_list):
                    key_value[key] = val
                key_value_list.append(key_value)
                key_list = []
                value_list = []
                key_value = {}
                x += 1

        keywords_list = []
        combined_keywords_list = []
        combined_str = ""

        for a in metadata:
            for b in a["attributes"]:
                for c in range(len(key_value_list)):
                    if b["key"] == key_value_list[c]["key"]:
                        str = "".join(key_value_list[c][b["value"]])
                        combined_str += " " + str + ","
                        keywords_temp_list = combined_str[1:-1].split(", ")
                        combined_keywords_list = core_list + keywords_temp_list
            combined_str = ""
            keywords_list.append(combined_keywords_list)

        return keywords_list

    def firestore(self, collectionName, metadataFilePath, keywordsFilePath):

        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        db = firestore.client()

        f = open(metadataFilePath, "r")
        metadata = json.load(f)
        f.close()

        for j in range(len(metadata)):
            db.collection("Nfts").document(metadata[j]["nftUUID"]).set(metadata[j], merge=True)
            db.collection("Nfts").document(metadata[j]["nftUUID"]).set(
                {"auctionStatus": "online", "directBuy": 500, "directBuyText": "500 DC", "highestBid": 100,
                 "highestBidOwner": "null", "highestBidText": "100 DC", "liveUntil": "-", "nftName": collectionName + " #" + str(j + 1),
                 "owner": "Deatris", "nftCollection": collectionName, "liveUntilTime": datetime.datetime.now()}, merge=True)
            db.collection("Nfts").document(metadata[j]["nftUUID"]).set(
                {"keywords": self.keyword(keywordsFilePath, metadataFilePath)[j]}, merge=True)

    def init(self, collectionName, imagesFilePath, csvFilePath, metadataFilePath, keywordsFilePath):

        self.metadata(collectionName, imagesFilePath, csvFilePath, metadataFilePath)
        f = open(metadataFilePath, "r")
        metadata = json.load(f)
        f.close()
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        db = firestore.client()

        for j in range(len(metadata)):
            db.collection("Nfts").document(metadata[j]["nftUUID"]).set(metadata[j], merge=True)
            db.collection("Nfts").document(metadata[j]["nftUUID"]).set(
                {"auctionStatus": "online", "directBuy": 500, "directBuyText": "500 DC", "highestBid": 100,
                 "highestBidOwner": "null", "highestBidText": "100 DC", "liveUntil": "-", "nftName": collectionName + " #" + str(j + 1),
                 "owner": "Deatris", "nftCollection": collectionName, "liveUntilTime": datetime.datetime.now()}, merge=True)
            db.collection("Nfts").document(metadata[j]["nftUUID"]).set(
                {"keywords": self.keyword(keywordsFilePath, metadataFilePath)[j]}, merge=True)
