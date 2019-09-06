"""
Get the images in the Tool Bar
"""

import os
import io

import wx
from wx import ImageFromStream, BitmapFromImage

#----------------------------------------------------------------------
def getNewData():
    return \
'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x0f\x08\x06\
\x00\x00\x00\xedsO/\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\x00\
\x00YIDATx\x9c\xed\xd31\n@!\x0c\x03\xd0\xa4\xfe\xfb\xdfX\xe3\xf0\x97R\xa5(.\
\x0ef\x13\xe45\xa2\x92Vp\x92\xcf/\xd4\xaa\xb2\xcd\xb4\xc2\x14\x00\x00in\x90\
\x84ZUDl\xa9\xa7\xc3c\xcb-\x80\xfc\x87{d8B6=B\xdb\rfy\xc0\r\xc0\xf0\x0e\xfc\
\x1d\xaf\x84\xa7\xbf\xb1\x03\xe1,\x19&\x93\x9a\xd2\x97\x00\x00\x00\x00IEND\
\xaeB`\x82'

def getNewData2():
    return \
"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x01\x04IDAT8\x8d\xa5\x93\xbdj\x02A\x10\xc7\x7f{gme\xe5c\xe4\t\x82\x85\
\x85\x85oa\xe5+\xd8Z\xd8'e\xfa\x80\xd8\xd8X\x19R\xc4\x07\x90\x04\xd1J\x08\
\x17\x0cr\\V\xe1\xe4\xfc\x80\xb58\xf7\xd8\xbd\x0f\xa280\xec\xec2\xbf\xff\xce\
\xcc\xb2B8.\xf7X\xc9\xdc|L\x97J\xc7\xbe\x0c\x01\xf0\xd6\x01\x00RFtZu\x91Q\
\x10\x8e\x9b\xf8\xe4\xf3[-w*\xf1\xafm\xec\xcf\x83\x89\x1a\xad\x94\xea\xbe\
\x8c\x95\x99/\x1c\x17\xe7\xdaR\xcb%xh\xd4hw_\x95yn\xb5\xe0\xcb\x90\xea%\x0eO\
\xf1\xba\xd9\xc7\xe5\xbf\x0f\xdfX]\xda)\x140A\r\x03<6klO\xf0w\x84~\xef\xc9\
\xca/lA\xc3@\x02\xe7\x99U\x81\xb7\x0e\xa8\xec\xed\x04\x13\xde\x1c\xfe\x11\
\x902\xb2@\xc8\xc2\x8b\xd9\xbcX\xc0\x045\xac\xc1 Jg\xe6\x08\xe8)\xa7o\xd5\
\xb0\xbf\xcb\nd\x86x\x0b\x9c+p\x0b\x0c\xa9\x16~\xbc_\xeb\x9d\xd3\x03\xcb3q\
\xefo\xbc\xfa/\x14\xd9\x19\x1f\xfb\x8aa\x87\xf2\xf7\x16\x00\x00\x00\x00IEND\
\xaeB`\x82"

def getNewBitmap():
    return BitmapFromImage(getNewImage())

def getNewImage():
    stream = io.BytesIO(getNewData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------
def getOpenData():
    return \
'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x01gIDAT8\x8d\xa5\x93=KBQ\x18\xc7\x7fWo)5\x1594DC\x04!\xd1\x0bM-\xd1\
\xd0T\x81\xba\xb7\xf8\x01Z\x9a\xdb\xfa\x08AC\x10\x0e\xb5\x86\xbaDC`CMaN\xd9\
\x0bQF7\xe2z\xc1kz\xcd\xc4\x97\xd3\xa0\xde\xbc\\oE\xfd\xa7s\xce\xf3\xfc\x7f\
\xe7y\xce\x8b$\xb9\xdc\xfcG2@\xf1bC\x00\x18%\xcd\x12\x1c^\xdc\x97~\x04\x18\
\xe7K\xa2of\x05\x80\xfe\x8e@\xc3\xc8\xf2zJ\x13\xac+\xe6\xfax(a\x81\xca\xa2w\
\x8a\x86\x91\x85\xaanE\xf7\x0c\xe0\xf3\xcf\x03P}|3\x97\x93\x11U\xcc\x85\xd3&\
D\xee\xf4\x88\xb2\xfa5)\xab(\x99"\x00\xb9\x87c\x0b;\x19\xf1\x0b\x80\xb9pZ\
\xb2\x00\x00\xd3T\xcb\xa5\x00(\xe4Uf\xd7\xb6m\xbd\xa7\x0e\xd6\x89\xc7\xa2\
\xc2\x04<_\xdf\xe3\x15\x1a\xb5V\xbfc\xab\x9b6S7\xc9FIC\xbf\xcb\xe0\x15\x1a\
\xbe\xe9e|\xad@C\xbfu4\x9d\xecnQ\x99\xdci\x02\x00\xea\x1f\x1a\x15]a\xa8pcK\
\xae\xbf?9\x82\x02\xc1\x90$\x1b\xba\x82<\xe8\xeb\x9a\\\xcb)\xdd|\x14r\x15<\
\xad\xb1\xab\x99\x98bdb\xd4q\xa7\xefd\xbb\x05\xa7\xdd\x8f\x0e/\x9d\x01\x85\
\xbc\nX+8K\\\x99\xe5\x02x\x16\xf6\xba\x02$\xc9\xe56\x1fF[\xda\x8bn\x9er\xa7\
\x02\xc1\x90\xedoH\xed\xdf\x18\x8fE\xc5o\x0c\x8e\x80\xbf\xea\x13\xa8\x18\x89\
5\xe7L\xb3:\x00\x00\x00\x00IEND\xaeB`\x82'

def getOpenBitmap():
    return BitmapFromImage(getOpenImage())

def getOpenImage():
    stream = io.BytesIO(getOpenData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------
def getCopyData():
    return \
'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x01_IDAT8\x8d\x8d\x92\xbfK\x02a\x18\xc7?w\xfa\'\xd8\xd0\xa0\xe4v\xd0$M\
\x8dB\x11\x11\xa5B\x7f@C\xd0RC{k8E\x834\xb45\n\x15\xfd\x80hhh\xd2\xadI\x82\
\xa4!\xb8\x84\xca\xd4;\xa5\xf2R\xe1m\xd0\xfb\xf5^\x1e~\xe1\xe5^\x9e{\xbe\x9f\
\xf7\xfb\xbcwJ\xa9\xa2\x0bFj\x98\xdf\x00\xd4\xea\x06\x00f\xdbbosQ!L\xa5\x8a.\
\xaa_"\xb0\x8e\xce\xcb\xa2\xfc)\xc4N\xfeT(j\x84\xb1\xabT\xd1E,\x19w\x80\x8d\
\x97Ww?A"\xd5n\xf2*\x96\x8c\x13K\xc6\xd1R\x1aZJcai\x1e\x80\xf4j\x9a\xed\xfd\
\xa2\xf0\x01B\xe7\x1b\xa9\xd9\x1d>;\x03X\xd9X\xf7AToC\xb3\xeb\xc6\x96e\xb6-\
\x1en\xef\xb999\x03\xe0\xea\xf2B\x00Dku\x83)\xcd\x85\x8c;}n9\r\x80\xd1\x87b\
\xbe\x00\xb33\xc3\x04f\xdbr\x9a;\x03\xbfI\x86\x1a\xfd\xe0\x01\xaam\xec\x0c\
\x86\r\xf6\x8d{\xcd\xf6;\x00\xb3\'\x01\xde?\x9a>\xba\x9cH6\xb7,x~\xaa:=Q\x9f\
\xb9\xe7\x1fE\xae\xb7\\\xb6\x1f\xe0\x8d\x15H$\x99\x1b?\x12@\xd7\xdf\xd0\x0f\
\nN!\x91\x98\x9e\xd8\x0c\x10\xbd>\xdeU\xeco\np\xf7\xf8\xebK\x14fvF\xc8ds\xce\
\xff\xbd\xb6u(\xbc\x89\xbc\x17\xf6\x9f\x14E\x8d\x04\x8a\xdeDa\xcads\xca\x1f\
\x0cI\xd4\xda\x88E\x9d\xc4\x00\x00\x00\x00IEND\xaeB`\x82'

def getCopyBitmap():
    return BitmapFromImage(getCopyImage())

def getCopyImage():
    stream = io.BytesIO(getCopyData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------
def getPasteData():
    return \
"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x01\x90IDAT8\x8d\x8d\x93?H\x02a\x18\x87\x9fSw\xb1\xa9!q\xc8\xb0?B\xd0\
\x98\x10DS\x10\x98\x82C\xd1\x12\x1a\xcd\rb&\xad\x1a\x144F`[\xd4 hBPKC\x83P\
\x8b4\xe4\xa9tP\x82\x98\x88`$\x82\x8b\xd8p\xddu\xa7\xa5\xfd\x96{\xbf\xef\xfd\
\xbd\xcf\xf7~w\xf7\n\x82\xc1\x08@M\xect\xd1(x\x12ef\xcaN./\x11\\\xdc\xd3\xa6\
pz\x8d\x82\x12\x0b\x82\xc1HM\xect-c\xf7\xaa!\x10\xc9\xe0]rR\xac\xb4\x01\xc8\
\xe5%\xe2\xbbF5_|\x0c\xa9\x10\x03=\nD2\x00$\xef\x9e\xc9\xe5%ryI\xde?\xe8\xe8\
|\xe9\xabT\x17\xc0\xd4\x0b\xd8\nl\xa8q\xfd\xa3%\xb7\xd9x\xe1\xad=\xc2q\xba\
\xc2\x8e\xfbU\xe7\xef\x03\x00\x98m\xd6\xef\xa7\xb23\xc9\xdbm\x06\xfb\x8a\x8f\
\xe0y\x8a\xc0\xc4\x10\x00\xc0\xcdEB\x8d\x97\xd7}j\xbc\xb0\xe6!~\x99d\xd11\
\x04\xa0-R$]'\xa84M4\xca\x05p8\x7f\x07\xd4?Z\x98mr\x07\x95\xa6\x9c\xf6o{\xb0\
\xce\xbb\x00\xb0\x03\xe9\xc3\xd8\xf0+h;x\xf9\xfc\xcb\xd5\x0bh>Pzw1>\x0bg\xa7\
)]\xaaQ.\x00`\xdb\x0c\x0f\x00hN\xf4o{~=\xf9\xa9\x0eY\xb1\x8awI\xf3\x0ej\x05\
\xb0\x98\x1f\x00x-\xd5\xb0\xce\xc3\xd1~LW\x98\x15\xab\xccM\x8f\xfe\xaf\x03\
\x00w0\xccS\xfdgm\xfb\xc3\xd7\xf7++w\xd5\x16\x0f\x92\t\xe4\xe9zN\x86\xbe\xa7\
1\xaa\xfbLY\xb1:\x10 (\xe3\x0c?\x03\xf2_\xb9W=\xc2\x17\x1c\xf8\x87\x9a\x03\
\x12\xd7\xb9\x00\x00\x00\x00IEND\xaeB`\x82"

def getPasteBitmap():
    return BitmapFromImage(getPasteImage())

def getPasteImage():
    stream = io.BytesIO(getPasteData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------
def getSaveData():
    return \
'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x01\x1dIDAT8\x8d\x9d\x93=N\xc3@\x10\x85\xbf\xf5\xa2-\xf1\x11\xa0\x8dC\
\x8f\x82\xa0\xe5\xa7\xa6\xe2\x04\xb4p\x00\x1a\xfb\x02\x11T\xf4\xa4\xa0\xc1\
\xc1\\\x01\x90R"\xc5\xa4\x89RD\x14\x04$\xa2@\x01\xb1\x04C\xe1\xc8\xb1`\x1dC^\
5;?\xef\xcd\x8cv\x94r4\xf1\xc5\xa7P\x82a\xff\xb7o\xfd@+\x94\xa3\xb9o"2\xa8K\
\x18\x86R\x84\xc1\x87\xc8\xdd\xf3X|\xdf\x17\x11\x91\x9bc$\x8a"q\xf2\x8cZk\
\xab\xfa\xd3\x18\x1e\xdf\x12\xba\xef\x06\x80\xdb\x13\x95\xc5\x1ckE\t\xd6\xb6\
\xf7\xec\x04I\x92\x94\xaa\xff\xc4\\\x1d\xf0\xd2\xfd\x1bA\x99:\xc0B\xfe\xb1\
\xbb\xf1@\x10\x043\xc5\x8f6\xaf\x00\xe8u\xc0]\x9e\x10\x0c\xfb@m\x92\xb0\xbf8\
\xcd\x1e\xb5\xacm\xdb;\x18\xb5\xc0]%8}\xcd\x85+\x99\xd5\x8e\xbf2\xfb\xfc\xb0\
g\x1f!U\xac\xe0y^\xe62\xc6p\xd6h\x14\x8e4s\x89\xc6\xa4\xcb[\xa9V\xffG\xa0\
\xb5\xce\x8a\x97j[\xb4\xe3\xb8\x90@)\'\xfd\xbe\xd7\xf5\xe2\x83\xeau\xec~w\'\
\x9a\x12\x00\\6\xc3\xd2\xab,\xec`^|\x03\xb6\xdf|Q.\xa7\x15\x89\x00\x00\x00\
\x00IEND\xaeB`\x82'

def getSaveBitmap():
    return BitmapFromImage(getSaveImage())

def getSaveImage():
    stream = io.BytesIO(getSaveData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------
def getSaveAllData():
    return \
'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x01UIDAT8\x8d\x9d\x93\xbfK\xc3@\x1c\xc5\xdf%\x01g\xeb \x1d\x8a\x8b\x83M\
\x11\xe9\x16\x8a\x8b\xff@\xa0\xdd\x14\'\x17\x17A2\xe9,\x08\xc9\x14\x82n.nn\
\x9a\xde?\xe0R;\xb88\x99v\xe8`\x86\n."\x81\xb6\xb4\xb4~\x1d\xd2\xc4^\x92j\
\xf5\x03\xc7\xfd~\xf7\xeeq\xc7<\x17\x84)\xa3\x1e\x04\x863\xfd\xf10\xac\xb7\
\x8fe&,\xf2\\\x10\xf9\x06q\xce)I\x7fL\xf4\xda\'2M\x93\x88\x88\x1e.@\x9csb\
\x92\x8c\xb8x.\xa8X6\xd0z\xb2c\xd1?9\x89\x1c\xfc\xd7\x89\x82\x04\xeb\x9f:Z\
\xf5l\';9\xe0\xf1\xea\x14\xca\x12\xb0\xe2\xebh8 ))\x00\x00\xc5\xb2\x81\x8e\
\xc4\xb1\xb5GB\xd9< \x14\xf6\t\xf7\xef&*Ga\xf6\x99\x02Y\x0c&\xc0\xc7\x08x\
\xe9\x01A\x10\xa0y\xc9\x16\x17\x98\xdd\x1cQ\xd1\x8d\x9f\x05<\xcf\x136\xcf#\
\x15b\xc4\xc9\xee\x1b,\xcb\x8a\xfbA\x10\xc4\xed\xf3\xc3\x01\x00\xc0o\x03J\
\xa9&\xb3\x86c\xd3r![\xe47\x14 |\x14\xcf\xb7\x13JNZ7\xab\xc2\xe9\xddn7\x9e\
\xbb>\xcb\x01\x98\xc9\xa0T\x93Y\x93\xdbH\xa2\xaa*4MC\xb5Z\xcdt \x84\x98\xfa(\
S\xf2\xf9\xfc\xdc+0&\xc9\xa9\xc1\x86\xf3}\x1d\xbf\r\xacm\x84\xf5\xc2\x02\x00\
Pw\xefR\x99d\xf1\x05z\x94\xd0b\xcb S\xf3\x00\x00\x00\x00IEND\xaeB`\x82'

def getSaveAllBitmap():
    return BitmapFromImage(getSaveAllImage())

def getSaveAllImage():
    stream = io.BytesIO(getSaveAllData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------
def getPrintData():
    return \
'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x01\xa7IDAT8\x8d\xa5S=K\xc3P\x14=\xef\xb5 \x0e\xf6\x17\xb8$X\x10\xa7\
\x82\xb4\n]\x05A\x07\xebd%\xfe\x02\x97\x82\xe0\xa0\x83\xa3\x88\xb5E\xfd\x07j\
\x0bq\xea\x07\x18(8:5\x16\xa2H\xf1\x8bN\x12\tt\xe9\x8b\xddZ\x9eC|i\x93\xd4\
\x0f\xf0\xc0\xe1\xe6\xbe\xdc{\xde\xb9\xc9{\x84\xd0\x10\xfe\x83\xb0x8m\xf6\
\xb8i\xf7=/\xfb\xad\x07O\x9e]\x9f%\x01\x05BC 4\x84\x1d\xbd\xc7\xfdx\xb2\x1d^\
\x99\x9c\x1f\xe6\x8ey\xb5Z\xe5\xa2^\x90\n\xa1\x83\xb91\xb2{;p\xf0\xfc\xe1\
\xc4W\xdb\x89\xe3\xcb\x19\xa8\xaa\x8aJ\xb9\xc4\x87\r\xd0\xe1\xc4o\xf9/\x08\
\x03\xc0\xc5\xf9\x19\x07\x80\xfb\xaf\x9d\xc5\xae-6(4\xed>\x9aoA\x01zq~\xc6\
\x15E\x81\xa2(\xee\xe2\xd4\x84\x13\xe5H\xb0\xc1?\x06\x05\x80b\xb1\xe8\x16\
\xbc\xda\x0e[\xcc\xa1i\xf71\xfcw\xf2\xf9\xbcG\x84\x14\n\x05\x1e\x8b\xc5\xa0\
\xd5\xae\xb1\xbd\x95\x81eY#gm\xb7\xdb\x9e|cs\x1fw7\x97$lZm\xc4\x00,-. \x9b?\
\xc1tT\x1e)\xc0\x18C$\x12\x01c\xce\x87\xe9\xbe\xeb\xa8\x94K\x9cNGeh\xb5k\x00\
\x80\xd1\xa8#\x91H@\x96\xe5\x00%I\xc2\xe3K\x0b\x9a\xa6A\x92$W8\xbc\x92Z%\xeb\
\xe95n4\xea\x01\xab\x9dN\xc7\xe3"9\x1fGr>\xeeYs\x8fr:\x9d\x06c\x0c\x86ax\nL\
\xcb;\xbb\x1f\x84\xd0\x10*\xe5\x12WU\x15\xcd7`f\xf2\xc7z\x00\x80\xae\xeb\xc8\
\xe5rXI\xad\x12"nc\xa5\\\xe2{G*\xba\xef\xfa\xaf\x02\xa2\xd9u \xe0?\xe7\xdfA4\
\x03\xc0\'\xe3\x82\xc9\x18g\x90\x8e]\x00\x00\x00\x00IEND\xaeB`\x82'

def getPrintBitmap():
    return BitmapFromImage(getPrintImage())

def getPrintImage():
    stream = io.BytesIO(getPrintData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------
def getPrintPreviewData():
    return \
'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x01mIDAT8\x8d\x8d\x92\xbdK\x02a\x1c\xc7?w\x1a\x85E\x04588XHa\xd1\x14!AB\
\r.\xbd\x07m-By.M\xfe\x03N\x05\x0e\xed\xf9\x124\x045\x04\x15\xdc\xda&4\xb5DC\
J\x8a\x81E\t.\x82\x918\xd8\xf0pOw\xde\x19}\xe1\xe1w\xf7;>\xdf\xdf\xcbs\xca\
\xddC\xb9C\x97\x1e\x8bU\xf9\x9c\xd8]V\xba\xbf\x9b\xa5\x02\xf8\xa6\xc6-ge=\
\x0c@p)\xcc\xc1\xe1\xa5\xad\x80\xcd\xa0\x97\x86\xfb`5\xba\xf3\xa7\x89\xdb)Y\
\xff\x16\xf1"{%s\xb77\xd7\x9d\xcd\xadm\xdb86\x03\x03\x0eE\xc2\x04\xdbPk\xc1y\
2Edf\xday\x84\xe6\xdb\x93\x84\x8c\xd8h\x8bSk\xf5j\xdcdPj\x8eX`C\x06\x9c?\x8a\
\xe3\xef/\xa3\xeb:\xb1\xfd=\xdb.,#4\xdav\x18-m\x01b\xd0\xc9\xe6N\xe5.Ts\xcbN\
pz\x0e\xa2~\x91\x0bx\x00-m\xe9D-W>%h\xc0\x1f_\xbf\x15\xef\xeb\x90\xaf\xc1\
\xe2\x18x="\x82\xb8\x15\xd9\x81yYf\x18\xe0\xac"\xc0\xc0\x10\x84\xc6D4\xcb\
\xf2#u\xc3\xb2m`t\x00&\x07E4\xcb]x.QH\xa6\xec$\x13\xf83q^\xb44^\x8f\xb8\xa5"\
p\x9c\x88\xa3\x91\xe1\x9d5\x00\x14Eu\xc9y\x9c\xa4\xeb\xba\xe5}\xb6\x9a\x01`\
\xc1\x07\xf39\x97\xa2(\xaa\xab\x17+\xd5]\xe0\xf5dC\x9a\xfc\xcb\xc0\xc9\xd00\
\xf9\x011\xc9\x87\xf3\xb4\xd1t\xaf\x00\x00\x00\x00IEND\xaeB`\x82'

def getPrintPreviewBitmap():
    return BitmapFromImage(getPrintPreviewImage())

def getPrintPreviewImage():
    stream = io.BytesIO(getPrintPreviewData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------
def getCutData():
    return \
'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x01HIDAT8\x8d\x85\x92OK\x02Q\x14\xc5\x7f\xa3\x05}\x1b\xa1\xc0\x9d\xb4\
\xaaf6\x93a\x10\xe3^\x83l\xdf\xc6\xa5\x1bIA\xb4\xa0\x9cM\xe5"\x84\x18\xff\
\x108\xbb\xf0\x93\xb4v\x15h\xa9\xaf\x16\xaf\x85\xbcat^\xd3\x81\xb79\xf7\xdc\
\xf3\xce{\xf7b$\x92\x84O\xa7\xd3\x91\x9b\\\xf8\xd4\xeb\xb5\xb5z\x02\r\x9e\
\x1e\x1f\xa4\x8eo5\x1b\x12`\xd0\xef\x05u\xadA.\x97\xc3u\xef\xd7LZ\xcd\x86\
\xb4\xedlD\xab5\xd0A\x08\xc1l6e>_\xc4\x1b\x88o\x01@\xde\xc9\x07\x91k\xd7Ui\
\x9a\x96\xd6xk\x93(\x14\xce\r@\x1e\x1e\x1cE\xc4\x9e\xe7\x91J\xa58\xce\x9e\
\x18\x7f\x1a\x00,\x17\xab\x98\xb6\x9dE\x08!M\xd3\x8aDW0\x8cDR[P\xb1U\xa3\xef\
\x8f"\xb7C\xcc\'\xee\xbdw\xf1</h\xceL\x86Z\x9d\xf6\to\x17\xbb2m90z\xc6\xf7!3\
\x19\x92\xb6\x1c\xc6\xdd\xab\x886v\x8ci\xcb\t\x9a\x15\xc2K\xa45P\xb7\x17o+\
\x00,\xa6\x9f\x00\x14o+\xec\x9f\x15X\xba\x97\xf1\tTC\x1c\xfe]e\x80v\xa9\xcc\
\xb8\xeb2\xfb\xf8\xe2\xf5\xaeA\xbbT\xd6\xea"c\x1c\xf4{r\xfbe\xf5Y?\xa7\xd5\
\x80W\xd1w\n7k\xa3\xd4\xee\x81\x8a\x18\x16\xea8\x80_\\\xa2\x8b\x88!\xd2S\x08\
\x00\x00\x00\x00IEND\xaeB`\x82'

def getCutBitmap():
    return BitmapFromImage(getCutImage())

def getCutImage():
    stream = io.BytesIO(getCutData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------
def getUndoData():
    return \
"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x01\xa7IDAT8\x8d\xa5\x90\xbfK[Q\x18\x86\x9fs#\x8d\x7fBu\xc8\xd6\xc9\xc1\
\xa1\x83\xd0\x16\xa1C@*\x98\xc4\xa2\x12\xda\x8e5\x9b\x83\x04\x07Aph\x17)\x16\
\xdd\xd4\xc1\xa1Z\x1b\xc5&9\xa6P\xbaw\xa8\x9b\x9b\xa0S\xb0\xe2\x8f\\%1^\x8d\
\xde\xfa9\x84s\xf1\xea\xa5\x06<p\x86\xc3\xf9\x9e\xe7\xbc\xefQ\xca\n\xf1\x90\
\xd5t\xdf@\xba\x10\x95r\xcd\x01`\xee\xf5o\xd5\xb0 ]\x88\n@\xd7\xb3^\x00.\xaf\
\xce\xd8\x9d>\x10\x80\x1fC[\x9eH\x05UH\x17\xa2r\x13\xac\x9d_Pq\x8f\x01(96\
\xdf\x16\xd7X\xff\xb8\xaf\x02\x05\x066\xa0+5\xe6\xb3\x0b\x1c\xeeW\x00x\xd1\
\xf3\x14\x80\xaf\x93\xbf\xd8\xcb\xb8\xeaN\x05\xd3\xd7\xbc\x9a\xd1\xdf\x19\
\x8cL@\xa4~\x9f\x9a\xec\xa3\xb3\xa7\r\x80|.+>\xc1\xfb\xd5\xe72\xf0\xf2-U\xa7\
\xec\x83c\xf1\x84\xd79\x9f\xcbJj\xa9/\xf8\x13\xcb\xe7U.\xaf\xcep\xa5\x06P\
\x8f\x1d\xf1'\x8c\xc5\x13*\x9f\xcb\x8a'\xe8_l\x17\x80\xe57\x1b\xea\xd4\xae\
\xc7w\xfe9\x94\x1c\xdb\x83\x1e\x0f4\t\xc0^\xc6UFb\xee\xacS\xdba\xf8\xd5\x08\
\xdd\xd3O\xc4t7\xab\xb8m\x93Z\xf2w\xbe\xfdgJk-\xb3\xc5\x11\xc6\xde\x8dS\x95\
\x8a\xd7\xbf\xe4\xd8\xec\x9c\xecr\xb2Sfm\xf9\x0f3\xc9\x15\xdf\xcb^\x82X<\xa1\
\x06#\x13\x0c}\x1a\x06 \xdc\xfc\xc87\xf0?\xb8\x1e\xc1\n\xa1\xac\x10Zk\xe9\
\x18k\x95\x9fGS\xf2\xa58*\x9f7S\xd2\x92\x0c\x8b\xd6Z\xccL\xd0\xf6\x1d\xb4\
\xd6\xd2\x92\x0c\xcb\xea\xdf\x0f\r\xc1w\x047%\x8d\xc0\x81\x02#i\x04VV\x88k\
\x82\xbe\xde\xc2\xb0\xb2\xea\xa7\x00\x00\x00\x00IEND\xaeB`\x82"

def getUndoBitmap():
    return BitmapFromImage(getUndoImage())

def getUndoImage():
    stream = io.BytesIO(getUndoData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------
def getRedoData():
    return \
"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x01\x88IDAT8\x8d\xa5\x92\xc1K\x02A\x14\xc6\xbfQ\t\xbc\x14tJ\xfb\x0f2\
\x08\xbaD\xdd:\xe5!\xd2\xad$/\x82FP\x06\x99\x87\x04\xa1\x83D\x10\x0b\x85\xd4\
\xa9\x8c (\x82<\xad\xce\xa9\xff\xc0[\xd2)\xbcu\t\xb2\xd0\xa5\xb5\x94\x14z\
\x1dd\x87]\x1bBh\xe0\xc1\xf0\xde\xfb~3\xef\x9ba\xcc\xe1\xc4\x7f\x96K\x96\xdc\
\xd6\xfcd\xeeO\x94;\xd67\xc0\x14Fg\xd7E\xae~\xa5S\xe3\xd3@!\xfe(\x051s\x84m\
\xcdOV!\x004\xbf\r\x00\x80\xde\xae\xe2B\xbb\x94B\\\x00\x10\xb9\x9a\x12\xe2,W\
Eqc~S\xec\xd7\x94\x18\xaa\xafY*e^l\x10\x87\xf5\xb4,W\xb1<\x98\x16q\x98W\xa1\
\xb7\xab\x00\x80F\xa7\x0e\x00(\x164\xb2\x02\xc0\x1cN(\xb9qRr\xe3\xc49'\xe6p\
\xc2\x1a3\xfb\xa3t\xfb\xbcK\xe7O[\xa4V\xc2\xe4K\x0e\xdb\xfa\\\x00\x10\xf3\
\x1c\x00\x00\x02AEj\x94\xd11P\xffz\x93\x95\xba\x80^\xe1\xf4\xde\x08\x01@)\
\xf3\xc2\xdek-!\xae5u\xe8\xcf-\x00\x80gi\x80l\x1e\xf4\xae\xc4j\x14c\x89!1o\
\xad\xa9\x8b\xda\xc6\xf5\n\x16v&\xbb\x16\xc8~b\xb1\xa0\x91\xfa\x10G4\xb2h;\
\xbd\xd1\xfe\x10=\xfc\xe8\x1eg\x91\xbc\xfc\x06\x81\xa0\xc2\xd2\x13\xa789\xbe\
\x91\xde\xce\x14\x07\x82\nC\xaf\xeb\xd6\xe0\x9c\x93/9Lj%L\xa9\xf2\x1c\xa5\
\xcas\xe4\r\xb9m\xaf\xf0'\xc0\x84xCnR+\xe1_\xe2\xbe\x00V\x88\xec\x9f\xf4\x05\
0!\xb2\xfc\x0f\xe0\xc4\xb6\xad\x97R\xe5z\x00\x00\x00\x00IEND\xaeB`\x82"

def getRedoBitmap():
    return BitmapFromImage(getRedoImage())

def getRedoImage():
    stream = io.BytesIO(getRedoData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------------

def getBlankData():
    return \
'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x00]IDAT8\x8d\xed\x931\x0e\xc00\x08\x03m\x92\xff\xff8q\x87\xb6C\x11\x89\
\xa8X:\xd4\x13\x03:\x1b\x01\xa45T\xd4\xefBsh\xd7Hk\xdc\x02\x00@\x8a\x19$\xa1\
9\x14A,\x95\xf3\x82G)\xd3\x00\xf24\xf7\x90\x1ev\x07\xee\x1e\xf4:\xc1J?\xe0\
\x0b\x80\xc7\x1d\xf8\x1dg\xc4\xea7\x96G8\x00\xa8\x91\x19(\x85#P\x7f\x00\x00\
\x00\x00IEND\xaeB`\x82'


def getBlankBitmap():
    return BitmapFromImage(getBlankImage())

def getBlankImage():
    stream = io.BytesIO(getBlankData())
    return ImageFromStream(stream)

def getBlankIcon():
    return wx.IconFromBitmap(getBlankBitmap())



#--------------------------------------------------------------------
def getBitmap(filename, imgType=wx.BITMAP_TYPE_PNG):
    """
    return the bitmap from a file.
    """
    imgdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
    if not os.path.exists(imgdir):  # for py2exe
        pdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        imgdir = os.path.join(pdir, 'images')

    fullname = os.path.join(imgdir, filename)

    return wx.BitmapFromImage( wx.Image(fullname, imgType).Scale(16, 16) )


def getStartJobBitmap():
    """ Return an image used in the tool bar to start the fitting."""
    return getBitmap('Run.jpg', wx.BITMAP_TYPE_JPEG)


def getStopJobBitmap():
    """ Return an image used in the tool bar to stop the fitting."""
    return  getBitmap('Stop.gif', wx.BITMAP_TYPE_GIF)


def getPreviousJobBitmap():
    """ Return an image used in the tool bar to go to previous job."""
    return getBitmap('Previous.png')


def getNextJobBitmap():
    """ Return an image used in the tool bar to go to next job."""
    return getBitmap('Next.png')


def getDeleteBitmap():
    """ Return an image used in the tool bar to delete current job."""
    return getBitmap('Delete.bmp', wx.BITMAP_TYPE_BMP)


def getCloseBitmap():
    """ Return an image used in the tool bar to close current job."""
    return getBitmap('Close.png')
