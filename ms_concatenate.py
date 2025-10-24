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
from datetime import datetime
from shutil import copy2 as copy
from itertools import combinations
from os.path import realpath
from mscore import Score, VoiceName
from mscore.fuzzy import FuzzyCandidate, FuzzyName
from datetime import datetime

def setup_logging(log_level="INFO", log_file=None, console_output=False, overwrite_log=False):
    """
    Set up logging configuration
    
    :param log_level: INFO or DEBUG or WARN (None for no logging)
    :param log_file: Path to log file, or None for no file logging
    :param console_output: Whether to also output to console (default: False)
    :param overwrite_log: Whether to overwrite the log file (default: False - append)
    """
    # Create logger
    logger = logging.getLogger('mscz_concatenator')
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # If log_level is None, return a null logger
    if log_level is None:
        logger.addHandler(logging.NullHandler())
        return logger
    
    # Set log level for active logging
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Console handler (only if requested)
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_mode = 'w' if overwrite_log else 'a'
        file_handler = logging.FileHandler(log_file, mode=file_mode)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Global logger instance
logger = None

def validate_and_skip_files(target, sources):
    """
    Validate files and return lists of valid files and skipped files with reasons
    """
    valid_sources = []
    skipped_files = []
    
    for src in sources:
        try:
            src_parts = src.part_names()
            target_parts = target.part_names()
            
            # Clean both part lists (remove None and empty values)
            src_parts_clean = [part for part in src_parts if part is not None and part != ""]
            target_parts_clean = [part for part in target_parts if part is not None and part != ""]
            
            # Check for text-only files
            if not src_parts_clean:
                skipped_files.append({
                    'file': src.basename,
                    'reason': 'Contains no musical parts (only text frames)'
                })
                continue
            
            # Check instrumentation match - WITHOUT sorting to preserve order
            if src_parts_clean != target_parts_clean:  # Remove sorted() here
                skipped_files.append({
                    'file': src.basename, 
                    'reason': f'Different instrumentation. Target: {target_parts_clean}, File: {src_parts_clean}'
                })
                continue
            
            valid_sources.append(src)
            
        except Exception as e:
            skipped_files.append({
                'file': src.basename,
                'reason': f'Validation error: {str(e)}'
            })
    
    return valid_sources, skipped_files
    
    
def concatenate(source_paths, target_path, copy_frames=True, copy_title_frames=True, 
                copy_system_locks=True, copy_pictures=False, verbose=False, 
                progress_callback=None, break_type="none", break_options=None,
                log_level="INFO", log_file=None, skip_incompatible=True, 
                console_output=False, overwrite_log=False):
    
    global logger
    logger = setup_logging(log_level, log_file, console_output, overwrite_log)
    
    logger.info(f"Starting concatenation of {len(source_paths)} files")
    logger.info(f"Source files: {[os.path.basename(f) for f in source_paths]}")
    logger.info(f"Target file: {os.path.basename(target_path)}")
    logger.info(f"Options - Copy frames: {copy_frames}, Copy title frames: {copy_title_frames}, "
                f"Copy system locks: {copy_system_locks}, Copy pictures: {copy_pictures}")
    logger.info(f"Break type: {break_type}, Skip incompatible: {skip_incompatible}")
    
    if len(source_paths) < 2:
        logger.error("At least two source files required")
        raise ValueError("You must provide at least two sources.")
        
    # Ensure only .mscz is used
    for src in source_paths:
        if not src.lower().endswith(".mscz"):
            logger.error(f"Unsupported file type: {src}")
            raise ValueError(f"Unsupported file type: {src}. Only .mscz files are supported.")

    if not target_path.lower().endswith(".mscz"):
        logger.error(f"Target must be .mscz file: {target_path}")
        raise ValueError(f"Target must be a .mscz file (got {target_path})")    

    target_path = realpath(target_path)
    source_paths = [realpath(src) for src in source_paths]

    if target_path in source_paths:
        logger.error("Target cannot be one of the source files")
        raise ValueError("Sources and Target must be different paths")

    # Sanity checks
    for a, b in combinations(source_paths, 2):
        if a == b:
            logger.error("Duplicate source files detected")
            raise ValueError("More than one Source are the same file")
    
    duplicate_warnings = []
    skipped_files = []
    
    # Update progress for base file (file 1)
    if progress_callback:
        progress_callback(1, len(source_paths))

    # Copy first file to target (includes all frames and measures from first score)
    logger.info(f"Using first file as base: {os.path.basename(source_paths[0])}")
    copy(source_paths[0], target_path)
    target = Score(target_path)
    logger.debug(f"First file loaded as target: {target.basename}")

    # Load rest of the files
    sources = [Score(src) for src in source_paths[1:]]
    logger.info(f"Additional files to concatenate: {[s.basename for s in sources]}")
    
    # Validate and potentially skip files
    if skip_incompatible:
        logger.info("Checking file compatibility...")
        valid_sources, skipped_files = validate_and_skip_files(target, sources)
        
        # Log skipped files
        for skipped in skipped_files:
            logger.warning(f"Skipped {skipped['file']}: {skipped['reason']}")
        
        if skipped_files:
            logger.info(f"Skipped {len(skipped_files)} file(s) due to incompatibility")
        else:
            logger.info("All files are compatible")
            
        sources = valid_sources
    else:
        logger.info("Using strict validation (will raise errors for incompatible files)")
        # Use original validation (will raise exceptions)
        for src in sources:
            src_parts = src.part_names()
            target_parts = target.part_names()
            
            # Clean both part lists
            src_parts_clean = [part for part in src_parts if part is not None and part != ""]
            target_parts_clean = [part for part in target_parts if part is not None and part != ""]
            
            # Check for text-only files
            if not src_parts_clean:
                logger.error(f"File {src.basename} contains no musical parts")
                raise ValueError(f'File "{src.basename}" contains no musical parts')
            
            # Check instrumentation match - WITHOUT sorting to preserve order
            if src_parts_clean != target_parts_clean:  # Remove sorted() here
                logger.error(f"File {src.basename} has different instrumentation")
                raise ValueError(f'File "{src.basename}" has different instrumentation')
        
        skipped_files = []

    # Add layout breaks to the FIRST file if requested
    if break_type != "none" and len(sources) >= 1:
        break_types = break_type.split(',') if ',' in break_type else [break_type]
        logger.info(f"Adding layout breaks to first file: {break_types}")
        
        for bt in break_types:
            if bt != "none":
                logger.debug(f"Processing break type: {bt}")
                current_break_options = break_options if bt == "section" else None
                _add_layout_break(target, bt, current_break_options)

    # Process each source file
    logger.info(f"Starting concatenation of {len(sources)} compatible files")
    for i, source in enumerate(sources):
        logger.info(f"Processing file {i+1}/{len(sources)}: {source.basename}")
            
        # Add layout breaks BEFORE concatenating this file (except for the first file)
        if break_type != "none" and i > 0:
            break_types = break_type.split(',') if ',' in break_type else [break_type]
            logger.debug(f"Adding breaks before file {source.basename}: {break_types}")
                
            for bt in break_types:
                if bt != "none":
                    logger.debug(f"Processing break type: {bt}")
                        
                    current_break_options = None
                    if bt == "section" and break_options:
                        auto_detect_enabled = break_options.get('auto_detect_repeats', False)
                        target_has_repeats = target.has_repeats_in_last_measure()
                            
                        logger.debug(f"Repeat check - Auto-detect: {auto_detect_enabled}, Has repeats: {target_has_repeats}")
                            
                        if auto_detect_enabled and target_has_repeats:
                            logger.info(f"Target has repeats, setting pause to 0 for {source.basename}")
                            current_break_options = break_options.copy()
                            current_break_options['pause'] = 0.0
                        else:
                            current_break_options = break_options
                        
                    _add_layout_break(target, bt, current_break_options)

        # Concatenate the source file
        logger.debug(f"Concatenating {source.basename}...")
        had_duplicates = target.concatenate_score(
            source, 
            copy_frames=copy_frames,
            copy_title_frames=copy_title_frames,
            copy_system_locks=copy_system_locks,
            copy_pictures=copy_pictures,
            target_path=target_path
        )
        
        if had_duplicates:
            logger.info(f"Duplicate eids resolved in {source.basename}")
            duplicate_warnings.append(source.basename)
        
        logger.info(f"Successfully concatenated {source.basename}")
        
        # Update progress
        if progress_callback:
            progress_callback(i + 2, len(source_paths))

    # Final operations
    logger.info("Saving concatenated score...")
    target.save()
    
    # Copy pictures if requested
    total_pictures_copied = 0
    if copy_pictures:
        logger.info("Copying embedded pictures...")
        for source in sources:
            pictures_copied = target.copy_pictures_to_target(source, target_path)
            total_pictures_copied += pictures_copied
            if pictures_copied > 0:
                logger.info(f"Copied {pictures_copied} pictures from {source.basename}")
        
    if total_pictures_copied > 0:
        logger.info(f"Total pictures copied: {total_pictures_copied}")
    
    # Final summary
    files_processed = len(sources)
    files_skipped = len(skipped_files)
    logger.info(f"Concatenation completed: {files_processed} files processed, {files_skipped} files skipped")
    
    if duplicate_warnings:
        logger.info(f"Duplicate eids resolved in: {', '.join(duplicate_warnings)}")
    
    return True, skipped_files
    
def _add_layout_break(score, break_type, break_options):
    """
    Add a layout break to the last measure of the score
    """
    if break_type == "none":
        return
        
    logger.debug(f"_add_layout_break: Adding layout break of type {break_type} to score {score.basename}")
    
    # Use the Score's method to add the layout break
    score.add_layout_break(break_type, break_options)
    logger.debug(f"_add_layout_break: Method called successfully")
    

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
