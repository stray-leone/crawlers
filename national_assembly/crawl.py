#!/usr/bin/python
#-*- coding: utf-8 -*-


from urlparse import urljoin
import re
import sys
import urllib2
import string #khh-?

import html5lib
import lxml

from scrapy.selector import Selector

# settings
PAGE_ENC = 'utf-8'
HEADERS = ['name_kr','name_cn','name_en','birth','party','district','committee','when_elected','off_phone','homepage','email','aides','pr_secrs','sc_secrs','hobby','experience','photo','url']
DATADIR = '.'


# global dicts
urls = {}
ppl_urls = []
ppl_data = []

def find_bracketed_text_regexp(exp, src):
    return re.search(exp, src, flags=re.DOTALL).group(1)

def find_bracketed_texts_regexp(exp, src):
    return re.search(exp, src, flags=re.DOTALL).groups(1)

def getlist_bracketed_regexp(exp, src):
    return re.findall(exp, src, flags=re.DOTALL)

def load_urls():
    for line in open('urls', 'r'):
        if line[0] == '#':
            continue
        key, url = line.split()
        urls[key] = url
        #print key + "////"  + url # khh-debug

def get_page(url, htmldir):
    page_in_txt = urllib2.urlopen(url).read()

    idx = url.find('num=')
    #print url # khh-debug
    #print idx # khh-debug
    #idx = url.find('memCode=')
    if idx != -1:
        #filename = '%s/%s.html' % (htmldir, url[idx + len('memCode='):]) # khh-old
        filename = '%s/%s.html' % (htmldir, url[idx + len('num='):])
    else:
        filename = '%s/index.html' % htmldir # khh-comment : is it necessary?

    with open(filename, 'w') as f:
        f.write(page_in_txt)
    #print type(page_in_txt) #khh-debug
    #page_in_txt = get_webpage(filename) # from e9t code
    return page_in_txt.decode(PAGE_ENC)
    #return page_in_txt.decode("utf-8")
    #return page_in_txt.decode(PAGE_ENC) # khh-old

def get_webpage(inf):  # from e9t code
    with open(inf, 'r') as f:
        page = html5lib.HTMLParser(\
            tree=html5lib.treebuilders.getTreeBuilder("lxml"),\
            namespaceHTMLElements=False)
        p = page.parse(f, encoding='euc-kr-8')
    return p

def get_xpath_data(data, _xpath):
    xpath_selector_list = []

    #print type(data) # khh-debug
    #print data # khh-debug
    hxs = Selector(text=data)
    for i in hxs.xpath(_xpath):
        xpath_selector_list.append(i.extract().encode("utf-8"))
    #debug_xpath_data( xpath_selector_list) # khh-debug
    #print len(xpath_selector_list) # khh-debug
    if len(xpath_selector_list) >0 :
        return  xpath_selector_list[0].decode(PAGE_ENC)
    else:
        return xpath_selector_list.decode(PAGE_ENC)

def get_ppl_urls(htmldir):
    def unescape_html(doc):
        escape_table = {'&lt;': '<', '&gt;': '>', '&amp;': '&'}
        for old, new in escape_table.items():
            doc = doc.replace(old, new)
        return doc

    url_key = 'people_list'
    list_class = 'memberna_list'


    page = get_page(urls[url_key], htmldir)

    full_member_list = []
    member_lists = getlist_bracketed_regexp(r'<dd class="img">(.+?)</dd>', page)
    print len(member_lists)

    #        <dd class="img">
    #                    <a href="#" onclick="jsMemPop(2680)" title="강기윤의원정보 새창에서 열림">
    #                                                                    <img src="/photo/9770703.jpg" alt="강기윤 의원사진" />
    #                    </a>
    #            </dd>

    for member_list in member_lists:
        #full_member_list += getlist_bracketed_regexp(r'<li class=".*?">[\r\n\s]*?<div class="fl"><a href="(.+?)".*?><img src=".+?" alt="(.+?)".*?>.*?</li>', member_list)
        full_member_list += getlist_bracketed_regexp(r'<a href="#" onclick="jsMemPop\((.+?)\)".*?>[\r\n\s]*?<img src=".+?" alt="(.+?)".*?/>', member_list)

    #print len(full_member_list)
    #full_member_list = full_member_list[:5] # khh-shirink
    #for url, name in full_member_list: # khh-old
    for url , name in full_member_list:
        #print url # khh-debug
        print urls['person']
        url = unescape_html(url)
        #ppl_urls.append(urljoin(urls['person'], url)) # khh-old
        ppl_urls.append(urls['person']+ url)


def extract_data(elems):
    key_x = 'descendant::text()'
    d = {}
    for i, e in enumerate(elems):
        if isinstance(e, lxml.etree._Element):
            key = e.xpath(key_x)[0].replace(' ', '')
            d[key] = ''
        else:
            d[key] += '\n' + elems[i].strip()
    return d

# TODO: remove this function
def debug_xpath_data(hxs):
    k =0
    for i in hxs:
        print str(k)+" : "+i.strip()
        k +=1

def extract_profile(page):
    def parse_name_and_birth(name_and_birth):
        # name_and_birth example:
        #        <strong>김윤덕</strong> (金潤德)<br>
        #        <strong class="txt_s">KIM Yunduk</strong><br>
        #        <span class="txt_e txt_s">1966.05.23</span>

        #<h4>강기윤</h4>
        #    <ul>
        #      <li class="photo">
        #           <img src="/photo/9770703.jpg" alt="강기윤 의원사진" />
        #      </li>
        #      <li>姜起潤</li>
        #      <li>KANG Gi Yun</li>
        #      <li>1960-06-04</li>
        #   </ul>

        #tokens = find_bracketed_texts_regexp(r'<strong>(.+?)</strong>\s\((.+?)\)<br\s*/?>.*?<strong class="txt_s">(.*?)</strong><br\s*/?>.*?<span class="txt_e txt_s">(.*)</span>', name_and_birth) # khh-old
        tokens = find_bracketed_texts_regexp(r'<h4>(.+?)</h4>.*?<ul>.*?<li" "class=.*?<li>(.*?)</li>.*?<li>(.*?)</li>.*?<li>(.*?)</li></ul>', name_and_birth)
        #print tokens # khh-debug
        #name_kr, name_cn, name_en, birth = tokens # khh-tmp-block
        #return [name_kr, name_cn, name_en, birth.replace('.','-')] # khh-tmp-block

    # get name & birth
    #name_and_birth = find_bracketed_text_regexp(r'<div class="profile">(.+?)</div>', page)
    profile = get_xpath_data(page,".//*/div[@class='profile']")
    name_kr = get_xpath_data(profile, ".//*/h4/text()")
    name_cn = Selector(text=profile).xpath('.//*/li/text()')[2].extract()
    name_en = Selector(text=profile).xpath('.//*/li/text()')[3].extract()
    birth = Selector(text=profile).xpath('.//*/li/text()')[4].extract()
    name_and_birth = [name_kr, name_cn, name_en, birth]
    #print name_and_birth # khh-debug

    #experience = get_xpath_data(page, ".//*/dl")
    #print experience
    # get experience
    experience =""
    experience = find_bracketed_texts_regexp(r'<dl class="per_history">.*?<dd.*?>(.+?)</dd>.*?</dl>', page)
    experience = ''.join(experience)
    experience = [d.strip() for d in experience.split('<br />')]
    experience = '||'.join(experience)
    #print "=========================\n"+str(len(experience)) #khh-debug

    # get photo
    photo = find_bracketed_text_regexp(r'<li class="photo".*?>[\r\n\s]*?<img src="(.+?)".*?/>[\r\n\s]*?</li>', page)
    photo = urljoin(urls['base'], photo)
    #print photo # khh-debug

    # get others
    #others = find_bracketed_text_regexp(r'<table.*?class="view_type03".*?>.*?<tbody>(.+?)</tbody>.*?</table>', page)
    others = find_bracketed_text_regexp(r'<dl.*?class="pro_detail">(.+?)</dl>', page)
    others = getlist_bracketed_regexp(r'<dd>[\r\t\n\s]*?(.+?)[\r\t\n\s]*?</dd>', others)

    #TODO: I don't know the meaning behind
    try:
        others[5] = re.search(r'<a.*?>(.+?)</a>', others[5]).group(1)
    except AttributeError as e:
        others[5] = ''

    print others
    stripped = [re.sub('\s+', '', i) for i in others]
    #for x in others:
    #    if '\t' in x:
    #        print "before:"+x
    #        #raw_input()
    #        #x.replace(" ","")
    #        str.strip(x.encode('utf-8'))
    #        print "after:"+x
    print others
    raw_input()
    full_profile = list(name_and_birth + others)
    full_profile.append(experience)
    full_profile.append(photo)
    [p.replace('\n','') for p in full_profile]
    return [p.replace('"',"'") for p in full_profile]

def crawl_ppl_data(htmldir):
    print len(ppl_urls)
    #for i, url in enumerate(ppl_urls): # khh-origin
    for i, url in enumerate(ppl_urls[:10]):
        #print url # khh-debug
        page = get_page(url, htmldir)
        profile = extract_profile(page)
        ppl_data.append(profile + [url])
        print i, ppl_data[i][0] # khh-to-unblock

def sort_ppl_data(ppl_data):
    ppl_data = sorted(ppl_data, key=lambda x: x[3])
    ppl_data = sorted(ppl_data, key=lambda x: x[0])

def write_csv():
    with open('assembly.csv', 'w') as f:
        f.write('%s\n' % ','.join(HEADERS))
        f.write('\n'.join(\
            '"%s"' % '","'.join(row) for row in ppl_data).encode('utf-8'))
    print 'Data succesfully written'

def main(argv, datadir=DATADIR):
    url = "http://www.assembly.go.kr/assm/memPop/memPopup.do?num=2680"
    htmldir = "./html"
    load_urls()
    get_ppl_urls(htmldir)
    crawl_ppl_data(htmldir)
    sort_ppl_data(ppl_data)
    write_csv()


if __name__ == '__main__':
    main(sys.argv[1:])
