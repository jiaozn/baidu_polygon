#!usr/bin/env python  
#-*- coding:utf-8 _*-  

""" 
@Author: SMnRa 
@Email: smnra@163.com
@Project: baidu_polygon
@File: baidu.py 
@Time: 2019/05/09 9:53

功能描述: 百度地图 电子边框


"""
import time,json,os
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import  expected_conditions as EC
from selenium.webdriver.common.by import By
import coordinateTranslate






# 初始化坐标系转化对象
coordTrans = coordinateTranslate.GPS()
def miToGPS(lon, lat):
    coord = coordTrans.convert_BD09MI_to_WGS84(float(lon), float(lat))
    return coord





def getUserAgent():
    ua = UserAgent()  # 初始化 随机'User-Agent' 方法
    tmpuserAnent =  'user-agent="'+ ua.random + '"'
    return tmpuserAnent

def seleniumChromeInit():
    # 模拟创建一个浏览器对象，然后可以通过对象去操作浏览器
    driverPath = r'./Chrome/Application/chromedriver.exe'
    downloadPath = r'C:\Users\Administrator\Downloads'
    # 浏览器驱动
    userAnent = getUserAgent()
    options = webdriver.ChromeOptions()
    prefs = {'profile.default_content_settings.popups': 0, 'download.default_directory': downloadPath}
    options.add_experimental_option('prefs', prefs)
    # 更换头部
    options.add_argument(userAnent)
    # options.add_argument("--no-sandbox")
    # options.add_argument('--headless')
    browserDriver = webdriver.Chrome(executable_path=driverPath, chrome_options=options)
    # browserDriver.maximize_window()     # 设置最大化
    # browserDriver.set_window_size(1366,900)
    action = ActionChains(browserDriver)
    return browserDriver





def webLoadComplate(browserDriver, id):
    # 等到id 元素载入完成 返回该元素
    try:
        # 等待到 元素载入完成  元素 出现
        element = WebDriverWait(browserDriver, 20).until(EC.presence_of_element_located((By.ID, id)))
    except Exception as e:
        print(e)
        time.sleep(1)
        return webLoadComplate(browserDriver, id)
        # 迭代本方法 直到加载完成...
    return element



def isJsonStr(jsonStr):
    # 判断一个字符串似否是json格式
    try:
        json.loads(jsonStr)
    except ValueError:
        return False
    return True


def toJson(text):
    # 字符串 反序列化
    if isJsonStr(text):
        return json.loads(text)



def isDictKey(mDict, *mKey):
    # 判断 字典 mDict 存在 mKey, 并且 mKey 的值为 字典类型 返回True 否则返回 False
    tempDict = dict(mDict)
    tag = True  # 是否无效标记
    rdict = None
    for key in mKey:
        if key in tempDict.keys() and isinstance(tempDict[key], dict):
            tempDict = tempDict.get(key, '')
            if not isinstance(tempDict, dict):
                print(key, "is not dict.")
                tag = False
            else:
                tag = True
        else:
            tag = False
    if tag:
        rdict = dict(tempDict)
    return rdict



def newTabGet(browserDriver, url):
    js = " window.open('')"
    browserDriver.execute_script(js)
    # 可以看到是打开新的标签页 不是窗口
    window = browserDriver.window_handles
    # 获取窗口(标签)列表
    browserDriver.switch_to.window(window[1])
    # 切换到新标签
    browserDriver.get(url)
    html = browserDriver.page_source

    try:
        preTag = jsonText = ''
        preTag = browserDriver.find_element_by_xpath("//pre")
        # 查找<pre> 标签
        if preTag and isJsonStr(preTag.text):
            jsonText = toJson(preTag.text)

        if html and isJsonStr(html):
            jsonText = toJson(jsonText.text)

    except Exception as e:
        print(e)

    browserDriver.close()
    browserDriver.switch_to.window(window[0])

    return jsonText


def clearCoord(coordStr):
    # 整理坐标数据
    coordStr = coordStr.split('|')[2]
    coordStr = coordStr.replace("1-", "").replace(";", "")
    coordList = '[' + coordStr + ']'
    coordList = eval(coordList)
    return list(zip(*(iter(coordList),) * 2))




def stripStr(tmp):
    # 删除字符串中的不可见字符
    result = str(tmp)
    result = result.strip()
    result = result.replace(",", ';')
    result = result.replace("\n", '')
    result = result.replace("\r", '')
    result = result.replace("\t", ' ')
    result = result.strip()
    return result




def searchPoi(browserDriver, buildName):
    # if self.searchAmap(browserDriver,searchBoxId, "安康学院"):
    #     print(browserDriver.title)
    # 返回 请求的返回数据

    searchUrl = 'http://api.map.baidu.com/?qt=s&c=131&rn=100&ie=utf-8&oue=1&res=api&wd='
    url = searchUrl + buildName

    # 在新标签中打开url
    result = newTabGet(browserDriver, url)

    poiInfo = []
    if isinstance(result, dict):
        # result 字典存在 key  'content' 并且 result['content'] 是列表
        if 'content' in result.keys() and isinstance(result['content'], list):
            pois = result.get('content')  # poi的列表
        else:
            print(" Not found poi.")
            return False

        for poi in pois:
            (pylgon, geoMi, x, y, lon, lat) = [[], '', '', '', '', '']  # 清空变量
            try:
                geoMi = isDictKey(poi, 'ext', 'detail_info', 'guoke_geo')
                if isinstance(geoMi, dict):
                    geoMi = geoMi.get('geo', '')
                    if geoMi:
                        # 如果存在 多边形边界
                        poiGeo = clearCoord(geoMi)
                        # print(poiGeo)
                        for coord in poiGeo:
                            # 由百度墨卡托坐标系 转换为 WGS-84 坐标系
                            gps = miToGPS(coord[0], coord[1])
                            pylgon.append([str(gps['lon']), str(gps['lat'])])
                        pylgon = ";".join([' '.join(node) for node in pylgon])
                        # print(pylgon)
                if not pylgon: pylgon = ''

            except Exception as e:
                print(e)

            try:
                csvName = buildName
                name = stripStr(poi.get('name', ''))
                uid = stripStr(poi.get('uid', '')) or ''
                alias = stripStr(poi.get('alias', ''))
                addr = stripStr(poi.get('addr', ''))
                address_norm = stripStr(poi.get('address_norm', ''))
                area = stripStr(poi.get('area', ''))
                area_name = stripStr(poi.get('area_name', ''))
                catalogID = stripStr(poi.get('catalogID', ''))
                di_tag = stripStr(poi.get('di_tag', ''))
                primary_uid = stripStr(poi.get('primary_uid', ''))
                std_tag = stripStr(poi.get('std_tag', ''))
                std_tag_id = stripStr(poi.get('std_tag_id', ''))
                tel = stripStr(poi.get('tel', ''))

                if isinstance(poi.get('x', ''), int):
                    x = poi.get('x', '') / 100
                    y = poi.get('y', '') / 100

                    pointGps = miToGPS(x, y)
                    lon = str(pointGps.get('lon', ''))
                    lat = str(pointGps.get('lat', ''))
                    x = str(x)
                    y = str(y)

                poiInfo.append(",".join(
                    [csvName, name, uid, primary_uid, alias, addr,
                     address_norm, area, area_name, catalogID, di_tag,
                     std_tag, std_tag_id, tel, x, y, lon, lat, pylgon + '\n'])
                )
                print(",".join(
                    [csvName, name, uid, primary_uid, alias, addr,
                     address_norm, area, area_name, catalogID, di_tag,
                     std_tag, std_tag_id, tel, x, y, lon, lat, pylgon + '\n']))

            except Exception as e:
                print(e)

        with open(r'./baidu.csv', mode='a+', encoding='gbk', errors=None) as f:  # 将采集数据写入文件
            f.writelines(poiInfo)



if __name__ == '__main__':
    # 初始化selenium Chrome 对象
    browserDriver = seleniumChromeInit()

    # 打开amap 首页 等待网页加载完成
    url = 'https://map.baidu.com/'
    browserDriver.get(url)

    # 暂停2秒，已达到完全模拟浏览器的效果
    time.sleep(2)

    # 等待 搜索框元素 加载完成
    searchBoxId = 'sole-input'
    searchBox = webLoadComplate(browserDriver, searchBoxId)
    print("OK")

    # 如果不存在r'./baidu.csv'  则建立并写入表头
    if not os.path.isfile(r'./baidu.csv'):
        with open(r'./baidu.csv', mode='a+', encoding='gbk', errors=None) as f:  # 将表头写入文件
            f.writelines("csvName,name,uid,primary_uid,alias,addr,address_norm,area,area_name,catalogID,di_tag,std_tag,std_tag_id,tel,x,y,lon,lat,geo\n")


    nameList =  ["西安交大", "西工大","西京医院","唐都医院","东方米兰"]

    for name in nameList:
        searchPoi(browserDriver, name)
        # searchBoxGetPoiInfo(name)
        print(name)




