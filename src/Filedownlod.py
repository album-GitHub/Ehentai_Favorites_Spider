from lxml import etree
import sys
sys.path.append('..')
from Browser import Browser
from SimpleEhentaiDownloader import Original_download
from config import (
    ExHentai_Cookies,
    Proxy,
    local_downloadPath,
    local_mangaPath,
    favorites_list_sw,

)

def fileDownloader(gid_token,Tail_path):
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
    url = 'https://e-hentai.org/g/'+str(gid_token)
    _raw = br.open_novisit(url)
    raw = _raw.read()
    #解码为html
    html = etree.HTML(raw)
    filelinkpath = html.xpath('//p[@class="g2 gsp"]/a/@onclick')
    
    #分割成列表，提取下载页链接部分
    pathlink = (filelinkpath[0].split("'"))[1]

    #进入链接提取页面 此链接用不同方式访问将获得不同结果，既是文件链接也是下载页面链接
    lingpathraw = br.open_novisit(pathlink)
    pathraw = lingpathraw.read()
    pathhtml = etree.HTML(pathraw)
    pathlink = pathhtml.xpath('string(//*[@id="db"]/p/a/@href)')

    #进入文件下载页面获取文件名称
    jump_raw = br.open_novisit(pathlink)
    _jupmraw = jump_raw.read()
    jumphtml = etree.HTML(_jupmraw)
    filename = jumphtml.xpath('//*[@id="db"]/p/strong/text()')
    #根据情况生成完整文件路径
    if favorites_list_sw:
        path = local_mangaPath + Tail_path + filename[0]
    else:
        path = local_downloadPath + filename[0]
    #传递给文件下载模块
    result = Original_download(pathlink,path)
    if result:
        print('文件'+str(filename[0])+'下载完成')
        return result
    else:
        return result
    


    