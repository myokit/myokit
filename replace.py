#!/usr/bin/env python
import os

abs_ignore = [
    './.git',
    './dev',
    './replace.py',
]
ext_ignore = [
    '.pyc',
]


# Scan whole project
def check_files(root):
    count = 0
    for leaf in os.listdir(root):
        leaf = os.path.join(root, leaf)

        # Absolute ignores
        if leaf in abs_ignore:
            continue

        # Directory checking
        if os.path.isdir(leaf):
            if not os.path.islink(leaf):
                count += check_files(leaf)
            continue

        # File checking
        if os.path.splitext(leaf)[-1] in ext_ignore:
            continue
        if replace(leaf):
            print('Updated ' + leaf)
            count += 1

    return count

head1 = """
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
""".strip()

head2 = """
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
""".strip()

head_new = """
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
""".strip()

# Replace
def replace(path):

    with open(path, 'r') as f:
        content = f.read()

    header = content[:1000]

    found = None

    if head1 in header:
        print('Found head 1')
        found = head1
    elif head2 in header:
        print('Found head 2')
        found = head2
    else:
        return 0

    content = content.replace(found, head_new)
    with open(path, 'w') as f:
        f.write(content)

    return 1


n = check_files('./')
print('Checked ' + str(n) + ' files.')
