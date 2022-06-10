import re, qbittorrentapi


Proxy = {"http": "http://localhost:1080", "https": "http://localhost:1080"}


ipb_member_id = "4xxxx"
ipb_pass_hash = "4xxxxx"
igneous = "6xxxxx"


local_mangaPath = r"\\QHHH\Book\Doujinshi"
local_downloadPath = r"\\QHHH\Book\Torrents"
remote_mangaPath = r"/Book/Doujinshi"
remote_downloadPath = r"/Book/Torrents"


favoritesDB = r"C:\Code\Ehentai_Favorites_Spider\db\Eh.db"
translationDB = r"C:\Code\Ehentai_Favorites_Spider\db\EhTagTranslation.db"


qbt_host = "xx.xx"
qbt_port = 11451
qbt_username = "xxx"
qbt_password = "xxxx"
timeLimit = 7
maxDownloadCount = 20


directDownloadLimit = 10
deleteAfterDownload = True


######以下不需要改动#######

Eh_Cookie = {
    "ipb_member_id": ipb_member_id,
    "igneous": igneous,
    "ipb_pass_hash": ipb_pass_hash,
}
ExHentai_Cookies = [
    {
        "name": "ipb_member_id",
        "value": ipb_member_id,
        "domain": ".exhentai.org",
        "path": "/",
    },
    {"name": "igneous", "value": igneous, "domain": ".exhentai.org", "path": "/"},
    {
        "name": "ipb_pass_hash",
        "value": ipb_pass_hash,
        "domain": ".exhentai.org",
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
