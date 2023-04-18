import re, qbittorrentapi

#建议不要在本地开启代理，qb容易连不上
Proxy = {"http": "http://localhost:1080", "https": "http://localhost:1080"}

#如果igneous为空的话自动切换到e-hentai下载
ipb_member_id = "4xxxx"
ipb_pass_hash = "4xxxxx"
igneous = ""

#本地漫画库文件夹路径，如果实际存放在远端，需要映射到本地
local_mangaPath = r"\\QHHH\Book\Doujinshi"

#本地下载文件夹路径，如果实际存放在远端，需要映射到本地
local_downloadPath = r"\\QHHH\Book\Torrents"

#安装有qbittorrent的主机的远端漫画库文件夹路径
remote_mangaPath = r"/Book/Doujinshi"

#安装有qbittorrent的主机的远端下载路径 如果你将qbittorrent安装在本地，则本地路径与远端路径是一样的
#但如果你使用Docker安装qbittorrent，则远端路径为Docker容器下路径，并确保上述文件夹映射到容器
remote_downloadPath = r"/Book/Torrents"

#存放数据库的绝对路径
favoritesDB = r"C:\Code\Ehentai_Favorites_Spider\db\Eh.db"
translationDB = r"C:\Code\Ehentai_Favorites_Spider\db\EhTagTranslation.db"

#qb的默认Torrent管理模式不能设置为自动，否则下载路径将失效
qbt_host = "xx.xx"
qbt_port = 11451
qbt_username = "xxx"
qbt_password = "xxxx"
timeLimit = 7
maxDownloadCount = 20


directDownloadLimit = 10
deleteAfterDownload = True

#根据收藏的分类保存到对应文件夹
favorites_list_sw = True

#没有种子的本子是否自动抓取图片保存成zip
ByDirect_sw = False

######以下不需要改动#######
if igneous == "":
    Eh_Cookie = {
        "ipb_member_id": ipb_member_id,
        "ipb_pass_hash": ipb_pass_hash,
    }
    ExHentai_Cookies = [
        {
            "name": "ipb_member_id",
            "value": ipb_member_id,
            "domain": ".e-hentai.org",
            "path": "/",
        },
        {
            "name": "ipb_pass_hash",
            "value": ipb_pass_hash,
            "domain": ".e-hentai.org",
            "path": "/",
        },
    ]
else:
    Eh_Cookie = {
        "ipb_member_id": ipb_member_id,
        "igneous": igneous,
        "ipb_pass_hash": ipb_pass_hash,
    }
    ExHentai_Cookies = [
        {
            "name": "ipb_member_id",
            "value": ipb_member_id,
            "domain": ".e-hentai.org",
            "path": "/",
        },
        {"name": "igneous", "value": igneous, "domain": ".e-hentai.org", "path": "/"},
        {
            "name": "ipb_pass_hash",
            "value": ipb_pass_hash,
            "domain": ".e-hentai.org",
            "path": "/",
        },
    ]

qbt = qbittorrentapi.Client(
    host=qbt_host, port=qbt_port, username=qbt_username, password=qbt_password
)


def validateTitle(title):
    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, "", title)  # 替换为下划线
    return new_title
