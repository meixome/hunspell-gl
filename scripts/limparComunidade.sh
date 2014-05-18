#!/bin/bash

# Este guión permite eliminar dun ficheiro de vocabulario («.dic») que estea dentro do módulo de comunidade aquelas
# entradas que estean xa presentes nun módulo distinto.
#
# Exemplo de uso:
# $ ./limparComunidade.sh toponimia.dic wikipedia/gl/onomástica/toponimia
#
# Neste exemplo, eliminaranse de «comunidade/toponimia.dic» as entradas que xa estean dispoñíbeis dentro do módulo
# «wikipedia/gl/onomástica/toponimia».

rootFolder="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/.."
pushd $rootFolder &> /dev/null

fileToClean="src/comunidade/${1}"
moduleReplacingTheFile="src/${2}"

# Limpar o ficheiro.
while read line
do
    if [ "$line" != "" ]; then
        if [ "${line:0:1}" != "#" ]; then
            entry="$(echo ${line} | cut -d" " -f 1)"
            currentIfs=${IFS}
            IFS=$'\n'
            escapedEntry="$(echo ${entry} | sed -e "s#\.#\\.#")"
            grepResults=( $(grep -hF "${escapedEntry}" "${moduleReplacingTheFile}"/* -R --exclude-dir="comunidade") )
            IFS=${currentIfs}

            unset entryExists
            for result in "${grepResults[@]}"
            do
                resultEntry=$(echo ${result} | cut -d" " -f 1)
                if [ "${entry}" == "${resultEntry}" ]; then
                entryExists=true
                fi
            done

            if [ "${entryExists}" == "true" ]; then
                echo "Eliminando «${entry}»…"
                sed -e "/^${escapedEntry}\($\| \)/d" -i ${fileToClean}
            fi
        fi
    fi
done < ${fileToClean}

popd &> /dev/null
