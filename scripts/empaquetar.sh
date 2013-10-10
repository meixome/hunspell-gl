#!/bin/bash

rootFolder="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/.."
code="gl_ES"

pushd $rootFolder &> /dev/null

# Eliminar o cartafol de construción existente se o hai.
rm -rf ./build

# Construír e empaquetar o corrector principal (VOLG).
scons aff=norma dic=volga rep=comunidade,galipedia code=${code}
pushd build &> /dev/null
packageName="hunspell-gl-$(date -u +"%Y%m%d")"
mkdir ${packageName}
mv ${code}.aff ${packageName}/${code}.aff
mv ${code}.dic ${packageName}/${code}.dic
for filename in $(find .. -name "*.txt")
do
  cp "$filename" "${packageName}/"
done
tar -cavf ${packageName}.tar.xz ${packageName} &> /dev/null
mv ${packageName}.tar.xz ../${packageName}.tar.xz
popd &> /dev/null

# Construír e empaquetar o corrector da comunidade.
scons aff=norma,trasno,unidades dic=comunidade,galipedia,iso639,iso4217,trasno,unidades,volga rep=comunidade,galipedia code=${code}
pushd build &> /dev/null
packageName="hunspell-gl-comunidade-$(date -u +"%Y%m%d")"
mkdir ${packageName}
mv ${code}.aff ${packageName}/${code}.aff
mv ${code}.dic ${packageName}/${code}.dic
for filename in $(find .. -name "*.txt")
do
  cp "$filename" "${packageName}/"
done
tar -cavf ${packageName}.tar.xz ${packageName} &> /dev/null
mv ${packageName}.tar.xz ../${packageName}.tar.xz
popd &> /dev/null

# Eliminar o cartafol de construción.
rm -rf ./build

popd &> /dev/null
