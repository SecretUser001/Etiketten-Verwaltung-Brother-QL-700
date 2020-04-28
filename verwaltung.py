#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import csv
import datetime
import os
import random

import cairo
import qrcode
import terminaltables

csvDict = []


def dateToday():
    dat = datetime.datetime.today()
    return str(dat.day) + "." + str(dat.month) + "." + str(dat.year)


def getSH():
    return (formToDict("Lebensmittel", "Haltbarkeit", openCSVDict("haltbarkeiten.csv")))


def getEAN():
    return (formToDict("ean", "Lebensmittel", openCSVDict("ean-codes.csv")))


def openCSVDict(fname):
    with open(fname) as csvfile:
        reader = csv.DictReader(csvfile)
        return [row for row in reader]


def formToDict(keyn, wert, liste):
    return {r[keyn]: r[wert] for r in liste}


def safeDict(dictionary, fname):
    with open(fname, "w+") as csvfile:
        csvfile.write("Lebensmittel,Haltbarkeit\n")
        for key in dictionary.keys():
            csvfile.write("%s,%s\n" % (key, dictionary[key]))


def genQrCode(text, safef):
    img = qrcode.make(text)
    img.save(safef)


def haltbarkeitbis(lm, dic):
    halb = datetime.datetime.now() + datetime.timedelta(int(dic[lm]))
    return (str(halb.day) + "." + str(halb.month) + "." + str(halb.year))


def genLabel(lm, dic, safef, bcode):
    WIDTH, HEIGHT = 413, 125
    if bcode:
        WIDTH, HEIGHT = 413, 150

    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, WIDTH, HEIGHT)
    ctx = cairo.Context(surface)

    dat = dateToday() + " - " + haltbarkeitbis(lm, dic)

    ctx.move_to(0, 0)
    ctx.set_source_rgb(1, 1, 1)
    ctx.rectangle(0, 0, WIDTH, HEIGHT)
    ctx.fill()

    ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(40)
    ctx.set_source_rgb(0, 0, 0)

    (x, y, width, height, dx, dy) = ctx.text_extents(dat)
    ctx.move_to(WIDTH / 2 - width / 2, 50)
    ctx.show_text(dat)

    ctx.set_font_size(45)
    (x, y, width, height, dx, dy) = ctx.text_extents(lm)
    ctx.move_to(WIDTH / 2 - width / 2, 100)
    ctx.show_text(lm)

    if bcode:
        ctx.set_font_size(35)
        (x, y, width, height, dx, dy) = ctx.text_extents(bcode)
        ctx.move_to(WIDTH / 2 - width / 2, 145)
        ctx.show_text(bcode)

    surface.write_to_png(safef)  # Output to PNG


def getAllLM(dic):
    allLM = []
    for key in dic.keys():
        allLM.append(key)
    return (allLM)


def getIndex(indfile):
    with open(indfile) as csvfile:
        reader = csv.DictReader(csvfile)
        return ([row for row in reader])


def randomHexNum():
    return ("{:010x}".format(random.randint(0, 1099511627776)))


def storeNewLM(lm, ident, hvon, hbis, hdic, index):
    if not hdic.has_key(lm):
        raise Exception("Shelf life not found.")
    if not ident:
        ident = randomHexNum()
    if not hvon:
        hvon = dateToday()
    if not hbis:
        hbis = haltbarkeitbis(lm, hdic)
    index.append({"Lebensmittel": lm, "Identifikationsnummer": ident, "Haltbarkeitvon": hvon, "Haltbarkeitbis": hbis})
    return (ident)


def delIndexLMIdent(ident, index):
    return ([row for row in index if row["Identifikationsnummer"] != ident])


def delIndexLMName(name, index):
    return ([row for row in index if row["Lebensmittel"] != name])


def delIndexLMHv(hv, index):
    return ([row for row in index if row["Halbarkeitvon"] != hv])


def delIndexLMHb(hb, index):
    return ([row for row in index if row["Halbarkeitbis"] != hb])


def safeIndex(index, fname):
    with open(fname, 'w') as csvfile:
        fieldnames = ['Lebensmittel', 'Identifikationsnummer', 'Haltbarkeitvon', 'Haltbarkeitbis']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in index:
            writer.writerow(row)


def printlabel(l):
    os.system(
        "~/.local/bin/brother_ql -m QL-700 -p usb://0x04f9:0x2042 print -l 38 ~/PycharmProjects/EtikettenDrucker/" + l)


def printIndex(index):
    data = [['Lebensmittel', 'Identifikationsnummer', 'Haltbarkeitvon', 'Haltbarkeitbis']]
    data.extend(
        [[r['Lebensmittel'], r['Identifikationsnummer'], r['Haltbarkeitvon'], r['Haltbarkeitbis']] for r in index])
    table = terminaltables.AsciiTable(data)
    print(table.table)


def printEANS(eans):
    print(eans)
    data = [["ean", 'Lebensmittel']]
    data.extend([[ean, lm] for ean, lm in eans.items()])
    table = terminaltables.AsciiTable(data)
    print(table.table)


def printShelfLife(sh):
    data = [['Lebensmittel', 'Haltbarkeit']]
    data.extend([[r['Lebensmittel'], r['Haltbarkeit']] for r in sh])
    table = terminaltables.AsciiTable(data)
    print(table.table)


def newLMPrint(lm, dfile, ifile, pfile):
    index = getIndex(ifile)
    dic = getSH()
    if not dic.has_key(lm):
        raise Exception(
            "Shelf life not found. Please specify that with: verwaltung print {lm} -s <Shelf life>".format(lm=lm))
    bcode = storeNewLM(lm, None, None, None, dic, index)
    genLabel(lm, dic, pfile, bcode)
    printlabel(pfile)
    storeNewLM(lm, None, None, None, dic, index)
    printIndex(index)
    safeDict(dic, "haltbarkeiten.csv")
    safeIndex(index, "index.csv")


def setShelfLife(lm, sh, dicf):
    dic = getSH()
    dic[lm] = sh
    safeDict(dic, dicf)


def getShelfLifef(shfile):
    return (openCSVDict("haltbarkeiten.csv"))


def printlcom(args):
    if args.s:
        setShelfLife(args.f, args.s, "haltbarkeiten.csv")
    for i in range(args.t):
        newLMPrint(args.f, "haltbarkeiten.csv", "index.csv", "print.png")


def showcom(args):
    if args.f == "index":
        printIndex(getIndex("index.csv"))
    elif args.f == "haltbarkeiten":
        printShelfLife(getShelfLifef("haltbarkeiten.csv"))
    else:
        raise Exception("File not found!")


def delLMcom(args):
    index = getIndex("index.csv")
    if args.f:
        index = delIndexLMName(args.f, index)
    if args.hv:
        index = delIndexLMHv(args.hv, index)
    if args.hb:
        index = delIndexLMHb(args.hb, index)
    if args.i:
        index = delIndexLMIdent(args.i, index)
    safeIndex(index, "index.csv")
    printIndex(index)
    print("Item deleted!")


def getlists():
    index = getIndex("index.csv")
    dic = getSH()
    return (dic, index)


def addLMcom(args):
    eans = getEAN()
    if isinstance(args.f,int):
        food = eans[args.ean]
    else:
        food = args.f

    if args.s:
        setShelfLife(food, args.s, "haltbarkeiten.csv")

    dic, index = getlists()
    for i in range(args.t):
        storeNewLM(food, args.i, args.hv, args.hb, dic, index)
    safeIndex(index, "index.csv")
    safeDict(dic, "haltbarkeiten.csv")
    printIndex(index)
    print("Item saved")

def vorratcomall():
    index = getIndex("index.csv");
    lmdic = {}
    for row in index:
        try:
            lmdic[row["Lebensmittel"]] += 1
        except:
            lmdic[row["Lebensmittel"]] = 1
    for key in lmdic.keys():
        print(str(lmdic[key]) + " " + key)


def vorratcom(args):
    if not args.f == "all":
        index = getIndex("index.csv");
        n = 0
        for row in index:
            if row["Lebensmittel"] == args.f:
                n += 1
        print("You stored {n} {l}".format(n=n, l=args.f))
    else:
        vorratcomall()


def eancom(args):
    eans = getEAN()
    if args.showLM:
        try:
            print("The foodstuff for {ean} is: {fs}".format(fs=eans[args.showLM], ean=args.showLM))
        except:
            raise Exception("EAN not found.")

    elif args.showEAN:
        for key, value in eans.items():
            if value == args.showEAN:
                print("The foodstuff for the ean {ean} is: {fs}".format(fs=args.showEAN, ean=key))

    else:
        printEANS(eans)


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()

parser_printl = subparsers.add_parser('print', help="Store new foodstuff. Print a label.")
parser_printl.add_argument('f', type=str, )
parser_printl.add_argument('-s', type=int, help="sets the shelf life")
parser_printl.add_argument('-t', type=int, help="Times to add", default=1)
parser_printl.set_defaults(func=printlcom)

parser_show = subparsers.add_parser('show', help="Shows the index or shelf life list.")
parser_show.add_argument('f', type=str, default=["index or haltbarkeiten"])
parser_show.set_defaults(func=showcom)

parser_delLM = subparsers.add_parser('delLM', help="Deletes foodstuffs using the identification number.")
parser_delLM.add_argument('-f', type=str, help="Lebenstmittel")
parser_delLM.add_argument('-i', type=str, help="Identification number")
parser_delLM.add_argument('-hv', type=str, help="Haltbarkeitvon")
parser_delLM.add_argument('-hb', type=str, help="Haltbarkeitbis")
parser_delLM.set_defaults(func=delLMcom)

parser_addLM = subparsers.add_parser('addLM', help="Add foodstuffs without printing the label")
parser_addLM.add_argument('f', type=str, help="Foodstuff")
parser_addLM.add_argument('-s', type=int, help="sets the shelf life")
parser_addLM.add_argument('-i', type=str, help="Identification number")
parser_addLM.add_argument('-hv', type=str, help="Haltbarkeitvon")
parser_addLM.add_argument('-hb', type=str, help="Haltbarkeitbis")
parser_addLM.add_argument('-t', type=int, help="Times to add", default=1)
parser_addLM.set_defaults(func=addLMcom)

parser_vorrat = subparsers.add_parser('vorrat', help="Shows you how many foodstuff you have.")
parser_vorrat.add_argument('f', type=str, help="Foodstuff")
parser_vorrat.set_defaults(func=vorratcom)

parser_ean = subparsers.add_parser("ean", help="Gives you Information about the ean")
parser_ean.add_argument('-showLM', type=str, help="Shows the foodstuff for an specified EAN")
parser_ean.add_argument('-showEAN', type=str, help="Shows the EAN for an specified foodstuff")
parser_ean.set_defaults(func=eancom)

args = parser.parse_args()
args.func(args)
