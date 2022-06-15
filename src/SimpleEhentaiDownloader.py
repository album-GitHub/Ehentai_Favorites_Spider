import os, time, requests, zipfile, shutil
from lxml import etree
from config import (
    Proxy,
    local_downloadPath,
    Eh_Cookie,
    local_mangaPath,
    deleteAfterDownload,
    validateTitle,
)


header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/93.0.4577.82 Safari/537.36 ",
    "Connection": "close",
}


# 经过测试,通过网页下载最高分辨率图片时,下载十张左右后后续图片分辨率会变成低分辨率,加上header_img可解决.head_img中影响下载分辨率参数不详,目前是all-in
header_img = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "zh-CN,zh;q=0.9",
    "cache-control": "no-cache",
    "Connection": "close",
    "pragma": "no-cache",
    "referer": "https://e-hentai.org/g/944656/0c2120f188/",
    "sec-ch-ua": '"Google Chrome";v="95", "Chromium";v="95", ";Not A Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36",
}

# 下载用header
header_download = {
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "close",
    "Pragma": "no-cache",
    "Referer": "https://e-hentai.org/",
    "sec-ch-ua": '"Google Chrome";v="95", "Chromium";v="95", ";Not A Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "image",
    "Sec-Fetch-Mode": "no-cors",
    "Sec-Fetch-Site": "cross-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36",
}


def getHTML(url):
    global header
    get_html = ""
    while get_html == "":
        try:
            get_html = requests.get(
                url, headers=header, proxies=Proxy, cookies=Eh_Cookie
            ).content.decode("utf-8")
        except requests.exceptions.SSLError:
            print("Connection refused by target server...sleep 1s")
            time.sleep(1)
            continue
        except requests.exceptions.ProxyError:
            print("Connection refused by proxy server...sleep 1s")
            time.sleep(1)
            continue

    return etree.HTML(get_html)


def getIMGHTML(url, header_img):
    get_html = ""
    while get_html == "":
        try:
            get_html = requests.get(
                url, headers=header_img, proxies=Proxy, cookies=Eh_Cookie
            ).content.decode("utf-8")
        except Exception as e:
            print(e)

    return etree.HTML(get_html)


def pageGraber(g_url, pageCount):
    page_url_list = []
    # page starts from zero
    page_url = g_url + "?p={}"
    page_no = 0
    while page_no < pageCount:
        page_html = getIMGHTML(page_url.format(page_no), header_img)
        page_url_list.extend(page_html.xpath('//*[@id="gdt"]/div/div/a/@href'))
        page_no += 1
    return page_url_list


def imgUrlGraber(page_url_list):
    global header_img
    img_url_list = []
    for page_url in page_url_list:
        img_html = getIMGHTML(page_url, header_img)
        img_url = img_html.xpath('//*[@id="img"]/@src')[0]
        img_url_list.append(img_url)
    return img_url_list


def imgUrlGraberAndDownload(page_url_list, title, path):
    def downloadImg(_img_url, _img_dir):
        count = 0
        resp = None
        while count < 5:
            try:
                resp = requests.get(
                    url=_img_url,
                    headers=header_download,
                    proxies=Proxy,
                    cookies=Eh_Cookie,
                )
                img_name = _img_url.split("/")[-1]
                with open(os.path.join(_img_dir, img_name), "wb+") as f:
                    f.write(resp.content)
                break
            except:
                count += 1
                continue

    def createZip(path):
        zipPath = path + ".zip"
        zip = zipfile.ZipFile(zipPath, "w")
        for file in os.listdir(path):
            zip.write(
                os.path.join(path, file),
                compress_type=zipfile.ZIP_DEFLATED,
                arcname=file,
            )
        zip.close()
        if deleteAfterDownload:
            shutil.rmtree(path)
        return zipPath

    img_dir = str(os.path.join(path, validateTitle(title)))
    try:
        os.makedirs(img_dir)
    except OSError:
        pass
    except Exception as e:
        print(e)

    global header_img

    count = 0
    total = len(page_url_list)
    for page_url in page_url_list:
        # count += 1
        # if count <= 42:
        #     continue
        # 获取url
        img_html = getIMGHTML(page_url, header_img)
        img_url = img_html.xpath('//*[@id="img"]/@src')[0]
        # 下载图片
        downloadImg(img_url, img_dir)
        count += 1
        print("down {}/{}.".format(count, total))
    return createZip(img_dir)


def get_info(url):
    # todo 获取分页信息
    html = getHTML(url)
    info = []
    for div in html.xpath("/html/body/div[2]/form/div[2]/div"):
        href = div.xpath("./div/div/a")[0].attrib["href"]
        title = div.xpath("./div/div/a/span")[0].text
        info.append((title, href))
    return info


def downloadByPage(gid, title):
    print(title, "开始下载")
    g_url = "https://exhentai.org/g/" + gid
    html = getHTML(g_url)
    pageCount = (
        int(
            int(
                html.xpath("/html/body/div[2]/div[3]/div[1]/div[3]/table/tr[6]/td[2]")[
                    0
                ].text.split(" ")[0]
            )
            / 40
        )
        + 1
    )
    global header_img
    header_img["referer"] = g_url
    try:
        page_url_list = pageGraber(g_url, pageCount)
        zipPath = imgUrlGraberAndDownload(
            page_url_list=page_url_list, title=title, path=local_downloadPath
        )
    except:
        raise Exception("下载失败")
    return zipPath


def loadManga(zipPath):
    dirName = validateTitle(".".join(os.path.basename(zipPath).split(".")[:-1]))
    try:
        os.makedirs(os.path.join(local_mangaPath, dirName))
        os.rename(
            zipPath, os.path.join(local_mangaPath, dirName, os.path.basename(zipPath))
        )
    except:
        raise Exception("io错误")
