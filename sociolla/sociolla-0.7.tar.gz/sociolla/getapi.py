import requests
import pandas as pd
import re
import numpy as np
from bs4 import BeautifulSoup

class scrapsociolla():

    def __init__(self, url):
        """
        url: Link web product / catalog
        pos & neg = List kalimat positif dan negatif
        """
        self.url = url 
#         self.factory = StemmerFactory() # Sastrawi
#         self.stemmer = self.factory.create_stemmer() #Sastrawi
  
    def get_url(self, url):
        """
        param :
        url: url API
        
        fungsi ini adalah untuk request ke API nya
        """
        url_api = url
        r_api = requests.get(url_api)
        return r_api
    
    def get_category(self, limit_prod=10, limit_comment=10):
        """
        Fungsi ini adalah untuk membuat dataframe komentar dari banyak produk
        """
        url_web = self.url
        category = url_web.split('/')[-1]
        url_api = f'https://catalog-api4.sociolla.com/search?limit={limit_prod}&filter=%7B%22categories.slug%22:%22{category}%22%7D'
        r_api_all = self.get_url(url_api) # Request API catalog sociolla
        if "catalog-api" in r_api_all.url:
            if r_api_all.status_code == 200:
                data_all = r_api_all.json()['data']
                category, brand_name, product_name, id = [], [], [], []
                for i in data_all:
                    try:
                        brand_name.append(i['brand']['name'])
                        product_name.append(i['name'])
                        id.append( i['id'])
                        category.append(i['default_category']['name'])
                    except:
                        break
                df_base_product = pd.DataFrame({'category':category,'brand_name': brand_name, 'product_name': product_name, 'id': id})
                df_detail_all = pd.DataFrame()
                for brand,name,id in zip(df_base_product['brand_name'], df_base_product['product_name'], df_base_product['id']):
                    other_url = f"https://soco-api.sociolla.com/reviews?skip=0&sort=-created_at&limit={limit_comment}&filter=%7B%22$and%22:[%7B%22is_published%22:true%7D,%7B%22product_id%22:{id}%7D],%22is_detail_review%22:false%7D"
                    r_api_item = self.get_url(other_url) # Request API per product dari catalog sociolla
                    if r_api_item.status_code == 200:
                        df_detail, df_skin = self.create_dataset(r_api_item, limit_comment, brand, name, id, many=True)
                        df_detail_all = pd.concat([df_detail_all, df_detail])
                        df_detail_all['id'] = df_detail_all['id'].astype('int')
                    else:
                        print(f"Product {id} Status:", r_api_item.status_code)
            else:
               raise Exception('Catalog Status :', r_api_all.status_code)
        else:
            raise Exception("Wrong Function, Maybe You Mean 'get_one()'")
        return df_base_product, df_detail_all, df_skin

    def get_search(self, limit_prod=10, limit_comment=10):
        """
        Fungsi ini adalah untuk membuat dataframe komentar dari banyak produk
        """
        keyword = self.url
        url_api = f'https://catalog-api1.sociolla.com/v3/search?filter=%7B%22keyword%22:%22{keyword}%22%7D&limit=16&skip=0'
        r_api_all = self.get_url(url_api) # Request API catalog sociolla
        if "catalog-api" in r_api_all.url:
            if r_api_all.status_code == 200:
                data_all = r_api_all.json()['data']
                category, brand_name, product_name, id = [], [], [], []
                for i in data_all:
                    try:
                        brand_name.append(i['brand']['name'])
                        product_name.append(i['name'])
                        id.append( i['id'])
                        category.append(i['default_category']['name'])
                    except:
                        break
                df_base_product = pd.DataFrame({'category':category,'brand_name': brand_name, 'product_name': product_name, 'id': id})
                df_detail_all = pd.DataFrame()
                for brand,name,id in zip(df_base_product['brand_name'], df_base_product['product_name'], df_base_product['id']):
                    other_url = f"https://soco-api.sociolla.com/reviews?skip=0&sort=-created_at&limit={limit_comment}&filter=%7B%22$and%22:[%7B%22is_published%22:true%7D,%7B%22product_id%22:{id}%7D],%22is_detail_review%22:false%7D"
                    r_api_item = self.get_url(other_url) # Request API per product dari catalog sociolla
                    if r_api_item.status_code == 200:
                        df_detail, df_skin = self.create_dataset(r_api_item, limit_comment, brand, name, id, many=True)
                        df_detail_all = pd.concat([df_detail_all, df_detail])
                        df_detail_all['id'] = df_detail_all['id'].astype('int')
                    else:
                        print(f"Product {id} Status:", r_api_item.status_code)
            else:
               raise Exception('Catalog Status :', r_api_all.status_code)
        else:
            raise Exception("Wrong Function, Maybe You Mean 'get_one()'")
        return df_base_product, df_detail_all, df_skin
    
    def get_one(self, limit=10):
        """
        Fungsi ini adalah untuk membuat dataframe komentar hanya dari satu produk
        """
        product_id = self.url
        url_api = f"https://soco-api.sociolla.com/reviews?skip=0&sort=-created_at&limit={limit}&filter=%7B%22$and%22:[%7B%22is_published%22:true%7D,%7B%22product_id%22:{product_id}%7D],%22is_detail_review%22:false%7D"
        r_api_one = self.get_url(url_api)
        if "soco-api" in r_api_one.url:
            if r_api_one.status_code == 200:
                df_detail, df_skin = self.create_dataset(r_api_one,limit=limit, many=False)
            else:
                raise Exception("STATUS :", r_api_one.status_code)
        else:
            raise Exception("Wrong Function, Maybe You Mean 'get_many()'")
        return df_detail,df_skin

    def create_dataset(self, get_data,limit, brand=None,name=None,id=None, many=True):
        """
        param:
        get_data: hasil request dari fungsi get_url()
        brand, name, id: dipakai bila menggunakan fungsi get_many() untuk memasukkan nama,id,dan brand dari produk yang berbeda2
        many: Boolean, untuk memisahkan apakah menggunakan fungi get_many() atau get_one()
        
        return: dataframe yang bersisi detail dari user(komen, umur rating, dll), dan dataframe jenis kulit dari user
        
        fungsi ini dipakai untuk membuat dataset
        """
        data = get_data.json()['data']
        details, skin_types, ages, repurchases, rating = [], [], [], [], []
        long_wear, packaging, pigmentation, texture, value_for_money = [], [], [], [], []
        ids, brands, names = [], [], []
        for i in range(limit):
            try:
                detail = data[i]['details']
                if many == True:
                    ids.append(id)
                    brands.append(brand)
                    names.append(name)
            except:
                break
            details.append(detail)
            
            try:
                repurchase = data[i]['is_repurchase']
                repurchases.append(repurchase)
            except:
                repurchases.append(np.nan)
            
            try:
                rating.append(data[i]['average_rating'])
            except:
                rating.append(np.nan)
            
            
            try:
                long_wear.append(data[i]['star_long_wear'])
#                 long_wear.append(0)
                packaging.append(data[i]['star_packaging'])
                pigmentation.append(data[i]['star_pigmentation'])
#                 pigmentation.append(0)
                texture.append(data[i]['star_texture'])
                value_for_money.append(data[i]['star_value_for_money'])
            except:
                long_wear.append(np.nan)
                packaging.append(np.nan)
                pigmentation.append(np.nan)
                texture.append(np.nan)
                value_for_money.append(np.nan)
                
            
            owner = data[i]['owner']
            try:
                skins_type = owner['skin_types']
                for i in skins_type:
                    skin_types.append(i['name'])
            except:
                skin_types.append(np.nan)
                
            try:
                ages.append(owner['age_range'])
            except:
                ages.append(np.nan)
        if many == True:
            df_detail = pd.DataFrame({'id':ids,'brand':brands,'name':names,'detail':details, 'age_range':ages, 'repurchase':repurchases, 'rating':rating,
                            'long_wear':long_wear, 'packaging':packaging, 'pigmentation':pigmentation, 'texture':texture, 'value_for_money':value_for_money})
        else:
            df_detail = pd.DataFrame({'detail':details, 'age_range':ages, 'repurchase':repurchases, 'rating':rating,
                            'long_wear':long_wear, 'packaging':packaging, 'pigmentation':pigmentation, 'texture':texture, 'value_for_money':value_for_money})
        df_skin = pd.DataFrame({'skin_type':skin_types})
        return df_detail, df_skin