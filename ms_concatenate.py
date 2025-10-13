#  mscore/scripts/ms_concatenate.py
#
#  Copyright 2025 Leon Dionne <ldionne@dridesign.sh.cn>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
"""
Concatenates the measures from two or more scores into another score.

The purpose of this script is to allow you to work on a section of a very long
composition, without "lag" slowing you down. When MuseScore has to interpret
and render a very long score, it gets a little slow. Breaking a long
composition down into parts gets around that, making your composing experience
more pleasant.

Note that all sources MUST have the same part / instrument structure.
"""
import logging, sys
import argparse
from os import linesep
from shutil import copy2 as copy
from itertools import combinations
from os.path import realpath
from mscore import Score, VoiceName
from mscore.fuzzy import FuzzyCandidate, FuzzyName


def concatenate(source_paths, target_path, verbose=False):
    """
    Concatenate MuseScore files into one.

    :param source_paths: list of paths to source score files (at least 2)
    :param target_path: path to the output score file
    :param verbose: whether to show debug logging
    """
    if len(source_paths) < 2:
        raise ValueError("You must provide at least two sources.")
        
    # Ensure only .mscz is used
    for src in source_paths:
        if not src.lower().endswith(".mscz"):
            raise ValueError(f"Unsupported file type: {src}. Only .mscz files are supported.")

    if not target_path.lower().endswith(".mscz"):
        raise ValueError(f"Target must be a .mscz file (got {target_path})")    

    target_path = realpath(target_path)
    source_paths = [realpath(src) for src in source_paths]

    if target_path in source_paths:
        raise ValueError("Sources and Target must be different paths")

    # Print info
    print("Concatenating:")
    print(linesep.join(source_paths))
    print("Target:")
    print(target_path)

    # Sanity checks
    for a, b in combinations(source_paths, 2):
        if a == b:
            raise ValueError("More than one Source are the same file")

    # Copy first file to target
    copy(source_paths[0], target_path)
    target = Score(target_path)

    # Load rest
    sources = [Score(src) for src in source_paths[1:]]
    for src in sources:
        if sorted(src.part_names()) != sorted(target.part_names()):
            raise ValueError(
                f'Source "{src.basename}" does not have the same part names as Source "{target.basename}"\n'
                "All sources must have the same part names"
            )

    # Logging
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.ERROR,
        format="[%(filename)24s:%(lineno)3d] %(message)s"
    )

    # Concatenate
    for source in sources:
        target.concatenate_measures(source)

    target.save()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("Sources", type=str, nargs="+",
                   help="MuseScore3 score file to copy measures from")
    p.add_argument("Target", type=str, nargs=1,
                   help="MuseScore3 score file to copy concatenated measures to")
    p.add_argument("--verbose", "-v", action="store_true",
                   help="Show more detailed debug information")
    p.epilog = __doc__
    options = p.parse_args()

    try:
        concatenate(options.Sources, options.Target[0], options.verbose)
    except Exception as e:
        p.error(str(e))


if __name__ == "__main__":
    main()

#  end mscore/scripts/ms_concatenate.py


