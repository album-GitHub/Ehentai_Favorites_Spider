### 源仓库：[nhysteric/Ehentai_Favorites_Spider](https://github.com/nhysteric/Ehentai_Favorites_Spider)
在原仓库基础上修复了收藏页面翻页功能，如果里站无权限则自动切换到表站获取、qb下载增加了按e站收藏夹保存到对应名字文件夹功能，并添加了直接下载存档的模式
### 简介

抓取用户Ehentai收藏的画廊及其元数据，并通过qbittorrent下载这些画廊，同时也支持直接抓取图片打包成zip或是直接下载存档

更新时，请先保存```config.py```与数据库文件，clone仓库后再进行替换


##### 来源

抓取元数据以及翻译标签的功能改写自 [nonpricklycactus/Ehentai_metadata](https://github.com/nonpricklycactus/Ehentai_metadata)
直接下载画廊的功能改写自 [HIbian/Simple_Ehentai_DownLoader](https://github.com/HIbian/Simple_Ehentai_DownLoader)
标签翻译库来自 [EhTagTranslation/Database](https://github.com/EhTagTranslation/Database)

##### 依赖的软件与库

* **目前使用的是python 3.10.8，更低或更高的环境暂未测试**，以及下列依赖库
  * lxml 4.9.2
  * mechanize 0.4.8
  * qbittorrent_api 2022.8.35
  * requests 2.28.2
* 可以使用`pip install -r requirements.txt`命令安装依赖
* **qbittorrent**，并确保打开远程访问，qb的默认Torrent管理模式不能设置为自动，否则下载路径将失效
* 最好也安装**sqlite**，以便在爬取出错时手动修改

##### 工作流程

脚本通过cookie登录Exhentai or E-hentai，扫描抓取收藏页面的画廊，将这些画廊的元数据录入sqlite数据库中。之后根据配置文件的配置，调用qbittorrent下载含有磁链的画廊、通过网页下载画廊图片，并将其打包为``.zip``格式、直接下载存档



### 如何使用

##### 参数设置

打开`config.py`，根据需要设置下列字段

* `Proxy` 代理，建议不要在本地开启代理，qb容易连不上
* `ipb_member_id` `ipb_pass_hash` `igneous` Ex cookie值，如果igneous为空的话自动切换到e-hentai下载
  
* `local_mangaPath` 本地漫画库文件夹路径，如果实际存放在远端，需要映射到本地
* `local_downloadPath` 本地下载文件夹路径，如果实际存放在远端，需要映射到本地
* `remote_mangaPath` 安装有qbittorrent的主机的远端漫画库文件夹路径
* `remote_downloadPath` 安装有qbittorrent的主机的远端下载路径
  如果你将qbittorrent安装在本地，则本地路径与远端路径是一样的，但如果你使用Docker安装qbittorrent，则远端路径为Docker容器下路径，并确保上述文件夹映射到容器
* `favoritesDB` 存放画廊收藏元数据的数据库的绝对路径，可以使用`sqlite`创建，也可以使用本脚本文件夹下``\db``文件夹中的空数据库``Eh.db``
* `translationDB`标签翻译库的绝对路径，本脚本文件夹下``\db``文件夹包含
* `qbt_host`qbittorrent主机
* `qbt_port`qbittorrent端口
* `qbt_username`qbittorrent用户名
* `qbt_password`qbittorrent密码
* `timeLimit`qbittorrent磁链下载期限，以天为单位，磁链下载时间超过该值且没有完成则删除本链接并使用下一个磁链（如果有的话）。请根据网络情况与种子活跃度酌情设置
* `maxDownloadCount`qbittorrent最大下载数，注意这不是qbittorrent同时下载数，而是发送给qbittorrent的最大任务数。请结合qbittorrent的同时下载数设置
* `directDownloadLimit`一次脚本运行期间通过网页直接下载的画廊数，是为了防止因为下载时间过长出错而设置
* `deleteAfterDownload`通过网页直接下载的画廊打包为``.zip``后，是否要删除下载的原始图片数据
* `favorites_list_sw`根据收藏的分类保存到对应文件夹
* `ByDirect_sw`没有种子的本子是否自动抓取图片保存成zip的开关
* `torrent_Download_sw`是否开启磁链下载模式
* `file_Download_sw`是否开启直接下载模式（消耗GP或下载额度）
* `checktorrent_sw`种子智能筛选开关，如果开启的话自动判断种子是否是压缩包、压缩包名称是否跟标题或日语标题相同，优先下载日语标题的种子，优先下载体积更大的种子
##### 使用

在脚本文件夹下使用命令行键入
```> python __init__.py```
脚本运行会出现输入提示，第一次使用，要键入```0```，脚本会在数据库中建表并爬取所有的收藏画廊元数据，之后进行下载流程。脚本录入数据库时会逐一检测是否已录入，当收藏画廊数过多时可能会耗费一定时间。只检查新的收藏画廊要键入```1```，这会在查询到数据库中画廊已录入时停止爬取。
```> python __init__.py -i``` 这相当于上面的键入```1```
可以使用计划任务来使脚本周期性运行
如果没有安装```sqlite```，可以使用[这个](https://inloop.github.io/sqlite-viewer/)来查看数据库

##### 数据库字段

| 字段名 |  |
|  ----  | ----  |
| gid |主键，由画廊id与画廊token构成。形如："gid/token"
|authors|艺术家名，多名艺术家以","隔开
|title|标题
|isExpunged|~~画廊是否被Exhentai删除~~ 现在isExpunged字段不再为Exhentai是否将画廊删除的字段，Exhentai标记画廊为删除仅仅是将画廊不公开，通过token依然能访问页面。现在该字段默认设置为0，并在通过网页直接下载不成功时置为1
|isExisting|记录画廊在漫画库情况<br>```exist```画廊存在<br>```undownloaded```画廊未开始下载<br>```downloading:n```画廊正在通过磁链下载，n为下载磁链的索引，以0为初始<br>```torrentFailed```所有磁链在规定时间内都没有完成下载
|groups|画廊所属的社团，多个社团以","隔开
|category|画廊分类
|tags|画廊标签，本脚本过滤了下列标签：```上传者：```、```翻译者：```、```语言：```，如有需要，请在```str.DoujinshiFavorites.toMetadata()```函数处自行更改
|characters|画廊包含的角色，多位角色以","隔开
|parody|画廊包含的题材，多个题材以","隔开
|torrentCount|画廊的磁链数量
|torrents|画廊的磁链，多个磁链以","隔开
|addDate|画廊添加进数据库的时间
|favorites_list|收藏夹名称

##### 已知的问题

* 画廊录入数据库后，画廊的元数据的更新，对画廊取消收藏等操作，脚本不会做出反应
* 没有完善的异常抛出机制与运行log记录
* 未做收藏夹名称过滤，如果收藏夹名称中有文件夹名不允许出现的字符将会无法执行下载
