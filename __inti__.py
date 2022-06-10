import src.DoujinshiFavorites as DoujinshiFavorites
import sys
import src.DoujinshiDownlod as DoujinshiDownlod


def welcome():
    print("请输入前面的数字，以确定要执行的模式")
    print("0:刷新收藏数据库（第一次必须执行）")
    print("1:仅执行现有数据的录入，并发送下载请求")
    return input()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        i = welcome()
        if i == "0":
            DoujinshiFavorites.start()
            DoujinshiDownlod.start()
        elif i == "1":
            DoujinshiFavorites.upgradaExist()
            DoujinshiDownlod.start()
        else:
            print("错误，请输入0或1")
    elif sys.argv[1] == "-i":
        DoujinshiFavorites.upgradaExist()
        DoujinshiDownlod.start()
    else:
        print("参数错误")
