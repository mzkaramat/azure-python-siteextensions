from __future__ import print_function

import os
import py_compile
import re
import sys

def is_in(value, patterns):
    for p in patterns:
        try:
            search = p.search
        except AttributeError:
            if p == value:
                return True
        else:
            if search(value):
                return True

SYSTEM_FILES = {
    (2, 7): ['python27.dll'],
    (3, 5): ['python35.dll', 'vcruntime140.dll'],
    (3, 6): ['python36.dll', 'vcruntime140.dll'],
}[sys.version_info[:2]]

EXCLUDED_STDLIB = [
    'test',
    re.compile('plat-.+', re.I),
]

EXCLUDED_FILES = [
    re.compile(r'tcl.+\.dll$', re.I),
    re.compile(r'tk.+\.dll$', re.I),
    re.compile(r'\\_test.+\.pyd$', re.I),
    re.compile(r'_test\.pyd$', re.I),
    re.compile(r'.+_d\.(pyd|dll|exe)$', re.I),
]

DO_NOT_COMPILE_FILES = [
    re.compile(r'\\pip\\_vendor\\distlib\\__init__\.py$', re.I),
    re.compile(r'\\wfastcgi\.py$', re.I),
]

EXCLUDED_SUFFIX = [
    '.pyc',
    '.pyo',
    '.pdb',
]

if sys.version_info[0] == 3:
    EXCLUDED_STDLIB.extend([
        'ensurepip',
        'idlelib',
        'tkinter',
        'turtledemo',
        'venv',
    ])

if sys.version_info[0] == 2:
    EXCLUDED_STDLIB.extend([
        'lib-tk',
        'pydoc_data',
    ])

LIB_ROOT = os.path.join(sys.prefix, 'Lib')

CURRENT_VERSION = '%s%s%s%s' % (
    sys.version_info[0],
    sys.version_info[1],
    sys.version_info[2],
    'x64' if sys.maxsize > 2**32 else 'x86'
)

if __name__ == '__main__':
    exit_code = 0
    
    try:
        VERSION = sys.argv[1]
    except:
        print('Expected version as first argument', file=sys.stderr)
        sys.exit(1)
    
    if VERSION != CURRENT_VERSION:
        print('Current version is', CURRENT_VERSION, file=sys.stderr)
        sys.exit(2)
    
    try:
        TARGET = sys.argv[2]
    except:
        print('Expected target directory as second argument', file=sys.stderr)
        sys.exit(1)
    
    print("Copying Python install from", sys.prefix)
    for basedir, subdirs, files in os.walk(sys.prefix):
        if basedir == sys.prefix:
            subdirs[:] = ['DLLs', 'Lib']
        elif basedir == LIB_ROOT:
            subdirs[:] = [d for d in subdirs if not is_in(d, EXCLUDED_STDLIB)]
        
        package_name = os.path.split(basedir)[-1].lower()
        if package_name in ('__pycache__',):
            continue
        
        for name in files:
            filename = os.path.join(basedir, name)
            if is_in(filename, EXCLUDED_FILES):
                continue
            
            target = os.path.join(TARGET, os.path.relpath(filename, start=sys.prefix))
            
            target_dir = os.path.dirname(target)
            if not os.path.isdir(target_dir):
                os.makedirs(target_dir)
            
            suffix = os.path.splitext(filename)[-1].lower()
            if suffix in EXCLUDED_SUFFIX:
                continue
            
            if suffix in ('.py',) and not is_in(filename, DO_NOT_COMPILE_FILES):
                try:
                    py_compile.compile(filename, os.path.splitext(target)[0] + '.pyc', doraise=True)
                except py_compile.PyCompileError:
                    pass
                else:
                    continue
            with open(filename, 'rb') as f1:
                with open(target, 'wb') as f2:
                    f2.write(f1.read())
    
    for name in SYSTEM_FILES:
        target = os.path.join(TARGET, name)
        system_source = os.path.join(os.getenv('SYSTEMROOT'), 'System32', name)
        if not os.path.isfile(target):
            if os.path.isfile(system_source):
                print('Copying', name, 'from', system_source)
                with open(system_source, 'rb') as f1:
                    with open(target, 'wb') as f2:
                        f2.write(f1.read())
            else:
                print('Unable to locate', name, file=sys.stderr)
                exit_code = 1
    
    sys.exit(exit_code)