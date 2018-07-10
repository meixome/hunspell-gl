Corrector ortográfico Hunspell para o galego
============================================

.. note:: This text is in Galician, as the main target audience of this
          software is expected to speak Galician, but not necessarily English.

Hunspell é unha tecnoloxía que permite desenvolver correctores ortográficos.

Hunspell é a tecnoloxía de corrección ortográfica que se emprega en aplicativos
como LibreOffice, Firefox, Scribus, OpenOffice, Google Chrome, Opera, ou
Evernote. Trátase así mesmo da principal tecnoloxía de corrección ortográfica
dos sistemas GNU/Linux e Mac OS X.

O Proxecto Trasno encárgase actualmente do desenvolvemento do corrector
Hunspell de galego.

Se busca información para usuarios sobre como instalar e usar o corrector, ou
máis información xeral sobre el, consulte a documentación no `sitio web de
Trasno <http://trasno.gal/corrector-de-galego-hunspell/>`_.

O resto deste documento está pensado para persoas con certas nocións avanzadas
de informática.

Construción
-----------

Para construír unha parella de ficheiros de Hunspell (:code:`.aff` e
:code:`.dic`):

#.  Instale Python 3.

#.  Cree un entorno virtual de Python e instale nel PyICU e SCons.

    En Linux::

        python3 -m venv venv
        . venv/bin/activate
        pip install wheel  # Pode ser necesario para instalar SCons
        pip install SCons PyICU

#.  Execute :code:`scons`.

Isto xerará dous ficheiros, :code:`build/gl.aff` e :code:`build/gl.dic`, que
inclúen as regras ortográficas para os módulos predeterminados do corrector.

Para construír a edición especial para tradución ao galego, cos acordos
terminolóxicos do Proxecto Trasno, execute::

    scons aff=norma,trasno,unidades dic=rag,trasno,unidades

Para volver construír o corrector ortográfico despois de cambiar algún
ficheiro, primeiro debe facer limpeza con::

    scons -c

Para obter información detallada sobre como construír un corrector ortográfico
personalizado, con vocabulario non normativo e extensións, execute::

    scons -h


Sobre a normativa lingüística
-----------------------------

Este corrector asume como modelo oficial para as regras gramaticais: Normas
ortográficas e morfolóxicas do idioma galego, Real Academia Galega / Instituto
da Lingua Galega, 2003.
http://academia.gal/documents/10157/704901/Normas+ortogr%C3%A1ficas+e+morfol%C3%B3xicas+do+idioma+galego.pdf

Sobre a normativa:

-   http://gl.wikipedia.org/wiki/Normativa_oficial_do_galego

-   http://gl.wikipedia.org/wiki/Normas_Ortogr%C3%A1ficas_e_Morfol%C3%B3xicas_do_Idioma_Galego


Autores e colaboradores
-----------------------

© 2006-2009 Mancomún-CESGA

© 2009-2011 Fundación para o Fomento da Calidade Industrial e Desenvolvemento
Tecnolóxico de Galicia, Xunta de Galicia - Consellería de Economía e Industria

© 2011-2018 Proxecto Trasno

Mantido por Proxecto Trasno (http://trasno.gal) baixo a coordinación de Antón
Méixome.

Desde que existe este recurso, e o seu predecesor, ispell, moita xente e varias
organizacións teñen participado no seu desenvolvemento e mantemento.
Entre eles, debemos salientar as achegas de:

-   André Ventas e Ramón Flores (para ispell). Ata 2003.

-   Xavier Gómez Guinovart, para Imaxin Software e este para Mancomún (primeira
    versión version hunspell, dicionario e regras básicas). 2006.

-   Mancomún, Iniciativa Galega para Software Libre, para Xunta de Galicia (Mar
    Castro, regras formais e dicionario; Francisco Rial, extensión oxt).
    2006-2008.

-   Proxecto Trasno (Miguel Solla, regras avanzadas e dicionario). 2009-2010.

-   Proxecto Trasno (Adrián Chaves, regras novas e reestruturación do código
    para a compilación, dicionario). 2010-2013.
    
Desde o comezo e hoxe en día as fontes principais para o dicionario son os
públicos Vocabulario Ortográfico da Lingua Galega (VOLGa) e o Dicionario da
Real Academia Galega en liña e as súas evolucións no tempos. Debemos
agradecerlle ao ILGA (en concreto a Antón Santamarina) o seu permiso explícito
para poder realizar un dicionario con licenza GPL a partir dos seus recursos
lingüísticos.

-   VOLG(a) Santamarina Fernández, Antón e González González, Manuel (coord.).
    Real Academia Galega / Instituto da Lingua Galega, 2004.
    http://www.realacademiagalega.org/volga/.

O dicionario tamén se alimenta tanto das suxestións dos usuarios como de recursos
libres descontinuados coma o Benposto ou o suxestións de corrección da Wikipedia en
galego.

Unha descrición técnica sobre o comportamento morfolóxico e sintáctico escrita
por Miguel Solla pódese ver en:

-   Núm. 1 da revista Linguamática (ISSN: 1647-0818)
    http://linguamatica.com/index.php/linguamatica/article/view/13


Licenza
-------

Este ficheiro é parte de Hunspell-gl.

.. code-block::

    Hunspell-gl is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Hunspell-gl is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

O corrector está publicado nos termos da licenca GPLv3 (desde 2010, antes
GPLv2 e GPLv1). Achégase o ficheiro «license-gl.txt», ou «license.txt» para
consultar o texto completo da versión orixinal da licenza.
