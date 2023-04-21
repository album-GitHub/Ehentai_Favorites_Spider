import sys
sys.path.append('./src')
import DoujinshiFavorites as DoujinshiFavorites
from urllib.error import URLError
from Browser import Browser
import config, os, sys
import DoujinshiDownlod as DoujinshiDownlod


def welcome():
    print("请输入前面的数字，以确定要执行的模式")
    print("0:创建并完整爬取收藏数据库，第一次或在上一次完整爬取时出错需要执行")
    print("1:刷新收藏画廊，并发送下载请求")
    print("2:获取数据库中喂下载的本子，并发送下载请求")
    return input()

def test():
    if not os.path.isdir(config.local_mangaPath) or not os.path.isdir(
        config.local_downloadPath
    ):
        print("无法访问本地漫画或是下载路径，请检查相关设置")
        return False
    if not os.path.isfile(config.favoritesDB) or not os.path.isfile(
        config.translationDB
    ):
        print("无法访问数据库文件，请检查相关设置")
        return False
    try:
        config.qbt.auth_log_in()
        config.qbt.auth_log_out()
    except:
        print("无法连接到qbit,请检查qbit设置") 
        return False
    if config.igneous == "":
        url = "https://e-hentai.org/"
    else:
        url = "https://exhentai.org/"
    br = Browser()
    br.set_proxies(proxies=config.Proxy, proxy_bypass=lambda hostname: False)
    br.addheaders = [
        (
            "User-agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
        )
    ]
    br.set_handle_robots(False)
    for cookie in config.ExHentai_Cookies:
        br.set_cookie(
            name=cookie["name"],
            value=cookie["value"],
            domain=cookie["domain"],
            path=cookie["path"],
        )
    try:
        _raw = br.open_novisit(url)
        raw = _raw.read()
        if raw == b"":
            print("cookie错误，请检查cookie")
            return False
    except URLError:
        print("无法访问exhentai，请检查代理")
        return False
    except Exception:
        print("网络错误，请检查相关设置")
        return False
    return True


def start():
    if len(sys.argv) != 2:
        i = welcome()
        if i == "0":
            DoujinshiFavorites.start(True)
            DoujinshiDownlod.start()
        elif i == "1":
            DoujinshiFavorites.start(False)
            DoujinshiDownlod.start()
        elif i == "2":
            DoujinshiDownlod.Downloading()
        else:
            print("错误，请输入0或1或2")
    elif sys.argv[1] == "-i":
        DoujinshiFavorites.start(False)
        DoujinshiDownlod.start()
    else:
        print("参数错误")


if __name__ == "__main__":
    if test():
        start()
