from newspaper import Article
from newspp.ImageHelper import process_image
import tempfile, os, uuid, random
from slugify import Slugify
import spacy
import random,json
site_url = os.getenv('SITE_URL','https://hoablue.xyz')
img_root = os.getenv('NEWS_IMG_ROOT','img')
slug_tag_stop_words_path = os.getenv('SLUG_TAG_STOP_WORDS_PATH','')

class NewsHelper:
    def load_file(self,path):
        rs = None
        try:
            with open(path, "r", encoding="UTF-8") as rf:
                rs = rf.readlines()
        except:
            pass
        return rs
    def parse(self, url, config=None, is_sum=False):
        article = Article(url,config=config)
        article.download()
        article.parse()
        new_top_image=""
        if article.top_image and len(article.top_image)>1 and "http" in article.top_image:
            new_top_image=process_image(article.top_image, article.title)
            if new_top_image:
                new_top_image = os.path.basename(new_top_image)
                new_top_image = f"{site_url}/img/{new_top_image}"
        keywords=''
        summary=''
        if is_sum:
            article.nlp()
            keywords= article.keywords
            summary= article.summary
        rs = {"title": article.title,
            "authors": article.authors,
            "text": article.text.split("\n"),
            "top_image": article.top_image, "new_top_image":new_top_image,
            "keywords": keywords, "summary": summary}
        return rs
    def make_body_html(self, arrtext):
        arr_html = []
        try:
            cut_begin=random.randint(0,3)
            cut_end=len(arrtext)-random.randint(0,3)
            arrtext=arrtext[cut_begin:cut_end]
            just_h2=False
            if len(arrtext)>3:
                for txt in arrtext:
                    if txt and len(txt)>1:
                        tmp_html = f"<p>{txt}</p>"
                        # if len(txt) < 100 and not just_h2:
                        #     tmp_html = f"<h2>{txt}</h2>"
                        #     just_h2 = True
                        # else:
                        #     tmp_html = f"<p>{txt}</p>"
                        #     just_h2 = False
                        arr_html.append(tmp_html)
        except:
            pass
        return arr_html
    def make_full_body_html(self, arrtext, remove_arr= []):
        arr_html = []
        try:
            for item in remove_arr:
                for row in arrtext:
                    if item in row:
                        arrtext.remove(row)
            if len(arrtext) > 3:
                for txt in arrtext:
                    if txt and len(txt) > 1:
                        tmp_html = f"<p>{txt}</p>"
                        arr_html.append(tmp_html)
        except:
            pass
        return arr_html
    def create_tag_from_title(self, title):
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(title)
        arr_tag = []
        for chunk in doc.noun_chunks:
            if chunk.text not in arr_tag:
                arr_tag.append(chunk.text)

        for entity in doc.ents:
            if entity.text not in arr_tag:
                arr_tag.append(entity.text)
        arr_tag_rs=arr_tag
        if len(arr_tag)>2:
            for _ in range(len(arr_tag)):
                i1 = random.randint(0, len(arr_tag)-2)
                i2 = random.randint(i1+1, len(arr_tag)-1)
                arr_tag_rs.append(arr_tag[i1]+" "+arr_tag[i2])
        return arr_tag_rs

    def parse_auto_full(self, url, categories, keywords=[], text_remove=[], config=None):
        rs = None
        try:
            rs = self.parse(url, config)
            if rs and rs['title']:
                arr_html = self.make_full_body_html(rs['text'], text_remove)
                if len(arr_html) > 0:
                    if rs['new_top_image'] and len(rs['new_top_image']) > 0:
                        title_tmp=rs['title'].replace('"', '\\"')
                        tmp_img = f"<figure class=\"wp-block-image size-large\"><img src=\"{rs['new_top_image']}\" alt=\"{title_tmp}\"/></figure>"
                        arr_html = [tmp_img] + arr_html
                    tmp_folder = tempfile.gettempdir()
                    rs_file = os.path.join(tmp_folder, str(uuid.uuid4()) + ".txt")
                    with open(rs_file, "w", encoding="utf-8") as wf:
                        wf.writelines(arr_html)
                    slugify_tag = Slugify()
                    slugify_tag.separator = ' '
                    slug_tag_stop_words = self.load_file(slug_tag_stop_words_path)
                    "".split()
                    slugify_tag.stop_words = slug_tag_stop_words
                    slugify_tag.max_length = 50
                    arrkw = []
                    keywords += self.create_tag_from_title(rs['title'])
                    for keyword in keywords:
                        if len(keyword)>3 and len(arrkw) < 10:
                            arrkw.append(slugify_tag(keyword))
                    tags_input = ",".join(set(arrkw))
                    title = rs['title'].replace('"', "'")
                    meta_input = {"_knawatfibu_url": rs['new_top_image'], "_knawatfibu_alt": title}
                    meta_input = json.dumps(meta_input).replace('"',"\\\"")
                    #meta_input = f"{{\"_knawatfibu_url\":\"{rs['new_top_image']}\",\"_knawatfibu_alt\":\"{title}\"}}"
                    cmd = f"wp --allow-root post create \"{rs_file}\" --post_title=\"{title}\" --post_status='publish'"
                    cmd_tag = f" --tags_input=\"{tags_input}\" --post_author={os.getenv('AUTHOR_ID', '1')} "
                    cmd_ping = f" --ping_status='open' --to_ping='http://rpc.pingomatic.com/ http://rpc.twingly.com http://www.blogdigger.com/RPC2 http://ping.blo.gs/ http://ping.feedburner.com http://rpc.weblogs.com/RPC2 http://www.pingmyblog.com' "
                    cmd_meta = f" --meta_input=\"{meta_input}\""
                    cmd += cmd_meta + cmd_tag + cmd_ping
                    print(cmd)
                    os.system(cmd)
                    os.remove(rs_file)
                    return True
        except:
            import traceback
            traceback.print_exc()
            pass
        return False
    def parse_auto(self,url, keywords):
        rs = None
        try:
            rs = self.parse(url)
            if rs and rs['title']:
                arr_html = self.make_body_html(rs['text'])
                if len(arr_html)>0:
                    if rs['new_top_image'] and len(rs['new_top_image'])>0:
                        title_tmp = rs['title'].replace("'", "\\'")
                        tmp_img = f"<figure class=\"wp-block-image size-large\"><img src=\"{rs['new_top_image']}\" alt=\"{title_tmp}\"/></figure>"
                        arr_html = [tmp_img]+arr_html
                    tmp_folder = tempfile.gettempdir()
                    rs_file = os.path.join(tmp_folder, str(uuid.uuid4()) + ".txt")
                    with open(rs_file,"w",encoding="utf-8") as wf:
                        wf.writelines(arr_html)
                    slugify_tag = Slugify()
                    slugify_tag.separator = ' '
                    slug_tag_stop_words= self.load_file(slug_tag_stop_words_path)
                    "".split()
                    slugify_tag.stop_words=slug_tag_stop_words
                    slugify_tag.max_length = 50
                    arrkw=[]
                    for keyword in keywords:
                        arrkw.append(slugify_tag(keyword))
                    arrkw.append(slugify_tag(rs['title']))
                    tags_input=",".join(set(arrkw))
                    title=rs['title'].replace('"','\\"')
                    meta_input=f"{{\"_knawatfibu_url\":\"{rs['new_top_image']}\",\"_knawatfibu_alt\":\"{title}\"}}"
                    cmd = f"wp --allow-root post create {rs_file} --post_title=\"{title}\" --post_status='publish'"
                    cmd_tag =f" --tags_input='{tags_input}' --post_author={os.getenv('AUTHOR_ID','1')} "
                    cmd_ping = f" --ping_status='open' --to_ping='http://rpc.pingomatic.com/ http://rpc.twingly.com http://www.blogdigger.com/RPC2 http://ping.blo.gs/ http://ping.feedburner.com http://rpc.weblogs.com/RPC2 http://www.pingmyblog.com' "
                    cmd_meta = f" --meta_input=\"{json.dumps(meta_input)}\""
                    cmd += cmd_meta + cmd_tag + cmd_ping
                    print(cmd)
                    os.system(cmd)
                    os.remove(rs_file)
                    return True
        except:
            import traceback
            traceback.print_exc()
            pass
        return False
