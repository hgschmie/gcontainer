#! /bin/bash

GHE_HOST=ghe.example.com

if [ "$(id -u)" == "0" ]; then
    echo "This script can not be run as root"
    exit 1
fi

if [ "$#" le 1 ]; then
    echo "Usage build_rpm <tag or sha> [<revision>]"
    exit 1
fi

TAG_OR_SHA=$1; shift

if [ "$#" != "0" ]; then
  REVISION=$1 ; shift
else
  REVISION=1
fi

BUILD_DIR=$(mktemp -d -t gcontainer.XXXXXXXX)
WORK_DIR=$(dirname $0)

ARCH=$(rpm --eval "%{_arch}")
PKG_NAME=$(rpm --eval "gcontainer-${TAG_OR_SHA}-${REVISION}.%{dist}")

for i in SPECS BUILDROOT BUILD SOURCES SRPMS RPMS RPMS/noarch RPMS/x86_64; do
    mkdir -p ${BUILD_DIR}/$i
done

mkdir -p ${WORK_DIR}/dist

ARCHIVE_NAME=${TAG_OR_SHA}.tar.gz

curl -k -L -o ${BUILD_DIR}/SOURCES/gcontainer-${ARCHIVE_NAME} https://${GHE_HOST}/g/gcontainer/archive/${ARCHIVE_NAME}
cp ${WORK_DIR}/gcontainer.spec ${BUILD_DIR}/SPECS/gcontainer.spec
rpmbuild --define="_topdir ${BUILD_DIR}" \
         --define="_TAG_OR_SHA ${TAG_OR_SHA}" \
         --define="_REVISION ${REVISION}" \
         -ba ${BUILD_DIR}/SPECS/gcontainer.spec
cp ${BUILD_DIR}/RPMS/x86_64/${PKG_NAME}.${ARCH}.rpm ${WORK_DIR}/dist
cp ${BUILD_DIR}/SRPMS/${PKG_NAME}.src.rpm           ${WORK_DIR}/dist

rm -rf ${BUILD_DIR}
