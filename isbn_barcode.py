"""EAN-13 barcode of a book's ISBN, drawn straight onto a canvas.

The barcode is the one the trade needs on the final page: EAN-13, from the
13-digit ISBN (a 10-digit ISBN is converted), with the digits printed under the
bars. An ISBN whose check digit does not verify returns no barcode, so a typo
never prints a barcode that scanners reject.
"""

import re

_L = {
    "0": "0001101", "1": "0011001", "2": "0010011", "3": "0111101",
    "4": "0100011", "5": "0110001", "6": "0101111", "7": "0111011",
    "8": "0110111", "9": "0001011",
}
_G = {
    "0": "0100111", "1": "0110011", "2": "0011011", "3": "0100001",
    "4": "0011101", "5": "0111001", "6": "0000101", "7": "0010001",
    "8": "0001001", "9": "0010111",
}
_R = {
    "0": "1110010", "1": "1100110", "2": "1101100", "3": "1000010",
    "4": "1011100", "5": "1001110", "6": "1010000", "7": "1000100",
    "8": "1001000", "9": "1110100",
}
_PARITY = {
    "0": "LLLLLL", "1": "LLGLGG", "2": "LLGGLG", "3": "LLGGGL", "4": "LGLLGG",
    "5": "LGGLLG", "6": "LGGGLL", "7": "LGLGLG", "8": "LGLGGL", "9": "LGGLGL",
}

BAR_FONT = "Helvetica"
BAR_FONT_SIZE = 6.4


def _check(body):
    total = sum(int(d) * (1 if index % 2 == 0 else 3) for index, d in enumerate(body))
    return (10 - total % 10) % 10


def isbn13(value):
    """The 13-digit ISBN, or '' when the number does not verify."""
    digits = re.sub(r"[^0-9Xx]", "", str(value or "")).upper()
    if len(digits) == 10:
        body = "978" + digits[:9]
        digits = body + str(_check(body))
    if len(digits) != 13 or not digits.isdigit():
        return ""
    return digits if int(digits[-1]) == _check(digits[:12]) else ""


def display(value):
    """The ISBN grouped the way it is printed: 978 1 234567 89 0."""
    digits = isbn13(value)
    if not digits:
        return str(value or "").strip()
    return " ".join([digits[0:3], digits[3:4], digits[4:9], digits[9:12], digits[12:13]])


def _bits(digits):
    left = _PARITY[digits[0]]
    bits = "101"
    for index in range(1, 7):
        digit = digits[index]
        bits += _L[digit] if left[index - 1] == "L" else _G[digit]
    bits += "01010"
    for index in range(7, 13):
        bits += _R[digits[index]]
    bits += "101"
    return bits


def draw_barcode(canvas, value, centre_x, base_y, width, height):
    """Draw the barcode with its bars' baseline at base_y. Returns the height used."""
    digits = isbn13(value)
    if not digits:
        return 0.0
    bits = _bits(digits)
    module = float(width) / len(bits)
    left = centre_x - float(width) / 2.0
    canvas.setFillColorRGB(0, 0, 0)
    canvas.setStrokeColorRGB(0, 0, 0)
    canvas.setLineWidth(0)
    index = 0
    while index < len(bits):
        if bits[index] == "1":
            run = 1
            while index + run < len(bits) and bits[index + run] == "1":
                run += 1
            guard = index < 3 or 45 <= index < 50 or index >= len(bits) - 3
            extra = module * 4 if guard else 0.0
            canvas.rect(left + index * module, base_y - extra, run * module + 0.15,
                        float(height) + extra, stroke=0, fill=1)
            index += run
        else:
            index += 1
    text_y = base_y - module * 4 - BAR_FONT_SIZE - 0.5
    canvas.setFont(BAR_FONT, BAR_FONT_SIZE)
    canvas.setFillColorRGB(0, 0, 0)
    canvas.drawRightString(left - module * 2, text_y, digits[0])
    canvas.drawCentredString(left + module * 24, text_y, digits[1:7])
    canvas.drawCentredString(left + module * 71, text_y, digits[7:13])
    return float(height) + BAR_FONT_SIZE + 6
