import requests
from requests_toolbelt import MultipartEncoder

def prediction(classes, ID, filename, Img):
    if classes == 'potato':
        url = "http://39.98.144.212:5000/api/prediction"
        header = {"Content-Type": "multipart/form-data"}
        m = MultipartEncoder(
          fields={
                 'ID':ID,
                 'filename': filename,
                  'Img': ('1.jpg', open(Img, 'rb'), 'text/plain')}
          )
        res = requests.post(url=url, headers={'Content-Type': m.content_type}, data=m)
        print(res.content.decode('unicode-escape'))

    elif classes == 'tomato':
        url = "http://39.98.144.212:5000/api/prediction_tomato"
        header = {"Content-Type": "multipart/form-data"}
        m = MultipartEncoder(
            fields={
                    'ID': ID,
                    'filename': filename,
                    'Img': ('1.jpg', open(Img, 'rb'), 'text/plain')}
        )
        res = requests.post(url=url, headers={'Content-Type': m.content_type}, data=m)
        print(res.content.decode('utf-8'))

    elif classes == 'corn':
        url = "http://39.98.144.212:5000/api/prediction_corn"
        header = {"Content-Type": "multipart/form-data"}
        m = MultipartEncoder(
            fields={
                    'ID': ID,
                    'filename': filename,
                    'Img': ('1.jpg', open(Img, 'rb'), 'text/plain')}
        )
        res = requests.post(url=url, headers={'Content-Type': m.content_type}, data=m)
        print(res.content.decode('unicode-escape'))

    else:
        return None





