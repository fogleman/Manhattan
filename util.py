from math import radians, asinh, tan, sin, cos

def mercator(lat, lng, scale=1):
    x = radians(lng) * scale
    y = asinh(tan(radians(lat))) * -scale
    return (x, y)

def laea(lat, lng, clat, clng, scale=1):
    lng, lat = radians(lng), radians(lat)
    clng, clat = radians(clng), radians(clat)
    k = (2 / (1 + sin(clat) * sin(lat) + cos(clat) * cos(lat) * cos(lng - clng))) ** 0.5
    x = k * cos(lat) * sin(lng - clng)
    y = k * (cos(clat) * sin(lat) - sin(clat) * cos(lat) * cos(lng - clng))
    return (x * scale, y * -scale)

def hex_color(x):
    x = x.replace('#', '')
    if len(x) == 3:
        x = x[0] * 2 + x[1] * 2 + x[2] * 2
    x = int(x, 16)
    r = ((x >> 16) & 255) / 255.0
    g = ((x >> 8) & 255) / 255.0
    b = ((x >> 0) & 255) / 255.0
    return (r, g, b)
