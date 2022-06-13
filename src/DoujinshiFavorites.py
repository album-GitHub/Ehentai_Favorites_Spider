import os, re, sqlite3, json, html
from datetime import datetime
from urllib.error import URLError
from src.Browser import Browser
from config import (
    ExHentai_Cookies,
    Proxy,
    favoritesDB,
    translationDB,
    local_mangaPath,
    validateTitle,
)
import src.DoujinshiDownlod as DoujinshiDownlod

query = "https://exhentai.org/favorites.php"
EHentai_API_url = "https://api.e-hentai.org/api.php"


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
    gidList = []
    a = 0
    flag=True
    while flag:
        url = query + "?page=" + str(a)
        try:
            _raw = br.open_novisit(url)
            raw = _raw.read()
            raw = raw.decode("unicode_escape")
        except Exception as e:
            print(e)
            return
        gidList = get_gallery_info(raw)
        if gidList == None:
            break
        for s in range(int(len(gidList) / 10) + 1):
            if not get_all_details(gidlist=gidList[s * 10 : (s + 1) * 10], timeout=1000,isTotal=isTotal):
                flag =False
                break
        a = a + 1


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


def get_all_details(gidlist, timeout,isTotal):

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


def optional(pattern: str):
    return "(?:" + pattern + ")?"


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
    m.isExpunged = gmetadata["expunged"]
    m.authors = []
    m.characters = []
    m.parody = []
    m.torrents = []
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
    if isExist(m.authors, m.title):
        m.isExisting = "exist"
    else:
        m.isExisting = "undownloaded"
    return m


def isExist(authors, title):
    mangaName = "[" + authors + "] " + title
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
    values(?,?,?,?,?,?,?,?,?,?,?,?,?)"""
    value = [
        m.gid,
        m.authors,
        m.title,
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
    print("[" + m.authors + "] " + m.title, "：录入")


def upgradaExist():
    con = sqlite3.connect(favoritesDB)
    cur = con.cursor()
    cur.execute("select * from favorites where isExisting != 'exist'")
    rows = cur.fetchall()
    cur.close()
    con.close()
    for row in rows:
        if isExist(row[1], row[2]):
            DoujinshiDownlod.updateDownload(row[0], "exist")
            print("[" + row[1] + "] " + row[2] + "记入")


def start(isTotal):
    con = sqlite3.connect(favoritesDB)
    con.execute(
        """create table if not exists favorites(
            gid TEXT PRIMARY KEY  NOT NULL,
            authors TEXT,
            title TEXT NOT NULL,
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
