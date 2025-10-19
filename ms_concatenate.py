#  mscore/scripts/ms_concatenate.py
#
#  Copyright 2025 Leon Dionne <ldionne@dridesign.sh.cn>
#  Modified 2025 Diego Denolf <graffesmusic@gmail.com> 
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
import logging
import sys
import argparse
import os
from os import linesep
from shutil import copy2 as copy
from itertools import combinations
from os.path import realpath
from mscore import Score, VoiceName
from mscore.fuzzy import FuzzyCandidate, FuzzyName


def concatenate(source_paths, target_path, copy_frames=True, copy_title_frames=True, copy_system_locks=True, copy_pictures=False, verbose=False, progress_callback=None):
    """
    Concatenate MuseScore files into one.

    :param source_paths: list of paths to source score files (at least 2)
    :param target_path: path to the output score file
    :param copy_frames: whether to copy frames from subsequent scores
    :param copy_title_frames: whether to copy title frames from subsequent scores
    :param verbose: whether to show debug logging
    :param progress_callback: callback function for progress updates (current, total)
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

    # Print info  -- remove for exe 
    # print("Concatenating:")
    # print(linesep.join(source_paths))
    # print("Target:")
    # print(target_path)
    # print(f"Copy frames: {copy_frames}")
    # print(f"Copy title frames: {copy_title_frames}")

    # Sanity checks
    for a, b in combinations(source_paths, 2):
        if a == b:
            raise ValueError("More than one Source are the same file")
    # Make sure duplicate_warnings is defined
    duplicate_warnings = []
    
    # Update progress for base file (file 1)
    if progress_callback:
        progress_callback(1, len(source_paths))

    # Copy first file to target (includes all frames and measures from first score)
    copy(source_paths[0], target_path)
    target = Score(target_path)

    # Load rest
    sources = [Score(src) for src in source_paths[1:]]
    for src in sources:
        # Get and clean part names FIRST, before any sorting
        src_parts = src.part_names()
        target_parts = target.part_names()
        
        # Clean both part lists (remove None and empty values)
        src_parts_clean = [part for part in src_parts if part is not None and part != ""]
        target_parts_clean = [part for part in target_parts if part is not None and part != ""]
        
        # Check for text-only files first
        if not src_parts_clean:
            raise ValueError(
                f'File "{src.basename}" contains no musical parts (only text frames).\n'
                "This file cannot be concatenated with musical scores.\n"
                "Please remove it from the file list."
            )
        
        # Also check if target has no parts (shouldn't happen, but just in case)
        if not target_parts_clean:
            raise ValueError(
                f'The first file "{os.path.basename(source_paths[0])}" contains no musical parts.\n'
                "Please select a different file as the first file."
            )
        
        # Now sort and compare
        if sorted(src_parts_clean) != sorted(target_parts_clean):
            first_filename = os.path.basename(source_paths[0])
            
            raise ValueError(
                f'File "{src.basename}" does not have the same part names as the first file "{first_filename}"\n'
                #f'First file parts: {sorted(target_parts_clean)}\n'
                #f'This file parts: {sorted(src_parts_clean)}\n'
                "All files must have the same instrument parts to be concatenated."
            )
            
       # Logging
            logging.basicConfig(
                level=logging.DEBUG if verbose else logging.ERROR,
                format="[%(filename)24s:%(lineno)3d] %(message)s"
            )            

         
    # Concatenate using the unified method with progress updates
    for i, source in enumerate(sources):
            had_duplicates = target.concatenate_score(
                source, 
                copy_frames=copy_frames,
                copy_title_frames=copy_title_frames,
                copy_system_locks=copy_system_locks,
                copy_pictures=copy_pictures,
                target_path=target_path
            )
            
            if had_duplicates:
                duplicate_warnings.append(source.basename)
            
            # Update progress
            if progress_callback:
                progress_callback(i + 2, len(source_paths))

    # Show duplicate warnings
    if duplicate_warnings and verbose:
        print(f"Note: Duplicate eids automatically resolved in: {', '.join(duplicate_warnings)}")

    target.save()
    
    # copy pictures (after the file exists)
    total_pictures_copied = 0  #  initializing
    
    if copy_pictures:
        total_pictures_copied = 0
        for source in sources:
            pictures_copied = target.copy_pictures_to_target(source, target_path)
            total_pictures_copied += pictures_copied
            if pictures_copied > 0 and verbose:
                print(f"Copied {pictures_copied} pictures from {source.basename}")
        
    if total_pictures_copied > 0 and verbose:
            print(f"Total pictures copied: {total_pictures_copied}")
    
    # Return both values
    return True, duplicate_warnings

def main():
    p = argparse.ArgumentParser()
    p.add_argument("Sources", type=str, nargs="+",
                   help="MuseScore3 score file to copy measures from")
    p.add_argument("Target", type=str, nargs=1,
                   help="MuseScore3 score file to copy concatenated measures to")
    p.add_argument("--no-copy-frames", action="store_true",
                   help="Do not copy frames from subsequent scores (only measures)")
    p.add_argument("--no-copy-title-frames", action="store_true",
                   help="Do not copy title frames from subsequent scores")
    p.add_argument("--no-copy-pictures", action="store_true",
               help="Do not copy embedded pictures from subsequent scores")               
    p.add_argument("--no-copy-system-locks", action="store_true",
                   help="Do not copy system locks from subsequent scores")
    p.add_argument("--verbose", "-v", action="store_true",
                   help="Show more detailed debug information")
    p.epilog = __doc__
    options = p.parse_args()

    try:
        success, duplicate_warnings = concatenate(
            options.Sources, 
            options.Target[0], 
            copy_frames=not options.no_copy_frames,
            copy_pictures=not options.no_copy_pictures,
            copy_title_frames=not options.no_copy_title_frames,
            copy_system_locks=not options.no_copy_system_locks,
            verbose=options.verbose
        )
        
        if duplicate_warnings and options.verbose:
            print(f"Files with duplicate eids: {', '.join(duplicate_warnings)}")
            
    except Exception as e:
        p.error(str(e))


if __name__ == "__main__":
    main()
