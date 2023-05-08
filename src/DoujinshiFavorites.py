import sys
sys.path.append('..')
import os, re, sqlite3, json, html
from datetime import datetime
from lxml import etree
from config import (
    ExHentai_Cookies,
    Proxy,
    favoritesDB,
    translationDB,
    local_mangaPath,
    igneous,
    checktorrent_sw,
    validateTitle,
)
from Browser import Browser
from DoujinshiDownlod import updateDownload
from difflib import SequenceMatcher
#如果igneous为空的话自动切换到e-hentai
if igneous == "":
    query = "https://e-hentai.org/favorites.php"
else:
    query = "https://exhentai.org/favorites.php"
EHentai_API_url = "https://api.e-hentai.org/api.php"
#本子id所属收藏夹
favorites_dice = {}

class md:
    def __init__(self) -> None:
        pass


def get_favorites(isTotal):
    br = Browser()
    br.set_proxies(proxies=Proxy, proxy_bypass=lambda hostname: False)
    br.addheaders = [
        (
            "User-agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
        )
    ]
    br.set_handle_robots(False)
    for cookie in ExHentai_Cookies:
        br.set_cookie(
            name=cookie["name"],
            value=cookie["value"],
            domain=cookie["domain"],
            path=cookie["path"],
        )
    
    a = 0
    #循环控制
    flag = True
    #已无下一页的信号
    Next_page = True
    xpathdice = {'Minimal':'gl2m','Minimal+':'gl2m','Compact':'gl2c','Extended':'gl2e','Thumbnail':'gl5t'}
    unext = ''
    while flag:
        gidList = []
        #收藏第一页
        if a == 0 and unext == '':
            url = query
        #下一页链接存在时
        elif len(unext) != 0:
            url = unext[0]
        elif len(unext) == 0 and a != 0:
            Next_page = False
        _raw = br.open_novisit(url)
        raw = _raw.read()
        #解码为html
        html = etree.HTML(raw)
        raw = raw.decode("unicode_escape")
        #先获取页面的显示模式，不同显示模式本子id的地址不同
        selected = html.xpath('//option[@selected="selected" and (@value="m" or @value="p" or @value="l" or @value="e" or @value="t")]/text()')
        if selected[0] in ['Minimal','Minimal+','Compact']:
            xpa = '//*[@class="'+str(xpathdice[(selected[0])])+'"]/div[3]/div/@id'
            results = html.xpath(xpa)
        elif selected[0] == 'Extended':
            xpa = '//*[@class="'+str(xpathdice[(selected[0])])+'"]/div[2]/@id'
            results = html.xpath(xpa)
        elif selected[0] == 'Thumbnail':
            results = html.xpath('//*[@class="'+str(xpathdice[(selected[0])])+'"]/div/div[2]/@id')
        if len(results) == 0:
                break 
        for i in results:
            #根据id匹配本子所属收藏夹，然后加入字典中
            category = html.xpath('//div[@id="'+i+'"]/@title')
            favorites_dice[str(i[7:])] = category[0]
                #获取下一页地址
        #获取下一页链接，上一次已获取不到下一页的话这次直接跳过
        if Next_page != False:
            unext = html.xpath('//*[@id="unext"]/@href')
        gidList = get_gallery_info(raw)
        if gidList == None:
            break
        for s in range(int(len(gidList) / 10) + 1):
            if not get_all_details(
                gidlist=gidList[s * 10 : (s + 1) * 10], timeout=1000, isTotal=isTotal
            ):
                break
        a = a + 1
        #不存在下一页则退出循环
        if Next_page == False:
            flag = False
            break 


def get_gallery_info(raw):
    global failed
    pattern = re.compile(
        r"https:\/\/(?:e-hentai\.org|exhentai\.org)\/g\/(?P<gallery_id>\d+)/(?P<gallery_token>\w+)/"
    )
    results = re.findall(pattern, raw)
    if not results:
        return None
    gidlist = []
    for r in results:
        gidlist.append(list(r))
    return gidlist


def isInserted(gmetadata):
    gid = str(gmetadata["gid"]) + "/" + str(gmetadata["token"])
    con = sqlite3.connect(favoritesDB)
    cur = con.cursor()
    cur.execute("select * from favorites where gid=" + "'" + gid + "'")
    count = len(cur.fetchall())
    cur.close()
    con.close()
    if count > 0:
        return True
    return False


def get_all_details(gidlist, timeout, isTotal):

    if len(gidlist) == 0:
        return
    EHentai_API_url = "https://api.e-hentai.org/api.php"
    br = Browser()

    data = {"method": "gdata", "gidlist": gidlist, "namespace": 1}
    data = json.dumps(data)

    br.set_proxies(proxies=Proxy, proxy_bypass=lambda hostname: False)

    try:
        raw = br.open_novisit(EHentai_API_url, data=data, timeout=timeout).read()
    except:
        print("网络错误")
        return
    gmetadatas = json.loads(raw)["gmetadata"]
    Newgmetadatas = []
    for gmetadata in gmetadatas:
        gmetadata["title_jpn"] = html.unescape(gmetadata["title_jpn"])
    if len(Newgmetadatas) > 0:
        gmetadatas = Newgmetadatas
    for gmetadata in gmetadatas:
        if not isInserted(gmetadata):
            m = toMetadata(gmetadata)
            insert(m)
        elif not isTotal:
            return False
    return True

def checktorrent(gmetadata):
    '''
    检查种子后缀是否为压缩包，如果是文件夹则跳过
    检查种子文件名与本子标题、原标题是否匹配，匹配度过低则跳过
    '''
    # 设置最大重试次数
    num_tries = 3 
    #字典，key=hash，vlan=[文件名,文件大小]
    filedict = {}
    # key=标题，vlan=[哈希，匹配程度]
    outdict = {}
    # key=日文标题，vlan=[哈希,匹配程度]
    outdict_jp = {}
    while num_tries > 0:
        try:
            #循环输出所有种子字典
            for i in gmetadata["torrents"]:
                #[文件名,文件大小]
                list = []
                name = i['name']
                hash = i['hash']
                size = i['fsize']
                # 判断常见本子压缩格式后缀正则
                compress_regex = r'\.(zip|rar|cbz|cbr|cb7|7z)$'
                #如果发现文件不是压缩文件则跳过
                if re.search(compress_regex, name):
                    print('文件是漫画压缩格式',str((name)[-3:]))
                    pass
                else:
                    print('文件不是漫画压缩格式',str((name)[-3:]))
                    continue 
                list.append(name)
                list.append(int((size)[:-3]))
                filedict[hash] = list
        except Exception as e:
            print(e)
            num_tries -= 1 # 重试次数-1
        if len(filedict) == 0:
            return 
        #依次输出vlan(哈希)
        for vlan in filedict:
            #filedict结构:{'哈希':[文件名,大小]}

            #对标题进行匹配
            Matching = SequenceMatcher(None, (filedict[vlan])[0], gmetadata["title"]).ratio()
            #字典结构：{'哈希':[匹配率]}
            outdict[vlan] = Matching
            if "title_jpn" in gmetadata:
                #对日文标题进行匹配
                Matching_jp = SequenceMatcher(None, (filedict[vlan])[0], gmetadata["title_jpn"]).ratio()
                outdict_jp[vlan] = Matching_jp
        #如果种子只有一个
        if len(filedict) == 1:
            #如果存在日语标题
            if "title_jpn" in gmetadata:
                #如果日语标题匹配成功则直接返回该种子哈希
                if outdict_jp[vlan] > 0.5:
                    return vlan
                #如果标题匹配成功则返回该种子哈希
                elif outdict[vlan] > 0.5:
                    return vlan
                else:
                    #都不匹配则返回空
                    return
            #如果不存在日语标题
            else:
                #如果匹配标题则返回种子哈希
                if outdict[vlan] > 0.5:
                    return vlan
                else:
                    #都不匹配则返回空
                    return
        #如果种子链接不止一个
        else:
            #符合条件的种子列表
            Conform_jp = {}
            Conform = {}
            #循环输出所有哈希值
            for h in filedict:
                #如果存在日文标题
                if "title_jpn" in gmetadata:
                    #如果匹配日文标题则添加哈希到列表中(日文标题列表)
                    if outdict_jp[h] > 0.5:
                        Conform_jp[h] = filedict[h][1]
                    #如果匹配标题则添加哈希到列表中(标题列表)
                    elif outdict[h] > 0.5:
                        Conform[h] = filedict[h][1]
                    else:
                        #都不匹配则跳出本次循环
                        continue
                
                #如果不存在日文标题
                else:
                    #如果匹配标题则添加哈希到列表中(标题列表)
                    if outdict[h] > 0.5:
                        Conform[h] = filedict[h][1]
                    else:
                        #不匹配则跳出本次循环
                        return
            #如果日文标题列表不为空
            if len(Conform_jp) != 0:
                #如果日文列表数量为1则直接返回该哈希
                if len(Conform_jp) == 1:
                    return next(iter(Conform_jp.keys()))
                else:
                    #获取体积最大的哈希值
                    return max(Conform_jp, key=lambda k: Conform_jp[k])
            if len(Conform) != 0:
                #如果日文列表数量为1则直接返回该哈希
                if len(Conform) == 1:
                    #直接返回第一个的哈希
                    return next(iter(Conform.keys()))
                else:
                    #获取体积最大的哈希值
                    return max(Conform, key=lambda k: Conform[k])



def optional(pattern: str):
    return "(?:" + pattern + ")?"


def getFileName(title: str, authors: str):
    if authors == "":
        return title
    return validateTitle("[" + authors + "] " + title)


def extractFieldFromTitle(title: str):
    global failed
    pattern = re.compile(
        r"^\s*"  # match spaces                  (optional)
        + optional(
            r"\((?P<publisher>[^\(\)]+)\)"
        )  # match publisher, such as C99  (optional)
        + r"\s*"  # match spaces                  (optional)
        + optional(
            r"\[(?P<authors>[^\[\]]+)\]"
        )  # match authors                  (optional)
        + r"\s*"  # match spaces                  (optional)
        + r"(?P<title>[^\[\]\(\)]+)"  # match title                   (must, need strip)
        + r"\s*"  # match spaces                  (optional)
        + optional(
            r"\((?P<magazine_or_parody>[^\(\)]+)\)"
        )  # match magazine_or_parody      (optional)
        + r"\s*"  # match spaces                  (optional)
        + optional(
            r"\[(?P<addtional1>[^\[\]]+)\]"
        )  # match addtional_field_1       (optional)
        + r"\s*"  # match spaces                  (optional)
        + optional(
            r"\[(?P<addtional2>[^\[\]]+)\]"
        )  # match addtional_field_2       (optional)
        + r"\s*"  # match spaces                  (optional)
        + optional(
            r"\[(?P<addtional3>[^\[\]]+)\]"
        )  # match addtional_field_3       (optional)
    )
    match = re.match(pattern, title)
    if match:
        re_title = match.group("title").strip()
    else:
        re_title = title
    return re_title


def getName(list, i):
    try:
        return list[i]
    except:
        return ""


def findName(conn, comment, raw):
    try:
        str = conn.execute(comment).fetchone()[0]
        if ")" in str:
            pattern = re.compile("\)(.*)")
            str = pattern.search(str).group(1)
        return str
    except:
        return raw


def toMetadata(gmetadata):
    
    m = md()
    m.gid = str(gmetadata["gid"]) + "/" + str(gmetadata["token"])
    m.title = extractFieldFromTitle(gmetadata["title_jpn"])
    m.category = gmetadata["category"]
    m.isExpunged = False
    m.authors = []
    m.characters = []
    m.parody = []
    m.torrents = []
    
    m.favorites_list = favorites_dice[str(gmetadata["gid"])]
    #开启智能种子筛选
    #print('gmetadata["torrentcount"]',gmetadata["torrentcount"],' gmetadata["torrents"]',gmetadata["torrents"])
    if checktorrent_sw:
        
        torrent = checktorrent(gmetadata)
        if torrent == None:
            m.torrents.append('')
            m.torrentCount = 0
        else:
            m.torrents.append(torrent)
            m.torrentCount = 1
    else:
        m.torrentCount = gmetadata["torrentcount"]
        for torrent in gmetadata["torrents"]:
            m.torrents.append(torrent["hash"])
    conn = sqlite3.connect(translationDB)
    c = conn.cursor()
    tranTag = []

    for tag in gmetadata["tags"]:

        taglist = tag.split(":")
        tableName = getName(taglist, 0)
        nameSpace = findName(
            c,
            "SELECT name from rows WHERE key like '{key}'".format(key=tableName),
            tableName,
        )
        if tableName == "group":
            tableName = "groups"
        raws = getName(taglist, 1).split(",")
        if len(taglist) == 1:
            comment = "SELECT name from reclass WHERE raw like '{raw}'".format(
                raw=taglist[0]
            )
            Newtag = findName(c, comment, taglist[0])
            tranTag.append(Newtag)
            continue
        for raw in raws:
            comment = "SELECT name from {table} WHERE raw like '{raw}'".format(
                table=tableName, raw=raw
            )
            Newtag = findName(c, comment, raw)
            if tableName == "groups":
                m.groups = Newtag
            elif tableName == "artist":
                m.authors.append(Newtag)
            elif tableName == "parody":
                m.parody.append(Newtag)
            elif tableName == "character":
                m.characters.append(Newtag)
            elif (
                tableName == "language"
                or tableName == "reclass"
                or nameSpace == "上传者"
                or nameSpace == "翻译者"
            ):
                pass
            else:
                Newtag = nameSpace + ":" + Newtag
                tranTag.append(Newtag)
    if not hasattr(m, "groups"):
        m.groups = "null"
    m.tags = tranTag
    conn.close()

    m.authors = ",".join(m.authors)
    m.authors = (
        m.groups if m.authors == "" and m.groups != "null" else m.authors
    )  # 如果作者名为空而社团名不为空，作者名使用社团名

    if isExist(m.authors, m.title):
        m.isExisting = "exist"
    else:
        m.isExisting = "undownloaded"
    return m


def isExist(authors, title):
    mangaName = getFileName(authors=authors, title=title)
    mangaFile = os.path.join(local_mangaPath, validateTitle(mangaName))
    if os.path.isdir(mangaFile):
        return True
    return False


def insert(m):
    m.addDate = datetime.now().strftime("%Y-%m-%d")
    sql = """insert into favorites(
    gid,
    authors,
    title,
    favorites_list,
    isExpunged,
    isExisting,
    groups,
    category,
    tags,
    characters,
    parody,
    torrentCount,
    torrents,
    addDate) 
    values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
    value = [
        m.gid,
        m.authors,
        m.title,
        m.favorites_list,
        m.isExpunged,
        m.isExisting,
        m.groups,
        m.category,
        ",".join(m.tags),
        ",".join(m.characters),
        ",".join(m.parody),
        m.torrentCount,
        ",".join(m.torrents),
        m.addDate,
    ]
    con = sqlite3.connect(favoritesDB)
    cur = con.cursor()
    try:
        cur.execute(sql, value)
        con.commit()
    except Exception as e:
        print(e)
    cur.close()
    con.close()
    print(getFileName(authors=m.authors, title=m.title), "：录入")


def upgradaExist():
    con = sqlite3.connect(favoritesDB)
    cur = con.cursor()
    cur.execute("select * from favorites where isExisting != 'exist'")
    rows = cur.fetchall()
    cur.close()
    con.close()
    for row in rows:
        if isExist(row[1], row[2]):
            updateDownload(row[0], "exist")
            print(getFileName(authors=row[1], title=row[2]) + "记入")


def start(isTotal):
    con = sqlite3.connect(favoritesDB)
    con.execute(
        """create table if not exists favorites(
            gid TEXT PRIMARY KEY  NOT NULL,
            authors TEXT,
            title TEXT NOT NULL,
            favorites_list TEXT NOT NULL,
            isExpunged BOOLEAN NOT NULL,
            isExisting TEXT NOT NULL,
            groups TEXT,
            category TEXT NOT NULL,
            tags TEXT,
            characters TEXT,
            parody TEXT,
            torrentCount INT,
            torrents TEXT,
            addDate DATE NOT NULL)"""
    )
    con.close()
    get_favorites(isTotal)
    upgradaExist()

