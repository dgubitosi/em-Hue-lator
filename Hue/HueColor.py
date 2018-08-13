"""
    HueColor
"""

import math

def xy_to_rgb(xy, bri):
    # https://developers.meethue.com/documentation/color-conversions-rgb-xy
    #
    # ignores color gamut
    # https://developers.meethue.com/documentation/supported-lights
    #Gamut_A = ((0.704, 0.296), (0.2151, 0.7106), (0.138, 0.08))
    #Gamut_B = ((0.675, 0.322), (0.409, 0.518), (0.167, 0.04))
    #Gamut_C = ((0.692, 0.308), (0.17 0.7), (0.153, 0.048))
    #Gamut_Default = ((1.0, 0.0), (0.0, 1.0), (0.0, 0.0))
    #Gamut = [ Gamut_A, Gamut_B, Gamut_C, Gamut_Default ]

    x = xy[0] * 1.0
    y = xy[1] * 1.0
    z = 1.0 - x - y

    Y = bri / 254.0
    X = (Y / y) * x
    Z = (Y / y) * z

    # wide RGB D65 conversion
    r = X * 1.656492 - Y * 0.354851 - Z * 0.255038
    g = -X * 0.707196 + Y * 1.655397 + Z * 0.036152
    b = X * 0.051713 - Y * 0.121364 + Z * 1.011530

    # reverse gamma correction
    i = 1.0 / 2.4
    if r <= 0.0031308:
        r *= 12.92
    else:
        r = 1.055 * math.pow(r, i) - 0.055
    if g <= 0.0031308:
        g *= 12.92
    else:
        g = 1.055 * math.pow(g, i) - 0.055
    if b <= 0.0031308:
        b *= 12.92
    else:
        b = 1.055 * math.pow(b, i) - 0.055

    # clamp any negative values to zero
    if r < 0: r = 0
    if g < 0: g = 0
    if b < 0: b = 0

    # https://stackoverflow.com/questions/16052933/convert-philips-hue-xy-values-to-hex
    # scale all values if the max is greater than 1
    i = max(r, g, b)
    if i > 1:
        r /= i
        g /= i
        b /= i

    # scale from 0.0:1.0 to 0:255
    r = int(r * 255)
    g = int(g * 255)
    b = int(b * 255)

    return [r, g, b]


def hsb_to_rgb(hue, sat, bri):
    # https://stackoverflow.com/questions/24852345/hsv-to-rgb-color-conversion

    # scale values to 0.0:0.1
    h = hue / 65535.0
    s = sat / 254.0
    v = bri / 254.0

    if s == 0.0:
        v = int(255*v)
        return [v, v, v]

    i = int(h*6.0)
    f = (h*6.0)-i
    p = int(255*(v*(1.0-s)))
    q = int(255*(v*(1.0-s*f)))
    t = int(255*(v*(1.0-s*(1.0-f))))
    v = int(255*v)
    RGB = {
        0: [v, t, p],
        1: [q, v, p],
        2: [p, v, t],
        3: [p, q, v],
        4: [t, p, v],
        5: [v, p, q]
    }
    return RGB[i % 6]


def ct_to_rgb(ct, bri):
    # https://gist.github.com/petrklus/b1f427accdf7438606a6

    # convert mired color temp to kelvin
    t = 1000000 / ct
    tmp_t = t / 100.0
    r, g, b = 0.0, 0.0, 0.0

    # red
    if tmp_t <= 66:
        r = 255
    else:
        r = 329.698727446 * math.pow(tmp_t - 60, -0.1332047592)

    # green
    if tmp_t <= 66:
        g = 99.4708025861 * math.log(tmp_t) - 161.1195681661
    else:
        g = 288.1221695283 * math.pow(tmp_t - 60, -0.0755148492)

    # blue
    if tmp_t >= 66:
        b = 255
    elif tmp_t <= 19:
        b = 0
    else:
        b = 138.5177312231 * math.log(tmp_t - 10) - 305.0447927307

    # brightness component
    bri = bri / 254.0
    r = int(r * bri)
    g = int(g * bri)
    b = int(b * bri)

    # clamp colors
    r = max(0, min(r, 255))
    g = max(0, min(g, 255))
    b = max(0, min(b, 255))

    return [r, g, b]

