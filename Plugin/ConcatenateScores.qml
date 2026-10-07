
//=============================================================================
//  Concatenate Scores — MuseScore 4.x
//  Launches mscz-concatenator (bundled alongside this plugin).
//
//  Copyright (c)2026 Diego Denolf 
//
// This program is free software; you can redistribute it or modify it under
// the terms of the GNU General Public License version 3 as published by the
// Free Software Foundation and appearing in the accompanying LICENCE file.
//
//  Installation:
//    1. Copy this file and the mscz-concatenator binary to your
//       MuseScore Plugins folder:
//       Linux:   ~/Documents/MuseScore4/Plugins/
//       Windows: %USERPROFILE%\Documents\MuseScore4\Plugins\
//       macOS:   ~/Documents/MuseScore4/Plugins/
//    2. On Linux/macOS, make the binary executable:
//       chmod +x mscz-concatenator
//    3. In MuseScore: Plugins → Manage plugins → Enable "Concatenate Scores"
//    4. Open a score, then: Plugins → Concatenate Scores
//=============================================================================

import QtQuick
import MuseScore 3.0

MuseScore {
    version: "1.0"
    title: "Concatenate Scores"
    description: "Launch the mscz-concatenator app to merge MuseScore files."
    requiresScore: false
    thumbnailName: "concatenate_scores.png"

    QProcess { id: proc }

    // Returns the folder where this plugin lives (with trailing slash removed)
    function pluginFolder() {
        var u = Qt.resolvedUrl(".").toString();
        if (Qt.platform.os === "windows")
            u = u.replace(/^file:\/\/\//, "");
        else
            u = u.replace(/^file:\/\//, "");
        return decodeURIComponent(u).replace(/\/$/, "");
    }

    // Returns the path to the bundled binary, based on the OS
    function binaryPath() {
        var folder = pluginFolder();
        if (Qt.platform.os === "windows")
            return folder + "/mscz-concatenator.exe";
        return folder + "/mscz-concatenator";
    }

    onRun: {
        // Save the current score if one is open (to avoid losing unsaved work)
        if (curScore) {
            cmd("file-save");
        }

        var binary = binaryPath();
        console.log("Concatenate Scores: launching " + binary);

        if (Qt.platform.os === "windows") {
            proc.startWithArgs("cmd.exe", ["/c", "start", "", binary]);
        } else {
            proc.startWithArgs("/bin/sh",
                ["-c", "nohup \"$0\" >/dev/null 2>&1 &", binary]);
        }
    }
}
