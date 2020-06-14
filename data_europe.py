# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 10:54:19 2020

@author: mylaa
"""

#
import sqlite3
import re

#
# Ouverture d'une connexion avec la base de données
#
conn = sqlite3.connect('pays.sqlite')

c = conn.cursor()
c.execute('''CREATE TABLE "countries" (
    "wp"    TEXT NOT NULL UNIQUE,
    "name"    TEXT,
    "capital"    TEXT,
    "latitude"    REAL,
    "longitude"    REAL,
    "population"    INTEGER,
    "continent"    TEXT,
    "area" TEXT,
    PRIMARY KEY("wp")
);''')
conn.commit()


from zipfile import ZipFile
import json


    # infobox de l'un des pays

def get_info(country,fichier):
    with ZipFile(fichier,'r') as z:
     # liste des documents contenus dans le fichier zip
         info = json.loads(z.read(country))
    return info



    
#
def get_capital(wp_info):
        # cas général
    if 'capital' in wp_info:
            # parfois l'information récupérée comporte plusieurs lignes
            # on remplace les retours à la ligne par un espace
        capital = wp_info['capital'].replace('\n',' ')
            # le nom de la capitale peut comporter des lettres, des espaces,
            # ou l'un des caractères ',.()|- compris entre crochets [[...]]
        m = re.match(".*?\[\[([\w\s',.()|-]+)\]\]", capital)
            # on récupère le contenu des [[...]]
        capital = m.group(1)
            # si on tombe sur une valeur avec des séparateurs |
            # on prend le premier terme
        if '|' in capital:
            capital = capital.split('|').pop()
            # Cas particulier : Singapour, Monaco, Vatican
        if ( capital == 'city-state' ):
            capital = wp_info['common_name']
            # Cas particulier : Suisse
        if ( capital == 'de jure' and wp_info['common_name'] == 'Switzerland'):
            capital = 'Bern'
        return capital
        # FIX manuel (l'infobox ne contient pas l'information)
    if 'common_name' in wp_info and wp_info['common_name'] == 'Palestine':
        return 'Ramallah'
        # Aveu d'échec, on ne doit jamais se retrouver ici
    print(' Could not fetch country capital {}'.format(wp_info))
    return None

#
def get_name(wp_info):
    
    # cas général
    if 'conventional_long_name' in wp_info:
        name = wp_info['conventional_long_name']
        
        # si le nom est composé de mots avec éventuellement des espaces,
        # des virgules et/ou des tirets, situés devant une double {{ ouvrante,
        # on conserve uniquement la partie devant les {{
        m = re.match("([\w, -]+?)\s*{{",name)
        if m:
            name = m.group(1)
            
        # si le nom est situé entre {{ }} avec un caractère séparateur |
        # on conserve la partie après le |
        m = re.match("{{.*\|([\w, -]+)}}",name)
        if m:
            name = m.group(1)           
        return name

    # FIX manuel (l'infobox ne contient pas l'information)
    if 'common_name' in wp_info and wp_info['common_name'] == 'Singapore':
        return 'Republic of Singapore'
    
    # S'applique uniquement au Vanuatu
    if 'common_name' in wp_info:
        name = wp_info['common_name']
        print( 'using common name {}...'.format(name),end='')
        return name

    # Aveu d'échec, on ne doit jamais se retrouver ici
    print('Could not fetch country name {}'.format(wp_info))
    return None


def get_area(info,country):
    area=info['area_km2']
    return area


def get_population(info,country):
    try :
        population = info['population_census']
    except:
        population = info['population_estimate']
    return population


def get_coords(wp_info):

    # S'il existe des coordonnées dans l'infobox du pays (cas le plus courant)
    if 'coordinates' in wp_info:

        # (?i) - ignorecase - matche en majuscules ou en minuscules
        # ça commence par "{{coord" et se poursuit avec zéro ou plusieurs espaces suivis par une barre "|"
        # après ce motif, on mémorise la chaîne la plus longue possible ne contenant pas de },
        # jusqu'à la première occurence de "}}"
        m = re.match('(?i).*{{coord\s*\|([^}]*)}}', wp_info['coordinates'])

        # l'expression régulière ne colle pas, on affiche la chaîne analysée pour nous aider
        # mais c'est un aveu d'échec, on ne doit jamais se retrouver ici
        if m == None :
            print(' Could not parse coordinates info {}'.format(wp_info['coordinates']))
            return None

        # cf. https://en.wikipedia.org/wiki/Template:Coord#Examples
        # on a récupère une chaîne comme :
        # 57|18|22|N|4|27|32|W|display=title
        # 44.112|N|87.913|W|display=title
        # 44.112|-87.913|display=title
        str_coords = m.group(1)

        # on convertit en numérique et on renvoie
        if str_coords[0:1] in '0123456789':
            return cv_coords(str_coords)

   

# Conversion d'une chaîne de caractères décrivant une position géographique
# en coordonnées numériques latitude et longitude
#
def cv_coords(str_coords):
    # on découpe au niveau des "|" 
    c = str_coords.split('|')

    # on extrait la latitude en tenant compte des divers formats
    lat = float(c.pop(0))
    if (c[0] == 'N'):
        c.pop(0)
    elif ( c[0] == 'S' ):
        lat = -lat
        c.pop(0)
    elif ( len(c) > 1 and c[1] == 'N' ):
        lat += float(c.pop(0))/60
        c.pop(0)
    elif ( len(c) > 1 and c[1] == 'S' ):
        lat += float(c.pop(0))/60
        lat = -lat
        c.pop(0)
    elif ( len(c) > 2 and c[2] == 'N' ):
        lat += float(c.pop(0))/60
        lat += float(c.pop(0))/3600
        c.pop(0)
    elif ( len(c) > 2 and c[2] == 'S' ):
        lat += float(c.pop(0))/60
        lat += float(c.pop(0))/3600
        lat = -lat
        c.pop(0)

    # on fait de même avec la longitude
    lon = float(c.pop(0))
    if (c[0] == 'W'):
        lon = -lon
        c.pop(0)
    elif ( c[0] == 'E' ):
        c.pop(0)
    elif ( len(c) > 1 and c[1] == 'W' ):
        lon += float(c.pop(0))/60
        lon = -lon
        c.pop(0)
    elif ( len(c) > 1 and c[1] == 'E' ):
        lon += float(c.pop(0))/60
        c.pop(0)
    elif ( len(c) > 2 and c[2] == 'W' ):
        lon += float(c.pop(0))/60
        lon += float(c.pop(0))/3600
        lon = -lon
        c.pop(0)
    elif ( len(c) > 2 and c[2] == 'E' ):
        lon += float(c.pop(0))/60
        lon += float(c.pop(0))/3600
        c.pop(0)
    
    # on renvoie un dictionnaire avec les deux valeurs
    return {'lat':lat, 'lon':lon }



def save_country(conn,country,info,continent):
    c = conn.cursor()
    sql = 'INSERT INTO countries VALUES (?,?,?,?,?,?,?,?)'
    name = get_name(info)
    capital = get_capital(info)
    population = get_population(info,country)
    area = get_area(info,country)
    coords = get_coords(info)
    c.execute(sql,(country ,name, capital, coords['lat'],coords['lon'],population,continent,area))
    conn.commit()


def read_country(conn,country):
    c = conn.cursor()
    sql = """SELECT * FROM countries WHERE wp = (?); """
    # soumission de la commande (noter que le second argument est un tuple)
    #try :
    c.execute(sql,(country,))# coords['lat'],coords['lon']))
    conn.commit()
    return c.fetchall()
    #except:
    conn.commit()
    return None

with ZipFile('europe.zip','r') as z:
     # liste des documents contenus dans le fichier zip
    countrylist = z.namelist()

for country in countrylist:
    m = re.match("(\w+).(\w+)", country)
    country_name = m.group(1)
    save_country(conn, country_name, get_info(country,'europe.zip'),'Europe')



