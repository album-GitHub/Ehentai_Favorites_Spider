from datetime import datetime
import sqlite3, time, os
import src.SimpleEhentaiDownloader as SimpleEhentaiDownloader
from config import (
    favoritesDB,
    maxDownloadCount,
    directDownloadLimit,
    qbt,
    remote_downloadPath,
    timeLimit,
    remote_mangaPath,
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


def refreshDownloading() -> int:
    con = sqlite3.connect(favoritesDB)
    cur = con.cursor()
    cur.execute(
        "select gid,torrents,torrentCount,isExisting,authors,title from favorites where isExisting like 'downloading%'"
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
        n = int(isExisting.split(":")[1])
        info = qbt.torrents_info(torrent_hashes=torrents[n])[0]
        if info["progress"] == 1:
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
                        urls=mangetHead + torrents.split(",")[n],
                        download_path=remote_downloadPath,
                        category="本子",
                        rename=info["name"],
                    )
                    updateDownload(gid, "downloaded:" + str(n + 1))
    return maxDownloadCount - count


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


def downloadByTorrent(torrentHash, name):
    url = mangetHead + torrentHash
    try:
        qbt.torrents_add(
            urls=url,
            save_path=remote_downloadPath,
            download_path=remote_downloadPath,
            category="本子",
            rename=name,
        )
    except Exception as e:
        print(e)
        return False
    return True


def downloadByDirect(gid, downloadName):
    try:
        zipPath = SimpleEhentaiDownloader.downloadByPage(gid, downloadName)
        SimpleEhentaiDownloader.loadManga(zipPath)
    except Exception as e:
        print(e)
        return False
    return True


def start():
    con = sqlite3.connect(favoritesDB)
    cur = con.cursor()
    count = refreshDownloading()
    cur.execute(
        "select gid,torrents,torrentCount,authors,title,isExisting from favorites where isExisting = 'undownloaded' and torrentCount>0 limit ?",
        [str(count)],
    )
    rows = cur.fetchall()
    cur.execute(
        "select gid,torrents,torrentCount,authors,title,isExisting from favorites where ( isExisting!='exist' ) and (torrentCount<=0 or isExisting =='torrentFailed') limit ?",
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
        if torrentCount > 0 and state == "undownloaded":
            downloadByTorrent(torrents[0], name)
            updateDownload(gid, "downloading:0")
        else:
            downloadByDirect(gid, name)
            updateDownload(gid, "exist")
