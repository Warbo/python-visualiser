#!/usr/bin/env python

# Easily import simple XML data to Python dictionary
# http://www.gmta.info/publications/parsing-simple-xml-structure-to-a-python-dictionary

import xml.dom.minidom
import os
import sys

def haschilds(dom):

    # Checks whether an element has any childs
    # containing real tags opposed to just text.
        
    for childnode in dom.childNodes:
        if childnode.nodeName != "#text" and childnode.nodeName != "#cdata-section":
            return True

    return False

def indexchilds(dom, enc):

    childsdict = dict()

    for childnode in dom.childNodes:

        name = childnode.nodeName.encode(enc)

        if name == "#text" or name == "#cdata-section":
            # ignore whitespaces
            continue

        if haschilds(childnode):
            v = indexchilds(childnode, enc)
        else:
            v = childnode.childNodes[0].nodeValue.encode(enc)

        if name in childsdict:

            if isinstance(childsdict[name], dict):
                # there is multiple instances of this node - convert to list
                childsdict[name] = [childsdict[name]]

            childsdict[name].append(v)

        else:

            childsdict[name] = v

    return childsdict

def xmltodict(data, enc):

    dom = xml.dom.minidom.parseString(data.strip())
    return indexchilds(dom, enc)


if __name__ == '__main__':

    filename = open(os.getcwd() + '/temp/genres/' + sys.argv[1], 'r')
    toParse = ''
    for line in filename.readlines():
        if '<toptags ' in line:
            toParse = toParse + '<toptags>\n'
        else:
            toParse = toParse + line + '\n'

    parsed = xmltodict(toParse, 'iso-8859-1')
    #print str(parsed)
    for tag in parsed['toptags']['tag']:
        print tag['name']

