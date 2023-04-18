from datetime import datetime
import sqlite3, time, os
import SimpleEhentaiDownloader as SimpleEhentaiDownloader
from config import (
    favoritesDB,
    maxDownloadCount,
    directDownloadLimit,
    qbt,
    remote_downloadPath,
    timeLimit,
    remote_mangaPath,
    favorites_list_sw,
    ByDirect_sw,
    validateTitle,
)


mangetHead = "magnet:?xt=urn:btih:"


def getFileName(title: str, authors: str):
    if authors == "":
        return title
    return validateTitle("[" + authors + "] " + title)


def updateDownload(gid, state):
    con = sqlite3.connect(favoritesDB)
    cur = con.cursor()
    cur.execute("update favorites set isExisting = ? where gid = ?", (state, gid))
    con.commit()
    cur.close()
    con.close()


def updateExpunged(gid, state):
    con = sqlite3.connect(favoritesDB)
    cur = con.cursor()
    cur.execute("update favorites set isExpunged = ? where gid = ?", (state, gid))
    con.commit()
    cur.close()
    con.close()


def refreshDownloading() -> int:
    con = sqlite3.connect(favoritesDB)
    cur = con.cursor()
    cur.execute(
        "select gid,torrents,torrentCount,isExisting,authors,title,favorites_list from favorites where isExisting like 'downloading%'"
    )
    rows = cur.fetchall()
    cur.close()
    con.close()
    count = len(rows)
    for row in rows:
        gid = row[0]
        torrents = row[1].split(",")
        torrentCount = row[2]
        isExisting = row[3]
        Tail_path = row[6]
        n = int(isExisting.split(":")[1])
        info = qbt.torrents_info(torrent_hashes=torrents[n])
        if favorites_list_sw:
            downloadPath = remote_downloadPath +'/' + Tail_path
        else:
            downloadPath = remote_downloadPath
        print('downloadPath',downloadPath,'len(info)',len(info))
        if len(info) == 0:
            print('种子未下载')
            updateDownload(gid, "undownloaded")
            continue
        if info[0]["progress"] == 1:
            if loadManga(torrents[n]):
                updateDownload(gid, "exist")
                print(info["name"] + "录入")
            count -= 1
        else:
            addTime = datetime.fromtimestamp(info["added_on"])
            timeDifference = (datetime.fromtimestamp(time.time()) - addTime).days
            if timeDifference > timeLimit:
                qbt.torrents_delete(delete_files=True, torrent_hashes=torrents[n])
                if n + 1 >= torrentCount:
                    updateDownload(gid, "torrentFailed")
                else:
                    qbt.torrents_add(
                        urls=mangetHead + torrents[n + 1],
                        save_path=downloadPath,
                        #category="本子",
                        rename=info[0]["name"],
                    )
                    updateDownload(gid, "downloading:" + str(n + 1))
    return maxDownloadCount - count if maxDownloadCount - count > 0 else 0


def loadManga(torrent_hash):
    slash = "\\" if "\\" in remote_mangaPath else "/"
    info = qbt.torrents_info(torrent_hashes=torrent_hash)[0]
    name = validateTitle(info["name"])
    ext = os.path.splitext(
        qbt.torrents_files(torrent_hash=torrent_hash, file_ids=0, priority=0)[0]["name"]
    )[-1]
    qbt.torrents_rename_file(
        torrent_hash=torrent_hash, file_id=0, new_file_name=name + ext
    )
    qbt.torrents_set_location(
        location=remote_mangaPath + slash + name, torrent_hashes=torrent_hash
    )
    return True


def downloadByTorrent(torrentHash, name, Tail_path):
    url = mangetHead + torrentHash
    #根据收藏的分类保存到对应文件夹
    if favorites_list_sw:
        downloadPath = remote_downloadPath +'/' + Tail_path
    try:
        qbt.torrents_add(
            urls=url,
            save_path=downloadPath,
            #download_path=downloadPath,
            #category="本子",
            rename=name,
        )
    except Exception as e:
        print(e)
        return False
    return True


def downloadByDirect(gid, downloadName, Tail_path):
    try:
        zipPath = SimpleEhentaiDownloader.downloadByPage(gid, downloadName, Tail_path)
        SimpleEhentaiDownloader.loadManga(zipPath)
    except IndexError:
        print(downloadName + "已被Exhentai删除")
        return False
    return True


def start():
    con = sqlite3.connect(favoritesDB)
    cur = con.cursor()
    count = refreshDownloading()
    cur.execute(
        "select gid,torrents,torrentCount,authors,title,isExisting,favorites_list from favorites where isExisting = 'undownloaded' and torrentCount>0 limit ?",
        [str(count)],
    )
    rows = cur.fetchall()
    cur.execute(
        "select gid,torrents,torrentCount,authors,title,isExisting,favorites_list from favorites where ( isExisting!='exist' and isExpunged==0) and (torrentCount<=0 or isExisting =='torrentFailed') limit ?",
        [str(directDownloadLimit)],
    )
    rows.extend(cur.fetchall())
    cur.close()
    con.close()
    for row in rows:
        gid = row[0]
        torrents = row[1].split(",")
        torrentCount = row[2]
        name = getFileName(authors=row[3], title=row[4])
        state = row[5]
        Tail_path = row[6]
        if torrentCount > 0 and state == "undownloaded":
            if downloadByTorrent(torrents[0], name, Tail_path):
                updateDownload(gid, "downloading:0")
        else:
            #如果开启无磁链直接下载则抓取图片链接直接下载打包zip
            if ByDirect_sw:
                if downloadByDirect(gid, name, Tail_path):
                    updateDownload(gid, "exist")
                else:
                    updateDownload(gid, "failed")
                    updateExpunged(gid, True)
