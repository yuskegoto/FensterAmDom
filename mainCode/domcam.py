from machine import Pin
import gc
import socket
# import urequests
import network
import time
import ntptime

from array import array
from neopixel12 import NeoPixel

# Custom jpeg decoder lib
import image
# import math

# IMT implemented Neopixel driver
# import nevercast_pixels as nv_Neopixel

########################### File IO setting ############################
OUT_FILE = 'out'
FILE_OUT = False

LOG_FILE = 'debug.log'
LOG_OUT = True

########################### Clip setting ############################
CLIP_WIDTH = 32
CLIP_HEIGHT = 32        # seems like minimum height must be 16

# mountain cologne
URL = "http://www.wdr.de/themen/global/webcams/domcam/domcam_960_live.jpg"
OFFSET_X = 720      # Must be multiple of 8
OFFSET_Y = 275 # Mountain

# Sky cologne
# OFFSET_X = 80      # Must be multiple of 8
# OFFSET_Y = 100 # Sky

# Sidney loyal yacht squadron
# URL = "https://www247.mangocam.com/c/rmys/img.php?w=640&h=360&auth=cm9vdDpheGlz&t=1599522073610"
# OFFSET_X = 80      # Must be multiple of 8
# OFFSET_Y = 24 # Sky

OFFSET_Y_REMINDER = OFFSET_Y % 8
OFFSET_Y = OFFSET_Y - OFFSET_Y_REMINDER

##################### URLs #############################################
# URL = "http://yuskegoto.net/koala.jpg"
# URL = "http://yuskegoto.net/Rlogo-old.jpg"
# http://yuskegoto.net/koala.jpg
# URL = "http://cam.wni.co.jp/taikobashi/mobile.jpg"
# http://cam.wni.co.jp/taikobashi/camera.jpg
# https://www.wdr.de/themen/global/webcams/domcam/domcam_960_live.jpg
# https://assets.koeln.de/stadtinfo/verkehr/webcams/live/a01-01-03.jpg
# # does not work with subdomain yet...
# https://yuskegoto.github.io/jpeggetter/Rlogo-old.jpg


##################### Sleep and Wait Timing Setting ####################
SLEEP_LENGTH_sec = 60
SLEEP_UPDATE_INTERVAL_ms = 2000
NEOPIXEL_WAIT_AFTERSENT_ms = 1000
debug_timeCounter_last_ms = time.ticks_ms()
update_timeStamp = time.ticks_ms()

##################### Neopixel Setting ###############################
NUM_LED = 768
LED_WIDTH = 32
LED_HEIGHT = 24

BRIGHTNESS = 0.2
# BRIGHTNESS = 0.15

COLOR_BALANCE_R = 230
COLOR_BALANCE_G = 255
COLOR_BALANCE_B = 210

# neo = machine.Neopixel(machine.Pin(21), NUM_LED)
neo = NeoPixel(Pin(13), NUM_LED)
# neo_l = NeoPixel(Pin(4), NUM_LED - NUM_LED_UPPER)

pixel_diff = bytearray()

##################### LED indicator Setting ###############################
led_indicator = Pin(4, Pin.OUT)
led_state = False

############################ LED indicator #####################################
def blink_LED(state = None):
    global led_state
    if state != None:
        led_state = not state
    if led_state:
        led_indicator.off()
        led_state = False
    else:
        led_indicator.on()
        led_state = True

################### Debug time counterS function ###############################
def debug_delta(title=None):
    global debug_timeCounter_last_ms
    if title is not None:
        print(title,time.ticks_diff(time.ticks_ms(), debug_timeCounter_last_ms),'ms')
    debug_timeCounter_last_ms = time.ticks_ms()

def debug_log(msg):
    if LOG_OUT:
        currentTime = time.localtime()
        logdata = "{0}.{1}.{2} {3}:{4}:{5} {6}\n".format(currentTime[0], currentTime[1], currentTime[2], currentTime[3], currentTime[4], currentTime[5], msg)
        print(logdata)
        with open(LOG_FILE, 'a') as f:
            f.write(logdata)
    return


########################### Sleep function #####################################
def sleep_count(sleep_len_sec, updated):
    # currentTime = time.ticks_ms()
    sleep_len_ms = sleep_len_sec * 1000
    global update_timeStamp
    update_duration_ms = sleep_len_ms - time.ticks_diff(time.ticks_ms(), update_timeStamp)
    print("sleep another {0} sec".format(update_duration_ms / 1000), end='')
    
    pixel_diff_inclement = [[0.0, 0.0, 0.0]] * NUM_LED #container for storing pixel value inclement
    
    update_freq = update_duration_ms // SLEEP_UPDATE_INTERVAL_ms
    # while time.ticks_diff(time.ticks_ms(), update_timeStamp) < sleep_len_ms:
    for u in range(update_freq):
        sleep_timeStamp = time.ticks_ms()
        blink_LED()
        if updated:
            updateNeopixel(update_freq, pixel_diff_inclement)
        wait_ms(SLEEP_UPDATE_INTERVAL_ms - time.ticks_diff(time.ticks_ms(), sleep_timeStamp))
        # gc.collect()  # garbage collector
        # gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())
        # print(gc.mem_free())
        print('.', end='')
    print('')
    update_timeStamp = time.ticks_ms()
    blink_LED(False)
    return

def wait_ms(sleep_len):
    currentTime = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), currentTime) < sleep_len:
        time.sleep_ms(500)
        pass
    return

########################### Neopixel update function #####################################
def updateNeopixel(update_rate, pixel_diff_inclement):
# def updateNeopixel(update_count, update_rate):
    global pixel_diff
    # update_fraction = 1 / (update_rate - update_count)
    # print("{} ".format(update_fraction))
    # if update_count < update_rate - 1:
    for i in range(0, NUM_LED):
        r, g, b = neo[i]
        r_diff, g_diff, b_diff = pixel_diff[i]
        r_diff_inclement, g_diff_inclement, b_diff_inclement = pixel_diff_inclement[i]

        update_diff = r_diff / update_rate
        r_diff_inclement += update_diff

        if abs(r_diff_inclement) > 1:
            r += int(r_diff_inclement)
            r_diff_inclement -= int(r_diff_inclement)
        # update_diff = int(r_diff * update_fraction) 
        # if abs(update_diff) >= 1:
        #     r += update_diff
        #     r_diff -= update_diff

        update_diff = g_diff / update_rate 
        g_diff_inclement += update_diff
        if abs(g_diff_inclement) >= 1:
            g += int(g_diff_inclement)
            g_diff_inclement -= int(g_diff_inclement)
        # update_diff = int(g_diff * update_fraction) 
        # if abs(update_diff) >= 1:
        #     g += update_diff
        #     g_diff -= update_diff

        update_diff = b_diff / update_rate 
        b_diff_inclement += update_diff
        if abs(b_diff_inclement) >= 1:
            b += int(b_diff_inclement)
            b_diff_inclement -= int(b_diff_inclement)
        # update_diff = int(b_diff * update_fraction) 
        # if abs(update_diff) >= 1:
        #     b += update_diff
        #     b_diff -= update_diff

        neo[i] = [r, g, b]
        pixel_diff_inclement[i] = [r_diff_inclement, g_diff_inclement, b_diff_inclement]
        # pixel_diff[i] = [r_diff, g_diff, b_diff]
    neo.write()

# SD mount related things
# if ENABLE_SD:
#     try:
#         uos.mountsd()
#         dir = ''
#         if len(FILE_PATH.split('/')) > 2:
#             if len(FILE_PATH.split('/'))[1] == 'sd':
#                 dir = '/sd'
#                 file_name = FILE_PATH.split('/')[-1]
#                 content = uos.listdir(dir)
#                 for i in content:
#                     lcd.println(i)
#                     if i == file_name:
#                         uos.remove(FILE_PATH)
#                         lcd.println('removed: ' + i)
#         wait(1)


######################### WIFI connection sequence #######################
#  copied from here, TQ!
# https://garaemon.hatenadiary.jp/entry/2018/04/20/180000

def connect_wifi(target_ssid, target_passwd, timeout_sec=20):
    wlan = network.WLAN(network.STA_IF)  # create station interface
    wlan.active(True)                    # activate the interface
    if wlan.isconnected():
        return True

    for net in wlan.scan():
        ssid = net[0].decode()
        if ssid == target_ssid:
            print('Connecting to {}'.format(ssid))
            wlan.connect(ssid, target_passwd)
            start_date = time.time()
            while not wlan.isconnected():
                now = time.time()
                print('.', end = '')
                if now - start_date > timeout_sec:
                    break
                time.sleep(1)
            if wlan.isconnected():
                print('Succeed')
                return True
            else:
                print('Failed')
                return False
    return False

def check_connection():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)                    # activate the interface
    if wlan.isconnected():
        return True
    return False

########################### Time update using NTP #####################################
def set_networktime():
    if check_connection():
        try:
            ntptime.settime()
            return True
        except Exception as e:
            debug_log("ntp error:{}".format(e))
    return False

def connect_network():
    try:
        f = 0
        # if ENABLE_SD:
        #     # recursively lead wifi ssid and password from wifi.ini file on sd
        #     f = open('/sd/wifi.ini')
        # else:
        # f = open('wifi.ini')
        if(not check_connection()):
            with open('wifi.ini') as f:
                wifi_info = f.readline()
                while wifi_info != '':
                    ssid = wifi_info.split(',')[0]
                    pw = wifi_info.split(',')[1][:-2]
                    if connect_wifi(ssid, pw):
                        f.close()
                        print("connected")
                        return True
                        # break
                    else:
                        print("connection failed: {0}".format(ssid))
                    # wait(1)
                    time.sleep_ms(1)
                    wifi_info = f.readline()
        else:
            print("already online")
            return True
    except Exception as e:
        print("No wifi.ini file")
        debug_log("connection unsuccessful")
        return False
    return False

########################## Data getter ######################################
# Helper fuction
def split_list(l, s):
    count = 0
    ni = []
    for i in range(0, len(l)-len(s)):
        if l[i] == s[count]:
            count = count+1
            if count == len(s):
                # lcd.println("Matched")
                ni.append(i+1)
                count = 0
        else:
            count = 0
    if len(ni) == 0:
        return l
    else:
        r = []
        pi = 0
        for j in range(0, len(ni)):
            r.append(l[pi:(ni[j]-len(s))])
            pi = ni[j]
        r.append(l[pi:len(l)])
        return r

####################################################################
#
#   @bref: data fetching fucntion using sockets
#
#
####################################################################
def updatePic_sockets():
    debug_timeCounter_last_ms = time.ticks_ms()

    rcv_data = bytearray()

    proto, dummy, host, path = URL.split('/', 3)
    # print('proto: ' + str(proto))
    # print('dummy: ' + str(dummy))
    # print('host: ' + str(host))
    # print('path: ' + str(path))

    port = 80
    if proto == 'https:':
        port = 443

    if ":" in host:
        host, port = host.split(":", 1)
        port = int(port)

    addr = socket.getaddrinfo(host, port)[0][-1]
    # addr = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
    # addr = addr[0]
    # print(str(addr))

    s = socket.socket()
    s.settimeout(5.0)
    # s = socket.socket(addr[0], addr[1], addr[2])
    method = "GET"

    # s.connect(addr)
    # s.send(bytes('GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n' % (path, host), 'utf8'))
    try:
        # s.connect(addr[-1])
        s.connect(addr)
        if proto == "https:":
            import ussl
            s = ussl.wrap_socket(s, server_hostname=host)
        s.write(b"%s /%s HTTP/1.0\r\nHost: %s\r\n\r\n" %
                (method, path, host))
        header_counter = 0
        header_received = False
        while True:
            # buffer size should not exceed header + content size!
            data = s.read(200)
            # data = s.recv(200)
            if data:
                # data will be splitted with \r\n\r\n\ = CR LF CR LF
                l = split_list(data, [13, 10, 13, 10])

                if len(l) == 2:
                    # print("header= : {} ".format(len(l[0])))
                    # print("JPG= : {}\n".format(len(l[1])))
                    # outfile.write(l[1])'
                    rcv_data += l[1]
                    header_received = True
                    break
            if header_counter > 2:
                rcv_data = bytearray()  #clear the data
                break
            header_counter += 1
        # once you received header and parsed out, receive 100 bytes data per each step until it stops.
        while header_received:
            blink_LED()
            data = s.read(1024)
            # data = s.recv(1024)

            if data:
                print(".", end = '')
                rcv_data += data
                
            # When no data is available, suppose all data were received. finish the loop...
            else:
                print("Data received\n")
                break
    except Exception as e:
        # if isinstance(e, OSError):
            # s.close()
        print("Error: {0}\n".format(e))
        rcv_data = bytearray()      # Clean up data when the data transfer is incomplete
        print("GC freemem: {0}\n".format(gc.mem_free()))
        debug_log("data not received")
            # raise

    s.close()
    gc.collect()  # garbage collector
    gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())

    debug_delta('fetch data')
    return rcv_data

# def updatePic_requests():
#     gc.collect()
#     debug_timeCounter_last_ms = time.ticks_ms()

#     print("updating...")
#     print(URL)

#     # This line is incredibly simple thanks to the large PS-RAM, normal ESP32 won't handle this well, especially for large jpeg files
#     webcam_data = None
#     try:
#         webcam_data = urequests.get(URL).content
#     except Exception as e:
#         print("Error: {0}".format(e))
#     debug_delta('fetch data')
#     return webcam_data

def writeData(data, file_name, data_width, data_height):
    if type(file_name == str) and type(data == bytearray):
        with open(file_name + ".ppm", "wb") as f:
            header = bytearray("P{}\n{} {}\n255\n".format(
                6, data_width, data_height))
            f.write(header)
            f.write(data)

def getPixelNum(n):
    led_num = 0
    x = 0
    y = n // LED_WIDTH
    # need to calculate this due to led matrix's wiring
    if y % 2 == 0:
        x = n % LED_WIDTH
        led_num = n
    else:
        x = (LED_WIDTH - n % LED_WIDTH) - 1
        led_num = x + y * LED_WIDTH
    # led_num += 1
    # print(led_num, end = " ")
    return led_num

########################## Read data from ppm #################################
# def readData(file_name, data_width, data_height):
#     header_length = len("P\n \n255\n;") + 2 + (int)(math.log10(data_width)) + (int)(math.log10(data_height))

#     i = 0
#     with open(file_name + ".ppm", "rb") as f:
#         f.seek(header_length)
#         for i in range(0, NUM_LED):
#             color_data = f.read(3)
#             # print(color_data, end = " ")
#             r = (int)(color_data[0] * BRIGHTNESS)
#             g = (int)(color_data[1] * BRIGHTNESS)
#             b = (int)(color_data[2] * BRIGHTNESS)
#             # rgb = (r << 16) | (g << 8) | b
#             # print(i, end=" ")
#             # print("{} {} {}, ".format(hex(r), hex(g), hex(b)), end=" ")

#             neo[getPixelNum(i)] = (r, g, b)
#         neo.write()
#         wait_ms(NEOPIXEL_SIGNAL_DELAY_ms)

# def readPixels():
#     # lcd.setCursor(0, 160)
#     # Get data from downloaded file
#     print("reading: {0}".format(FILE_PATH))
#     # lcd.println("reading: %s"%(FILE_PATH))
#     # img_clip_setting = image.get_jpeg_size(FILE_PATH)
#     # gc.collect()  # garbage collector

#     # img_clip_setting.update({'offset_x': 0})
#     # img_clip_setting.update({'offset_y': 0})
#     # img_clip_setting.update(width=read_width)
#     # img_clip_setting.update(height=read_height)
#     # print(img_clip_setting)
#     # img_clip_size = img_clip_setting['width'] * img_clip_setting['height']
#     # img_clip_data = array('H', img_clip_size, 0)

#     # pixel_data = image.decode_jpeg(
#     #     FILE_PATH, CLIP_WIDTH, CLIP_HEIGHT, OFFSET_X, OFFSET_Y)
#     input_data = open(FILE_PATH, 'rb').read()
#     pixel_data = image.decode_jpeg_buf(
#         input_data, CLIP_WIDTH, CLIP_HEIGHT, OFFSET_X, OFFSET_Y)

#     input_data = 0
#     gc.collect()  # garbage collector

#     # Debug preview file
#     writeData(pixel_data, OUT_FILE, CLIP_WIDTH, CLIP_HEIGHT)


#     # draw clipping area
#     # actual_scale = 2**SCALE
#     # lcd.rect((int)(OFFSET_X / actual_scale), (int)(OFFSET_Y / actual_scale),
#     #          (int)(CLIP_WIDTH / actual_scale), (int)(CLIP_HEIGHT / actual_scale), YELLOW)

#     # # print(pixel_data)

#     # for i in range(1, NUM_LED + 1):
#     #     led_num = 0
#     #     x = 0
#     #     y = i // CLIP_WIDTH
#     #     # need to calculate this due to led matrix's wiring
#     #     if y % 2 == 0:
#     #         x = i % CLIP_WIDTH
#     #         led_num = i
#     #     else:
#     #         x = (CLIP_WIDTH - i % CLIP_WIDTH) - 1
#     #         led_num = x + y * CLIP_WIDTH
#     #     # led_num *= 3
#     #     led_num = i * 3
#     #     ptColor_r = (int)(pixel_data[led_num] * BRIGHTNESS)
#     #     ptColor_g = (int)(pixel_data[led_num + 1] * BRIGHTNESS)
#     #     ptColor_b = (int)(pixel_data[led_num + 2] * BRIGHTNESS)
#     #     pixelRGB = 0
#     #     pixelRGB = (ptColor_r << 16) | (ptColor_g << 8) | ptColor_b
#     #     # print("X: {0} Y: {1} LED: {2} RGB: {3}".format(
#     #     #     x, y, led_num, pixelRGB))
#     #     neo.set(i, pixelRGB)
#     #     wait(0.01)
#     # print(pixel_data)
#     gc.collect()  # garbage collector
#     return

########################### Jpeg Decode function ######################################
#       IN:     jpeg data from buf
#       OUT:    True if decode was successful
#
#######################################################################################
def readPixels_buf(buf):
    if len(buf) > 0:
        global pixel_diff
        pixelBlackoutCheck = False
        try:
            debug_timeCounter_last_ms = time.ticks_ms()
            # Get data from downloaded file
            # print("Len: {0}".format(len(buf)))
            # buf = open(FILE_PATH, 'rb').read()
            # pixel_data = image.decode_jpeg_buf(
            #     buf, CLIP_WIDTH, CLIP_HEIGHT, OFFSET_X, OFFSET_Y)

            pixel_data = bytearray(CLIP_WIDTH * CLIP_HEIGHT * 3)    # Container for decoded data
            image.decode_jpeg(buf, pixel_data, CLIP_WIDTH, CLIP_HEIGHT, OFFSET_X, OFFSET_Y)
            buf = 0       # clear buf content as soon as decode completes
            gc.collect()  # garbage collector
            gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())

            # need to store in the immutable...
            led_data = bytes(pixel_data)
            pixel_diff = [None] * NUM_LED

            # Debug preview file
            if FILE_OUT:
                writeData(pixel_data, OUT_FILE, CLIP_WIDTH, CLIP_HEIGHT)
            # readData(OUT_FILE, CLIP_WIDTH, CLIP_HEIGHT)

            # print("pixel data length: {}".format(len(pixel_data)))
            # counter = 0
            # for p in pixel_data:
            #     p_int = int(p)
            #     print(hex(p_int), end='')
            #     if counter%3 == 2:
            #         print(" ", end='')
            #     if counter%(96) == 95:
            #         print("\n", end='')
            #     counter += 1
            offsetNumLED = LED_WIDTH * OFFSET_Y_REMINDER
            for i in range(0, NUM_LED):
                r = led_data[(i + offsetNumLED) * 3]
                g = led_data[((i + offsetNumLED) * 3) + 1]
                b = led_data[((i + offsetNumLED) * 3) + 2]
                
                # checking whether the decoded data contains any values
                if not pixelBlackoutCheck:
                    if r > 0 or g > 0 or b > 0:
                        pixelBlackoutCheck = True

                # print(hex(r) + hex(g) + hex(b), end = ' ')
                # if i%32 == 31:
                #     print("")
                r = int(r * BRIGHTNESS)
                g = int(g * BRIGHTNESS)
                b = int(b * BRIGHTNESS)

                r_c, g_c, b_c = colorCorrection(r, g, b)
                pixelNum = getPixelNum(i)
                # pixel_diff[pixelNum] = [r_c, g_c, b_c]
                currentPixelVal = neo[pixelNum]
                pixel_diff[pixelNum] = [r_c - currentPixelVal[0], g_c - currentPixelVal[1], b_c - currentPixelVal[2]]
                # neo[getPixelNum(i)] = [r_c, g_c, b_c]
                # else:
                #     neo_l[getPixelNum(i) - NUM_LED_UPPER] = (r_c, g_c, b_c)
            debug_delta('update')
            # neo.write()
            # wait_ms(NEOPIXEL_WAIT_AFTERSENT_ms)
            # debug_delta('write')


            gc.collect()  # garbage collector
            gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())
            print(gc.mem_free())

            return pixelBlackoutCheck
        except Exception as e:
            debug_log("Error on decode: {0}".format(e))
    else:
        debug_log("incomplete data: {0}".format(len(buf)))
    return False

def colorCorrection(colorR, colorG, colorB):
    colorR = int(colorR * (COLOR_BALANCE_R/255))
    colorG = int(colorG * (COLOR_BALANCE_G/255))
    colorB = int(colorB * (COLOR_BALANCE_B/255))
    return colorR, colorG, colorB

# def timerCallBack(timer):
#     lcd.clear()
#     update_cb = True
#     return

########################## Init #################################
gc.enable()

if connect_network():
    if set_networktime():
        blink_LED(True)
debug_log("Boot")

########################## Loop #################################
while True:
    updateState = False
    if check_connection():
        updateState = readPixels_buf(updatePic_sockets())
        if not updateState:
            debug_log("failed decode process")
        gc.collect()  # garbage collector
        gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())    
    else:
        connect_network()
        if check_connection():
            debug_log("Reconnect")
        else:
            debug_log("unable to connect wifi")

    sleep_count(SLEEP_LENGTH_sec, updateState)
    gc.collect()  # garbage collector
    # gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())