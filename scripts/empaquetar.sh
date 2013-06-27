#!/bin/bash

rootFolder="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/.."

pushd $rootFolder &> /dev/null

# Eliminar o cartafol de construción existente se o hai.
rm -rf ./build

# Construír e empaquetar o corrector principal (VOLG).
scons aff=norma dic=volga rep=comunidade,galipedia
pushd build &> /dev/null
packageName="hunspell-gl-$(date -u +"%Y%m%d")"
mkdir ${packageName}
mv gl.aff ${packageName}/gl.aff
mv gl.dic ${packageName}/gl.dic
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
