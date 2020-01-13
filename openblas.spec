%bcond_with system_lapack

Name:           openblas
Version:        0.3.3
Release:        3
Summary:        An optimized BLAS library based on GotoBLAS2 1.13 BSD version
License:        BSD
URL:            https://github.com/xianyi/OpenBLAS/
Source0:        https://github.com/xianyi/OpenBLAS/archive/v%{version}/openblas-%{version}.tar.gz
Patch0000:      openblas-0.2.15-system_lapack.patch
Patch0001:      openblas-0.2.5-libname.patch
Patch0002:      openblas-0.2.15-constructor.patch
Patch0003:      openblas-0.3.2-tests.patch
Patch0004:      openblas-0.3.3-tls.patch
Requires:       %{name}-devel = %{version}-%{release}
BuildRequires:  gcc gcc-gfortran perl-devel

%if %{with system_lapack}
BuildRequires:  lapack-static lapack64-static
%global lapacke 0
%else
%global lapacke 1
Provides:       bundled(lapack) = 3.8.0
%endif

Provides:       openblas-serial = %{version}-%{release} openblas-openmp = %{version}-%{release}
Provides:       openblas-threads = %{version}-%{release} openblas-serial64 = %{version}-%{release}
Provides:       openblas-openmp64 = %{version}-%{release} openblas-threads64 = %{version}-%{release}
Provides:       openblas-serial64_ = %{version}-%{release} openblas-openmp64_ = %{version}-%{release}
Provides:       openblas-threads64_ = %{version}-%{release} openblas-Rblas = %{version}-%{release}
Provides:       openblas-static = %{version}-%{release}
Obsoletes:      openblas-serial < %{version}-%{release} openblas-openmp < %{version}-%{release}
Obsoletes:      openblas-threads < %{version}-%{release} openblas-serial64 < %{version}-%{release}
Obsoletes:      openblas-openmp64 < %{version}-%{release} openblas-threads64 < %{version}-%{release}
Obsoletes:      openblas-serial64_ < %{version}-%{release} openblas-openmp64_ < %{version}-%{release}
Obsoletes:      openblas-threads64_ < %{version}-%{release} openblas-Rblas < %{version}-%{release}
Obsoletes:      openblas-static < %{version}-%{release}

ExclusiveArch:  x86_64 aarch64

%description
OpenBLAS is an optimized BLAS library based on GotoBLAS2 1.13 BSD \
version. The Lab of Parallel Software and Computationla Science, ISCAS \
supports this project, see: http://www.rdcps.ac.cn


%package devel
Summary:        Development headers and libraries for OpenBLAS
Requires:       %{name} = %{version}-%{release} %{name}-srpm-macros

%description devel
This package contains the development headers and libraries for openblas.

%prep
%setup -q -c
cd OpenBLAS-%{version}
%if %{with system_lapack}
%patch0000 -p1 -b .system_lapack
%endif
%patch0001 -p1 -b .libname
%patch0003 -p1 -b .tests
%patch0004 -p1 -b .tls

# Set source permissions
find -name \*.f -exec chmod 644 {} \;

%if %{with system_lapack}
rm -rf lapack-netlib
%endif

# Make serial, threaded, OpenMP, 64-bit versions
# and an libRblas.so
cd ..
cp -ar OpenBLAS-%{version} openmp
cp -ar OpenBLAS-%{version} threaded
for d in {serial,threaded,openmp}64{,_}; do
    cp -ar OpenBLAS-%{version} $d
done
cp -ar OpenBLAS-%{version} Rblas
mv OpenBLAS-%{version} serial

sed -i 's\.so.$(MAJOR_VERSION)\.so\g' Rblas/Makefile
sed -i 's\.so.$(MAJOR_VERSION)\.so\g' Rblas/exports/Makefile
sed -i 's\@ln -fs $(LIBSONAME) $(LIBPREFIX).so\#@ln -fs $(LIBSONAME) $(LIBPREFIX).so\g' Rblas/Makefile

%if %{with system_lapack}
mkdir netliblapack
cd netliblapack
ar x %{_libdir}/liblapack_pic.a
for f in laswp getf2 getrf potf2 potrf lauu2 lauum trti2 trtri getrs; do
    \rm {c,d,s,z}$f.o
done

%if %{lapacke}
ar x %{_libdir}/liblapacke.a
%endif

# Create makefile
echo "TOPDIR = .." > Makefile
echo "include ../Makefile.system" >> Makefile
echo "COMMONOBJS = \\" >> Makefile
for i in *.o; do
 echo "$i \\" >> Makefile
done
echo -e "\n\ninclude \$(TOPDIR)/Makefile.tail" >> Makefile

%if %{lapacke}
# Copy include files
cp -a %{_includedir}/lapacke .
%endif
cd ..

# Copy in place
for d in serial threaded openmp; do
    cp -pr netliblapack $d
done
rm -rf netliblapack


# Setup 64-bit interface LAPACK
mkdir netliblapack64
cd netliblapack64
ar x %{_libdir}/liblapack64_pic.a
# Get rid of duplicate functions. See list in Makefile of lapack directory
for f in laswp getf2 getrf potf2 potrf lauu2 lauum trti2 trtri getrs; do
    \rm {c,d,s,z}$f.o
done

# LAPACKE, no 64-bit interface
%if %{lapacke}
ar x %{_libdir}/liblapacke.a
%endif

# Create makefile for 64-bit interface
echo "TOPDIR = .." > Makefile
echo "include ../Makefile.system" >> Makefile
echo "COMMONOBJS = \\" >> Makefile
for i in *.o; do
    echo "$i \\" >> Makefile
done
echo -e "\n\ninclude \$(TOPDIR)/Makefile.tail" >> Makefile

%if %{lapacke}
# Copy include files
cp -a %{_includedir}/lapacke .
%endif
cd ..

# Copy in place
for d in {serial,threaded,openmp}64{,_}; do
    cp -pr netliblapack64 $d/netliblapack
done
rm -rf netliblapack64
%endif

%build
%if !%{lapacke}
LAPACKE="NO_LAPACKE=1"
%endif

# Maximum possible amount of processors
NMAX="NUM_THREADS=128"

%ifarch x86_64
TARGET="TARGET=CORE2 DYNAMIC_ARCH=1 DYNAMIC_OLDER=1"
%endif
%ifarch aarch64
TARGET="TARGET=ARMV8 DYNAMIC_ARCH=0"
%endif

COMMON="%{optflags} -fPIC"
FCOMMON="%{optflags} -fPIC -frecursive"
export LDFLAGS="%{__global_ldflags}"

make -C Rblas      $TARGET USE_THREAD=0 USEOPENMP=0 FC=gfortran CC=gcc COMMON_OPT="$COMMON" FCOMMON_OPT="$FCOMMON" $NMAX LIBPREFIX="libRblas" LIBSONAME="libRblas.so" $AVX $LAPACKE INTERFACE64=0

# Declare some necessary build flags
COMMON="%{optflags} -fPIC"
FCOMMON="$COMMON -frecursive"
make -C serial     $TARGET USE_THREAD=0 USE_OPENMP=0 FC=gfortran CC=gcc COMMON_OPT="$COMMON" FCOMMON_OPT="$FCOMMON" $NMAX LIBPREFIX="libopenblas"      $AVX $LAPACKE INTERFACE64=0
make -C threaded   $TARGET USE_THREAD=1 USE_OPENMP=0 FC=gfortran CC=gcc COMMON_OPT="$COMMON" FCOMMON_OPT="$FCOMMON" $NMAX LIBPREFIX="libopenblasp"     $AVX $LAPACKE INTERFACE64=0

# USE_THREAD determines use of SMP, not of pthreads
COMMON="%{optflags} -fPIC -fopenmp -pthread"
FCOMMON="$COMMON -frecursive"
make -C openmp     $TARGET USE_THREAD=1 USE_OPENMP=1 FC=gfortran CC=gcc COMMON_OPT="$COMMON" FCOMMON_OPT="$FCOMMON" $NMAX LIBPREFIX="libopenblaso"     $AVX $LAPACKE INTERFACE64=0

COMMON="%{optflags} -fPIC"
FCOMMON="$COMMON -frecursive -fdefault-integer-8"
make -C serial64   $TARGET USE_THREAD=0 USE_OPENMP=0 FC=gfortran CC=gcc COMMON_OPT="$COMMON" FCOMMON_OPT="$FCOMMON" $NMAX LIBPREFIX="libopenblas64"    $AVX $LAPACKE INTERFACE64=1
make -C threaded64 $TARGET USE_THREAD=1 USE_OPENMP=0 FC=gfortran CC=gcc COMMON_OPT="$COMMON" FCOMMON_OPT="$FCOMMON" $NMAX LIBPREFIX="libopenblasp64"   $AVX $LAPACKE INTERFACE64=1

COMMON="%{optflags} -fPIC -fopenmp -pthread"
FCOMMON="$COMMON -frecursive -fdefault-integer-8"
make -C openmp64   $TARGET USE_THREAD=1 USE_OPENMP=1 FC=gfortran CC=gcc COMMON_OPT="$COMMON" FCOMMON_OPT="$FCOMMON" $NMAX LIBPREFIX="libopenblaso64"   $AVX $LAPACKE INTERFACE64=1

COMMON="%{optflags} -fPIC"
FCOMMON="$COMMON -frecursive  -fdefault-integer-8"
make -C serial64_   $TARGET USE_THREAD=0 USE_OPENMP=0 FC=gfortran CC=gcc COMMON_OPT="$COMMON" FCOMMON_OPT="$FCOMMON" $NMAX LIBPREFIX="libopenblas64_"  $AVX $LAPACKE INTERFACE64=1 SYMBOLSUFFIX=64_
make -C threaded64_ $TARGET USE_THREAD=1 USE_OPENMP=0 FC=gfortran CC=gcc COMMON_OPT="$COMMON" FCOMMON_OPT="$FCOMMON" $NMAX LIBPREFIX="libopenblasp64_" $AVX $LAPACKE INTERFACE64=1 SYMBOLSUFFIX=64_

COMMON="%{optflags} -fPIC -fopenmp -pthread"
FCOMMON="$COMMON -frecursive -fdefault-integer-8"
make -C openmp64_   $TARGET USE_THREAD=1 USE_OPENMP=1 FC=gfortran CC=gcc COMMON_OPT="$COMMON" FCOMMON_OPT="$FCOMMON" $NMAX LIBPREFIX="libopenblaso64_" $AVX $LAPACKE INTERFACE64=1 SYMBOLSUFFIX=64_

%install
rm -rf %{buildroot}
# Install serial library and headers
make -C serial USE_THREAD=0 PREFIX=%{buildroot} OPENBLAS_LIBRARY_DIR=%{buildroot}%{_libdir} OPENBLAS_INCLUDE_DIR=%{buildroot}%{_includedir}/%name OPENBLAS_BINARY_DIR=%{buildroot}%{_bindir} OPENBLAS_CMAKE_DIR=%{buildroot}%{_libdir}/cmake install

# Copy lapacke include files
%if %{with system_lapack} && %{lapacke}
cp -a %{_includedir}/lapacke %{buildroot}%{_includedir}/%{name}
%endif

# Fix name of libraries
%ifarch aarch64
suffix="_armv8"
%endif
slibname=`basename %{buildroot}%{_libdir}/libopenblas${suffix}-*.so .so`
mv %{buildroot}%{_libdir}/${slibname}.a %{buildroot}%{_libdir}/lib%{name}.a
if [[ "$suffix" != "" ]]; then
   sname=$(echo $slibname | sed "s|$suffix||g")
   mv %{buildroot}%{_libdir}/${slibname}.so %{buildroot}%{_libdir}/${sname}.so
else
   sname=${slibname}
fi

# Install the Rblas library
mkdir -p %{buildroot}%{_libdir}/R/lib/
install -p -m 755 Rblas/libRblas.so %{buildroot}%{_libdir}/R/lib/

# Install the OpenMP library
olibname=`echo ${slibname} | sed "s|lib%{name}|lib%{name}o|g"`
install -D -p -m 644 openmp/${olibname}.a %{buildroot}%{_libdir}/lib%{name}o.a
if [[ "$suffix" != "" ]]; then
   oname=$(echo $olibname | sed "s|$suffix||g")
else
   oname=${olibname}
fi
install -D -p -m 755 openmp/${olibname}.so %{buildroot}%{_libdir}/${oname}.so

# Install the threaded library
plibname=`echo ${slibname} | sed "s|lib%{name}|lib%{name}p|g"`
install -D -p -m 644 threaded/${plibname}.a %{buildroot}%{_libdir}/lib%{name}p.a
if [[ "$suffix" != "" ]]; then
   pname=$(echo $plibname | sed "s|$suffix||g")
else
   pname=${plibname}
fi
install -D -p -m 755 threaded/${plibname}.so %{buildroot}%{_libdir}/${pname}.so

# Install the 64-bit interface libraries

slibname64=`echo ${slibname} | sed "s|lib%{name}|lib%{name}64|g"`
install -D -p -m 644 serial64/${slibname64}.a %{buildroot}%{_libdir}/lib%{name}64.a
slibname64_=`echo ${slibname} | sed "s|lib%{name}|lib%{name}64_|g"`
install -D -p -m 644 serial64_/${slibname64_}.a %{buildroot}%{_libdir}/lib%{name}64_.a

if [[ "$suffix" != "" ]]; then
   sname64=$(echo ${slibname64} | sed "s|$suffix||g")
   sname64_=$(echo ${slibname64_} | sed "s|$suffix||g")
else
   sname64=${slibname64}
   sname64_=${slibname64_}
fi
install -D -p -m 755 serial64/${slibname64}.so %{buildroot}%{_libdir}/${sname64}.so
install -D -p -m 755 serial64_/${slibname64_}.so %{buildroot}%{_libdir}/${sname64_}.so

olibname64=`echo ${slibname} | sed "s|lib%{name}|lib%{name}o64|g"`
install -D -p -m 644 openmp64/${olibname64}.a %{buildroot}%{_libdir}/lib%{name}o64.a
olibname64_=`echo ${slibname} | sed "s|lib%{name}|lib%{name}o64_|g"`
install -D -p -m 644 openmp64_/${olibname64_}.a %{buildroot}%{_libdir}/lib%{name}o64_.a

if [[ "$suffix" != "" ]]; then
   oname64=$(echo ${olibname64} | sed "s|$suffix||g")
   oname64_=$(echo ${olibname64_} | sed "s|$suffix||g")
else
   oname64=${olibname64}
   oname64_=${olibname64_}
fi
install -D -p -m 755 openmp64/${olibname64}.so %{buildroot}%{_libdir}/${oname64}.so
install -D -p -m 755 openmp64_/${olibname64_}.so %{buildroot}%{_libdir}/${oname64_}.so

plibname64=`echo ${slibname} | sed "s|lib%{name}|lib%{name}p64|g"`
install -D -p -m 644 threaded64/${plibname64}.a %{buildroot}%{_libdir}/lib%{name}p64.a
plibname64_=`echo ${slibname} | sed "s|lib%{name}|lib%{name}p64_|g"`
install -D -p -m 644 threaded64_/${plibname64_}.a %{buildroot}%{_libdir}/lib%{name}p64_.a

if [[ "$suffix" != "" ]]; then
   pname64=$(echo $plibname64 | sed "s|$suffix||g")
   pname64_=$(echo $plibname64_ | sed "s|$suffix||g")
else
   pname64=${plibname64}
   pname64_=${plibname64_}
fi
install -D -p -m 755 threaded64/${plibname64}.so %{buildroot}%{_libdir}/${pname64}.so
install -D -p -m 755 threaded64_/${plibname64_}.so %{buildroot}%{_libdir}/${pname64_}.so

# Fix symlinks
cd %{buildroot}%{_libdir}

# Serial libraries
ln -sf ${sname}.so lib%{name}.so
ln -sf ${sname}.so lib%{name}.so.0
# OpenMP libraries
ln -sf ${oname}.so lib%{name}o.so
ln -sf ${oname}.so lib%{name}o.so.0
# Threaded libraries
ln -sf ${pname}.so lib%{name}p.so
ln -sf ${pname}.so lib%{name}p.so.0

# 64bit Serial libraries
ln -sf ${sname64}.so lib%{name}64.so
ln -sf ${sname64}.so lib%{name}64.so.0
ln -sf ${sname64_}.so lib%{name}64_.so
ln -sf ${sname64_}.so lib%{name}64_.so.0
# 64bit OpenMP libraries
ln -sf ${oname64}.so lib%{name}o64.so
ln -sf ${oname64}.so lib%{name}o64.so.0
ln -sf ${oname64_}.so lib%{name}o64_.so
ln -sf ${oname64_}.so lib%{name}o64_.so.0
# 64bit Threaded libraries
ln -sf ${pname64}.so lib%{name}p64.so
ln -sf ${pname64}.so lib%{name}p64.so.0
ln -sf ${pname64_}.so lib%{name}p64_.so
ln -sf ${pname64_}.so lib%{name}p64_.so.0


# Get rid of generated CMake config
rm -rf %{buildroot}%{_libdir}/cmake
# Get rid of generated pkgconfig
rm -rf %{buildroot}%{_libdir}/pkgconfig

%post
/sbin/ldconfig

%postun
/sbin/ldconfig

%files
%license serial/LICENSE
%doc serial/Changelog.txt serial/GotoBLAS*
%{_libdir}/lib%{name}*-*.so
%{_libdir}/lib%{name}*.so.*
%{_libdir}/R/lib/libRblas.so
%{_libdir}/lib%{name}*.a

%files devel
%{_includedir}/%{name}/
%{_libdir}/lib%{name}.so
%{_libdir}/lib%{name}o.so
%{_libdir}/lib%{name}p.so
%{_libdir}/lib%{name}*64.so
%{_libdir}/lib%{name}*64_.so

%changelog
* Wed Nov 13 2019 Alex Chao <zhaolei746@huawei.com> - 0.3.3-3
- Package init
