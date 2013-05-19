# -*- coding:utf-8 -*-
"""

Requisitos:
    • Uns 4 GiB de memoria RAM son recomendables, dado que o guión consume arredor de 1,6 GiB de memoria.
    • Necesitará ter instalados:
        • Python 2.x: http://www.python.org/download/
        • Beautiful Soup 4.x: http://www.crummy.com/software/BeautifulSoup/#Download

Para usar este guión:

1. Obteña o ficheiro «index.jsp» cos datos:

    1. Abra no Firefox o enderezo «http://www.realacademiagalega.org/recursos-volg».

        Nota: outro navegador podería valer, pero estas instrucións son específicamente para Firefox 21.

    2. No campo «Entrada», escriba «*» e prema «Buscar».

    3. Cando remate de cargarse completamente a páxina, prema co botón secundario en calquera parte dela, e seleccione
    «Gardar páxina como». Garde a páxina onde lle pareza.

    Fírefox gardará unha páxina HTML, e un cartafol co mesmo nome que a páxina. Nese cartafol atopará un ficheiro,
    «index.jsp», que é o que necesitará para executar este guión.

2. Execute o guión coa ruta ao ficheiro «index.jsp» como primeiro argumento:

    python2 volga-tolerado.py ~/Descargas/Recursos\ -\ VOLG\ -\ Real\ Academia\ Galega_ficheiros/index.jsp

O guión creará un ficheiro no cartafol actual, «toleradas.txt», coa lista de entradas do VOLGa marcadas como toleradas.

"""

import codecs, re, sys, urllib2
from bs4 import BeautifulSoup


def main():

    filepath = sys.argv[1]
    with codecs.open(filepath, 'r', 'iso-8859-15') as fileObject:
        fileContent = fileObject.read()
    soup = BeautifulSoup(fileContent)

    outputFileContent = ""
    for item in soup.find_all("font", color=re.compile("(?i)#00a9FF")):
         outputFileContent += item.get_text().strip() + '\n'

    with codecs.open("toleradas.txt", 'w', 'utf-8') as fileObject:
        fileObject.write(outputFileContent)

main()
