#!/usr/bin/env python3
import web,sys,os,socket
from os import path
import re
from pathlib import Path
from io import BytesIO
from .. import yxsfile
from .. import encrypt
from . import m_file
import time
from PIL import Image
import hashlib
import pickle
import json
from urllib.parse import quote,unquote
# from base64 import b64encode,b64decode
# sys.argv.append('8088')
#这是一个基于web.py的文件服务器
urls = (   
    '/account/.*','account',
    '/file_downloader/.*','download',
    '/player_/.*','player',
    '/.*','FileSystem')
file_render=web.template.render('.',cache=False)
global_text_suffix=set(['.html','.js','.css'])
pic_suffix = ('.jpg','.jpeg','.png','.webp','.jpxs')
pic_suffix += tuple([i.upper() for i in pic_suffix[:-1]])
media_suffix = pic_suffix + ('.mp4','.ogg','.webm','.mpxs') 
pic_suffix = set(pic_suffix)
# poster_dict = dict()
# global_setting=dict()
# global_account_info = dict()
# global_cookies = set()

web.config.debug = False  # 注意调式模式使用
# web.config.session_paremeters['timeoue'] = 60*10  # 10分子超时

def generate_html(body,dirname):
    def write_element(urlt,namet):
        fs3 = '     <li><a href="{i}">{j}</a></li>\n'
        fimage = '<div class="item"><img src="" alt=" " data-src="{infojpg}"/></div>\n'	
        content_html = '<li class="post box row fixed-hight"><div class="post_hover"><div class="thumbnail boxx"><a href="{infohtml}" class="zoom click_img" rel="bookmark" title="{videoname}"><img src="" data-src="{infojpg}" width="300" height="500" alt="{videoname}"/> </a></div><div class="article"><h2>  <a class="click_title" href="{infohtml}" rel="bookmark" title="{videoname}">{videoname}</a></h2></div></div></li>\n'	
        if urlt[:2] == '__':
            return ''
        for ftyp in pic_suffix:
            if urlt.endswith(ftyp) and urlt.find('__poster_dir__')==-1:
                jpgid[0] += 1
                if jpgid[0] % 8 == 1:
                    ti = '<div class="masonry2">'
                    if jpgid[1] == 1:
                        ti = '</div>'+ti 
                    jpgid[1] = 1
                else:
                    ti = ''
                ft = ti+fimage.format(infojpg = urlt)
                break 
        else:
            if urlt[-1] == '/':
                ft = content_html.format(infohtml = urlt,videoname = namet,infojpg=urlt+'__poster_dir__.jpg')
            else:
                if Path(urlt).suffix in media_suffix and urlt.find('__poster_dir__')==-1:
                    ft = fs3.format(i=urlt,j=namet)
                else:
                    ft=''
        return ft
    html_string1 = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Type" content="text/html" />
<meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
<title>{dirname}</title>
<meta name="description" content="" />
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=0, minimum-scale=1.0, maximum-scale=1.0">

<link rel="stylesheet" type="text/css" href="builtin_kube.css" />
<link rel="stylesheet" type="text/css" href="builtin_style.css" /> 

    <style>

            .masonry2 {{ 
                column-count:4;
                column-gap: 1px;
                width: 100%;
                margin:1px auto;
            }}
            .item {{ 
                margin-bottom: 1px;
                min-height:200px;
            }}
            @media screen and (max-width: 1400px) {{ 
                .masonry2 {{ 
                    column-count: 3; // two columns on larger phones 
                }} 
            }} 

			@media screen and (max-width: 1000px) {{ 
                .masonry2 {{ 
                    column-count: 2; // two columns on larger phones 
                }} 
            }} 
            @media screen and (max-width: 600px) {{ 
                .masonry2 {{ 
                    column-count: 1; // two columns on larger phones 
                }} 
            }}

    </style>
</head>

'''

    html_string3 = '''<body class="custom-background">
    <div class="container">  
    <div class="mainleft" id="mainleft">
   
              <ul id="post_container" class="masonry clearfix">

    '''
        # $for i,j in body:
    # fs3 = '     <label><input name="{i}" type="checkbox" value=""/><a href="{i}">{j}</a></label> </br>\n'
    
    html_string4='''    </ul>
<div class="clear"></div><div class="last_page tips_info"></div>
</div>  
</div>
<div class="clear"></div>
<script src="builtin_jquery.min.js"></script>
<script>
start();
$(window).on('scroll', function() {
start();
})

function start() {
//.not('[data-isLoaded]')选中已加载的图片不需要重新加载
$('.container img').not('[data-isLoaded]').each(function() {
var $node = $(this);
if (isShow($node)) {
loadImg($node);
}
})
}

//判断一个元素是不是出现在窗口(视野)
function isShow($node) {
return $node.offset().top <= $(window).height() + $(window).scrollTop();
}
//加载图片
function loadImg($img) {
//.attr(值)
//.attr(属性名称,值)
$img.attr('src', $img.attr('data-src')); //把data-src的值 赋值给src
$img.attr('data-isLoaded', 1); //已加载的图片做标记
}
</script>

</body>
</html>
'''

    html_bytes = BytesIO()
    html_bytes.write(html_string1.format(dirname=dirname).encode('utf8'))
    # html_bytes.write(fs1.format(dirname = dirname).encode('utf8'))
    # html_bytes.write(html_string2.encode('utf8'))
    # html_bytes.write(fs2.format(dirname = dirname).encode('utf8'))
    html_bytes.write(html_string3.encode('utf8'))
    jpgid = [0,0]
    a = [write_element(i,j) for i,j in body]
    if jpgid[1]>0:
        a.append('</div>')
    html_bytes.write(''.join(a).encode('utf8'))
    html_bytes.write(html_string4.encode('utf8'))
    length = html_bytes.tell()
    html_bytes.seek(0,0)
    web.header('Content-Type','text/html')
    web.header('Content-Length',str(length))
    return html_bytes


def encode(url):
    return quote(url)
def decode(url):
    return unquote(url)
def check_user_passwd(user,passwd,db={}):
    if not db:
        db_file = global_setting.get('passwd_file','password.json')
        if not Path(db_file).is_file():
            t = {'1':'1'}
            fp = open(db_file,'w')
            json.dump(t,fp)
            fp.close()
        db = json.load(open(db_file))
    rr = False 
    if user in db:
        md = hashlib.md5()
        md.update(passwd.encode())
        md.update(b'__s__')
        tt = md.hexdigest()
        if tt == db[user] or db[user] == passwd:
            rr = True   
    return rr
def cookie_available(cookie,account_info=None):
    if account_info is None:
        account_info = global_account_info
        if not account_info and Path(global_setting.get('account_file','account_file.pickle')).is_file():
            t = pickle.load(open(Path(global_setting.get('account_file','account_file.pickle')),'rb'))
            global_account_info.update(t)
            global_account_info['read']=True 
    rr = False
    user = cookie.get('cku')
    if user:
        if user in account_info:
            val = cookie.get('ckv')
            if val == account_info[user]:
                rr = True
    return rr

def check_cookie():
    if global_setting['check_user']:
        cookies = web.cookies()
        user_token = cookies.get('user_token')
        if user_token in global_cookies:
            return True 
        else:
            return False
    else:
        return True
class account:
    def GET(self,*d):
        url=web.url()
        filepath = url[1:]
        p = Path(filepath)
        if not p.is_file():
            if not p.name.startswith('builtin_'):
                filepath = str(p.with_name('builtin_'+p.name))
        return send_file(filepath)
    def POST(self,*d):
        indata = web.input()
        if not check_user_passwd(indata['username'],indata['password']):
            raise web.seeother('/account/login.html')
        cookie = hashlib.md5()
        cookie.update(indata['username'].encode())
        cookie.update(b'kwsst')
        cku = cookie.hexdigest()
        cookie.update(str(time.time()).encode())
        ckv = cookie.hexdigest()
        user_token = f'{cku}_{ckv}'
        web.setcookie('user_token',user_token,3600*24*365)
        global_cookies.add(user_token)
        raise web.seeother('/')
class FileSystem:
    def GET(self,*d):
        if not check_cookie():
            raise web.seeother('/account/login.html')
        url=web.url()
        hp  = web.input()
        url=decode(url)
        url = '.'+url
        url_path = Path(url)
        if url_path.is_dir():
            p=url
            if p[-1] != '/':
                raise web.seeother(url[1:]+'/')
        else:
            if url.endswith('mp4') or url.endswith('mpxs'):
                if not hp:
                    raise web.seeother('/player_/auto'+encode(url)+'?first=ok')
                else:
                    raise web.seeother('/file_downloader/x'+encode(url))
            else:
                return send_file(url)
                
        x=os.listdir(p)
        index_file = url_path / 'index.html'
        if index_file.is_file():
            return send_file(str(index_file))
        a=[]
        x.sort()
        for i in x:
            filename=p+i
            if path.isfile(filename):
                a.append([i,i])
            else:
                a.append([i+os.sep,i+os.sep])
        a.sort(key=lambda x:x[1][-1])
        for i in a:
            i[0]=encode(i[0])
        return generate_html(a,url_path.name)
        # return file_render.file(a,path.split(p[:-1])[1])
def find_poster(dirname):
    for root,ds,fs in os.walk(dirname):
        for f in fs:
            suffix = Path(f).suffix
            if suffix in pic_suffix:
                return (Path(root)/f).absolute()
    return None

def get_small_poster(filename,size=(256,-1)):
    if filename.endswith('.jpxs'):
        fp = open(filename,'rb')
        fp.read(2048)
        im = Image.open(BytesIO(fp.read()))
    else:
        im = Image.open(filename)
    if im.mode == 'RGBA':
        im = im.convert('RGB')
    
    w0,h0 = im.size
    w,h = size 
    bs = BytesIO()
    if h>0:
        if w/h>=w0/h0:
            m = int((h0 - w0/w*h)//2)
            cut = (0,m,w0,h0-m)
        else:
            m = int((w0-h0/h*w)//2)
            cut = (m,0,w0-m,h0)
        im = im.crop(cut)
        im = im.resize(size)
    else:
        h = int(w/w0*h0)
        im = im.resize((w,h))
    im.save(bs,format='jpeg')
    length = bs.tell()
    bs.seek(0,0)
    return bs,length
def send_file(filename):
    ppf = Path(filename)
    if ppf.name.startswith('builtin_'):
        sp =  m_file.sfile_dict.get(ppf.name)
        if sp:
            sp.seek(0,0)
            return sp
        else:
            return None
    if ppf.stem == '__poster_dir__':
        if filename in poster_dict:
            filename = poster_dict[filename]
        else:
            is_ppf = ppf.is_file()
            if not is_ppf and ppf.with_suffix('.jpxs').is_file():
                poster_dict[filename] = ppf.with_suffix('.jpxs')
                filename = poster_dict[filename]
            elif not is_ppf:
                filename0 = filename
                for i in ppf.parent.glob('*'):
                    suffix = i.suffix
                    if suffix in pic_suffix:
                        poster_dict[filename] = str(i)
                        filename = poster_dict[filename]
                        break
                else:
                    t = find_poster(ppf.parent)
                    if t is not None:
                        poster_dict[filename] = str(t)
                        filename = str(t)
                    else:
                        poster_dict[filename] = filename
                if filename != filename0:
                    content,_ = get_small_poster(filename,size=(256,256))
                    fjpxs = Path(filename0).with_suffix('.jpxs')
                    fp = open(fjpxs,'wb')
                    fp.write(b'0'*2048)
                    fp.write(content.read())
                    fp.close()
                    poster_dict[filename0] = fjpxs
                    filename = str(fjpxs)

    pre_suffix = Path(filename).suffix
    if not path.exists(filename):
        if filename.endswith('.vtt'):
            p = Path(filename).with_suffix('.mpxs')
            if p.is_file():
                if p.is_symlink():
                    p = p.resolve()
                dn = yxsfile.yxsFile(p).decode_filename()
                filename = yxsfile.yxsFile(dn.with_suffix('.vtt')).encode_filename()
            else:
                return None
        else:
            return None
    
    ct = web.ctx.env.get('CONTENT_TYPE')
    offset = 0
    fp = open(filename,'rb')
    length0 = path.getsize(filename)

    if ct is None:
        suffix = Path(filename).suffix.lower()
        if suffix == '.html':
            ct = 'text/html'
        elif suffix == '.js':
            ct = 'text/javascript'
        elif suffix == '.css':
            ct = 'text/css'
        elif pre_suffix == '.vtt':
            ct = 'text'
            offset=2048
            fp.read(2048)
        elif suffix == '.mp4':
            ct = 'video/mp4'
        elif suffix == '.mpxs':
            ct = 'video/mp4'
            fp.read(2048)
            offset = 2048
        elif suffix == '.jpxs':
            ct = 'image/jpeg'
            fp.read(2048)
            offset = 2048
        else:
            ct = 'application/octet-stream'
        if suffix in global_text_suffix:
            data = fp.read()
            fp = BytesIO()
            if data[:10] == b'SP_ENCRYPT':
                data = encrypt.b64decode(data[10:],passwd=encrypt.get_default_passwd())
            offset = length0 - len(data)
            fp.write(data)
            fp.seek(0,0)
    web.header('Content-Type',ct)
    web.header('Content-Length',str(length0-offset))
    return fp
    

def download_file(fp,length,file_name='package',hrange = None):
    BUF_SIZE=1024*1024*2
    try:
        ct = web.ctx.env.get('CONTENT_TYPE')
        offset = 0
        if ct is None:
            suffix = Path(file_name).suffix.lower()
            if suffix == '.html':
                ct = 'text/html'
            elif suffix == '.js':
                ct = 'text/javascript'
            elif suffix == '.css':
                ct = 'text/css'
            elif suffix == '.mp4':
                ct = 'video/mp4'
            elif suffix == '.mpxs':
                ct = 'video/mp4'
                offset = 2048
            else:
                ct = 'application/octet-stream'
        
        web.header('Content-Type',ct)
        # 下载则加以下head
        # web.header('Content-disposition', 'attachment; filename={name}'.format(name=quote(file_name)))
        
        # Content-Range: bytes 2293762-3342338/145108958
        start = 0
        if hrange:
            web.ctx.status = '206 PartialContent'
            hrange = hrange[6:].split('-')
            ipos = int(hrange[0])
            fp.seek(ipos+offset,0)
            start = ipos
            # if len(hrange) == 2 and hrange[1]:
            #     BUF_SIZE = int(hrange[1]) - ipos
        fs = 'bytes {}-{}/{}'
        # print(206,'HTTP_RANGE',hrange)
        while True:
            
            c = fp.read(BUF_SIZE)
            if c:
                end = start + len(c)-1
                web.header('Content-Range',fs.format(start,end,length-offset))
                start = end
                yield c
            else:
                web.header('Content-Range',fs.format(start,start,length-offset))
                yield   b''
                break
        
    except Exception as err:
        print(err)
        yield 'Error'
    finally:
        if fp:
            fp.close()
class player:
    player_html = '''<video controls autoplay>
    <source src="{mp4}?play=ok"  type="video/mp4" />
    <track  kind="subtitles" srclang="zh-cn" src="{vtt}" default>
</video>'''
    def GET(self):
        if not check_cookie():
            raise web.seeother('/account/login.html')
        url=web.url()
        hp = web.input()
        file_name=decode(url)[13:]
        if file_name.startswith('./'):file_name = file_name[1:]
        if file_name[0] != '/':file_name = '/'+file_name
        if 'first' in hp:
            html_string1 = self.player_html.format(mp4=file_name,vtt=Path(file_name).with_suffix('.vtt'))
            html_bytes = BytesIO()
            html_bytes.write(html_string1.encode('utf8'))
            length = html_bytes.tell()
            html_bytes.seek(0,0)
            web.header('Content-Type','text/html')
            web.header('Content-Length',str(length))
            return html_bytes
        else:
            web.seeother('/file_downloader/x'+encode(file_name))
 
        

class download:
    def GET(self):
        if not check_cookie():
            raise web.seeother('/account/login.html')
        url=web.url()[18:]
        file_name=decode(url)
        f = open(file_name, "rb")
        length=path.getsize(file_name)
        hrange = web.ctx.env.get('HTTP_RANGE',None)
        for i in download_file(f,length,path.basename(file_name),hrange=hrange):
            yield i
            if hrange:
                break
def getip(ipv6):
    if ipv6:
        afi = socket.AF_INET6
        ip8 = '2001:4860:4860::8888'
    else:
        afi = socket.AF_INET
        ip8 = '8.8.8.8'
    
    try:
        s=socket.socket(afi,socket.SOCK_DGRAM)
        s.connect((ip8,80))
        ip=s.getsockname()[0]
    finally:
        s.close()
    return ip
 
    # out = os.popen("ifconfig").read()
    # k = re.findall('(?<=inet) +\\d+\\.\\d+\\.\\d+\\.\\d+',out)
    # ips = [i.lstrip() for i in k]
    # ips = [i for i in ips if i!='127.0.0.1']
    # if ips:
    #     return ' '.join(ips)
    # else:
    #     return socket.gethostbyname(socket.gethostname())

def main(port,ssl,ipv6=False,check_user=False):
    global poster_dict,global_setting,global_account_info,global_cookies
    poster_dict = dict()
    global_setting=dict()
    global_account_info = dict()
    global_cookies = set()

    x=getip(ipv6)
    print('本机ip：{ip}'.format(ip=x))
    sys.argv = sys.argv[:1]

    if ipv6:
        ps = '[::]:'
    else:
        ps = ''
    if port:
        ps += str(port)
    if ps:
        sys.argv.append(ps)
    if ssl:
        from cheroot.server import HTTPServer
        from cheroot.ssl.builtin import BuiltinSSLAdapter
        yxspkg_rc = Path.home() /'.yxspkg'/'.ssl'
        crt = yxspkg_rc/ 'yxs_server.crt'
        key = yxspkg_rc/ 'yxs_server.key'
        if not crt.exists() or not key.exists():
            print('The files yxs_server.crt or yxs_server.key are not fond in {}'.format(yxspkg_rc))
        HTTPServer.ssl_adapter = BuiltinSSLAdapter(
            certificate=crt, 
            private_key=key)
    gsetting = {'check_user':check_user,'cookies.log':'cookies.log'}
    global_setting.update(gsetting)
    if Path(global_setting['cookies.log']).is_file():
        fp = open(global_setting['cookies.log'])
        t = [i.strip() for i in fp]
        global_cookies.update(t)

    app=web.application(urls, globals ())

    app.run()
if __name__ == '__main__': 
    main(8080,False,check_user=False)
    
    
