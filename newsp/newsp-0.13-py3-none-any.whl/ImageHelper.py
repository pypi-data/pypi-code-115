import requests, os,uuid
import tempfile
from PIL import ImageOps, Image
logo_path = os.getenv('NEWS_LOGO_PATH','img/logo.png')
img_root = os.getenv('NEWS_IMG_ROOT','img')
from slugify import slugify_url
def download_image(url):
    try:
        tmp_dir = tempfile.gettempdir()
        r = requests.get(url, allow_redirects=True)
        type = r.headers.get('content-type').split("/")[1]
        file_name = os.path.join(tmp_dir, str(uuid.uuid4()) + "." + type)
        open(file_name, 'wb').write(r.content)
        return file_name, type
    except:
        pass
    return None, None
def process_image(img_url, title):
    rs=None
    try:
        file_name, type = download_image(img_url)
        if file_name:
            img = Image.open(file_name)
            logo = Image.open(logo_path)
            thumbnail = ImageOps.fit(
                img,
                (1280, 720),
                Image.ANTIALIAS
            )
            thumbnail.paste(logo, (0, 0), logo)
            thumbnail = thumbnail.convert('RGB')
            rs = os.path.join(img_root, slugify_url(title)+".jpg")
            thumbnail.save(rs)
            os.remove(file_name)
    except:
        import traceback
        traceback.print_exc()
        pass
    return rs
def upload_direct_image(img_url):
    try:
        file_name, type = download_image(img_url)
        if file_name:
            return upload_image(file_name,type)
    except:
        pass
    return None
def upload_image(img_path, type):
    url = "https://upload.uploadcare.com/base/?jsonerrors=1"

    payload={"UPLOADCARE_PUB_KEY":"17bedf1d77d1153fa313","source":"local","signature" : "", "expire" : "","UPLOADCARE_STORE":""}
    headers = {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0',
      'Accept': 'application/json, text/javascript, */*; q=0.01',
      'Accept-Language': 'en-US;q=0.5,en;q=0.3',
      'Accept-Encoding': 'gzip, deflate, br',
      'Referer': 'https://repost.soundcloud.com/',
      'X-UC-User-Agent': 'UploadcareWidget/3.10.0/17bedf1d77d1153fa313 (JavaScript)',
      'Origin': 'https://repost.soundcloud.com',
      'Sec-Fetch-Dest': 'empty',
      'Sec-Fetch-Mode': 'cors',
      'Sec-Fetch-Site': 'cross-site',
      'Connection': 'keep-alive'
    }
    img_name = os.path.basename(img_path)
    up = {'image': (img_name, open(img_path, 'rb'), "image/"+type)}
    response = requests.request("POST", url, headers=headers, data=payload, files=up).json()
    return response['image']
